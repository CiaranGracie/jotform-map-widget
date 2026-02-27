import os
import uuid
import shutil
import subprocess
import threading
import time
import math
from pathlib import Path

from flask import Flask, request, jsonify
from flask_cors import CORS
import boto3
from osgeo import gdal

app = Flask(__name__)
CORS(app)

app.config['MAX_CONTENT_LENGTH'] = int(os.getenv('MAX_CONTENT_LENGTH_MB', 5120)) * 1024 * 1024

s3 = boto3.client(
    's3',
    region_name=os.getenv('AWS_REGION', 'ap-southeast-2'),
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
)

S3_BUCKET = os.getenv('S3_BUCKET', '')
S3_PREFIX = os.getenv('S3_PREFIX', 'tiles')
CLOUDFRONT_DOMAIN = os.getenv('CLOUDFRONT_DOMAIN', '')
UPLOAD_SECRET = os.getenv('UPLOAD_SECRET', '')
BLEND_TIMEOUT_SECONDS = int(os.getenv('BLEND_TIMEOUT_SECONDS', '3600'))
TILE_TIMEOUT_SECONDS = int(os.getenv('TILE_TIMEOUT_SECONDS', '14400'))
GDAL2TILES_PROCESSES = int(os.getenv('GDAL2TILES_PROCESSES', '4'))
TEMP_DIR = Path('/tmp/tile-processing')

jobs = {}

VALID_LAYER_TYPES = ['boundaries', 'infrastructure', 'nfz-daily', 'nfz-permanent']

SITES = [
    'binduli-north', 'gudai-darri', 'gruyere', 'saraji',
    'peak-downs', 'goonyella', 'koth', 'caval-ridge', 'blackwater',
]


def require_auth():
    token = request.headers.get('X-Upload-Secret', '')
    if not UPLOAD_SECRET or token != UPLOAD_SECRET:
        return False
    return True


def upload_directory_to_s3(local_dir, s3_prefix):
    """Recursively upload a local directory to S3."""
    local_path = Path(local_dir)
    files = [f for f in local_path.rglob('*') if f.is_file()]
    uploaded = 0
    for file_path in files:
        if not file_path.is_file():
            continue
        relative = file_path.relative_to(local_path)
        s3_key = f"{s3_prefix}/{relative.as_posix()}"
        content_type = 'image/png' if file_path.suffix == '.png' else 'application/octet-stream'
        s3.upload_file(
            str(file_path), S3_BUCKET, s3_key,
            ExtraArgs={'ContentType': content_type},
        )
        uploaded += 1
    return uploaded, len(files)


def delete_s3_prefix(s3_prefix):
    """Delete all objects under a prefix in batches."""
    paginator = s3.get_paginator('list_objects_v2')
    deleted = 0
    for page in paginator.paginate(Bucket=S3_BUCKET, Prefix=s3_prefix):
        contents = page.get('Contents', [])
        if not contents:
            continue
        batch = [{'Key': item['Key']} for item in contents]
        for i in range(0, len(batch), 1000):
            chunk = batch[i:i + 1000]
            s3.delete_objects(Bucket=S3_BUCKET, Delete={'Objects': chunk, 'Quiet': True})
            deleted += len(chunk)
    return deleted


def format_eta(seconds):
    if seconds is None:
        return ''
    seconds = max(0, int(seconds))
    minutes = seconds // 60
    secs = seconds % 60
    if minutes:
        return f"{minutes}m {secs:02d}s"
    return f"{secs}s"


def estimate_tiling_seconds(input_bytes):
    # Rough heuristic: bigger TIFFs take longer to tile.
    input_gb = max(0.1, input_bytes / (1024 * 1024 * 1024))
    estimate = int(input_gb * 15 * 60)
    return max(120, min(3600, estimate))


def blend_with_hillshade(ortho_path, hillshade_path, output_path, opacity):
    """Blend ortho with hillshade using multiply mode and opacity."""
    calc_expr = f"(A*(1-{opacity:.4f}))+((A*(B/255.0))*{opacity:.4f})"
    return subprocess.run(
        [
            'gdal_calc.py',
            '--overwrite',
            '--allBands', 'A',
            '-A', str(ortho_path),
            '-B', str(hillshade_path),
            '--calc', calc_expr,
            '--type', 'Byte',
            '--NoDataValue', '0',
            '--outfile', str(output_path),
        ],
        capture_output=True, text=True, timeout=BLEND_TIMEOUT_SECONDS,
    )


def align_hillshade_to_ortho(ortho_path, hillshade_path, aligned_path):
    """Warp hillshade to match ortho extent, projection, and dimensions."""
    ortho_ds = gdal.Open(str(ortho_path))
    if ortho_ds is None:
        raise Exception('Could not open ortho TIFF for alignment')

    gt = ortho_ds.GetGeoTransform()
    if gt is None:
        raise Exception('Ortho TIFF has no geotransform')

    x_size = ortho_ds.RasterXSize
    y_size = ortho_ds.RasterYSize
    min_x = gt[0]
    max_y = gt[3]
    max_x = min_x + gt[1] * x_size
    min_y = max_y + gt[5] * y_size
    projection = ortho_ds.GetProjection()

    warp_opts = gdal.WarpOptions(
        format='GTiff',
        width=x_size,
        height=y_size,
        outputBounds=(min_x, min_y, max_x, max_y),
        dstSRS=projection if projection else None,
        resampleAlg='bilinear',
        multithread=True,
    )
    aligned = gdal.Warp(str(aligned_path), str(hillshade_path), options=warp_opts)
    if aligned is None:
        raise Exception('Failed to align hillshade to ortho grid')
    aligned = None

    aligned_ds = gdal.Open(str(aligned_path))
    if aligned_ds is None:
        raise Exception('Aligned hillshade output could not be opened')
    if aligned_ds.RasterXSize != x_size or aligned_ds.RasterYSize != y_size:
        raise Exception('Aligned hillshade dimensions still do not match ortho')


def process_tif(job_id, tif_path, hillshade_path, hillshade_opacity, site, output_dir):
    """Run gdal2tiles in a background thread and upload results to S3."""
    try:
        start_time = jobs[job_id]['startedAt']
        tif_size_bytes = jobs[job_id].get('inputBytes', 0)
        tiling_estimate = estimate_tiling_seconds(tif_size_bytes)

        jobs[job_id]['status'] = 'tiling'
        jobs[job_id]['message'] = 'Generating tiles with gdal2tiles...'
        jobs[job_id]['progressPct'] = 35
        jobs[job_id]['etaSeconds'] = tiling_estimate

        source_for_tiling = tif_path
        if hillshade_path and hillshade_path.exists():
            jobs[job_id]['message'] = 'Aligning hillshade to ortho grid...'
            jobs[job_id]['progressPct'] = 15
            aligned_hillshade_path = tif_path.parent / 'hillshade_aligned.tif'
            align_hillshade_to_ortho(tif_path, hillshade_path, aligned_hillshade_path)

            jobs[job_id]['message'] = f'Blending hillshade (opacity {hillshade_opacity:.2f})...'
            jobs[job_id]['progressPct'] = 20
            blended_path = tif_path.parent / 'blended.tif'
            blend_result = blend_with_hillshade(tif_path, aligned_hillshade_path, blended_path, hillshade_opacity)
            if blend_result.returncode != 0:
                jobs[job_id]['status'] = 'error'
                jobs[job_id]['message'] = f'Hillshade blend failed: {blend_result.stderr[:500]}'
                return
            source_for_tiling = blended_path

        jobs[job_id]['message'] = 'Generating tiles with gdal2tiles...'
        jobs[job_id]['progressPct'] = 35

        gdal2tiles_cmd = [
            'gdal2tiles.py',
            '-p', 'mercator',
            '-z', '14-21',
            '--xyz',
            '-w', 'none',
            '--processes', str(max(1, GDAL2TILES_PROCESSES)),
            str(source_for_tiling),
            str(output_dir),
        ]
        result = subprocess.run(
            gdal2tiles_cmd,
            capture_output=True, text=True, timeout=TILE_TIMEOUT_SECONDS,
        )

        if result.returncode != 0:
            jobs[job_id]['status'] = 'error'
            jobs[job_id]['message'] = f'gdal2tiles failed: {result.stderr[:500]}'
            return

        tile_prefix = f"{S3_PREFIX}/{site}" if S3_PREFIX else site
        jobs[job_id]['status'] = 'uploading'
        jobs[job_id]['message'] = 'Replacing existing tiles in S3...'
        jobs[job_id]['progressPct'] = 70
        jobs[job_id]['etaSeconds'] = 90

        deleted = delete_s3_prefix(f"{tile_prefix}/")
        jobs[job_id]['status'] = 'uploading'
        jobs[job_id]['message'] = f'Uploading new tiles to S3... (deleted {deleted} old object(s))'
        jobs[job_id]['progressPct'] = 80

        upload_started = time.time()
        uploaded, total_files = upload_directory_to_s3(output_dir, tile_prefix)
        upload_elapsed = max(1.0, time.time() - upload_started)
        upload_rate = uploaded / upload_elapsed
        remaining = max(0, total_files - uploaded)
        upload_eta = math.ceil(remaining / upload_rate) if upload_rate > 0 else 0

        tile_url = f"https://{CLOUDFRONT_DOMAIN}/{tile_prefix}/{{z}}/{{x}}/{{y}}.png"
        jobs[job_id]['status'] = 'complete'
        jobs[job_id]['message'] = f'Done. {uploaded} tiles uploaded.'
        jobs[job_id]['progressPct'] = 100
        jobs[job_id]['etaSeconds'] = 0
        jobs[job_id]['deletedOldTiles'] = deleted
        jobs[job_id]['uploadedTiles'] = uploaded
        jobs[job_id]['tileCount'] = total_files
        jobs[job_id]['elapsedSeconds'] = int(time.time() - start_time)
        jobs[job_id]['uploadEtaSeconds'] = upload_eta
        jobs[job_id]['tileUrl'] = tile_url

    except subprocess.TimeoutExpired:
        jobs[job_id]['status'] = 'error'
        jobs[job_id]['message'] = f'Tile generation timed out (max {TILE_TIMEOUT_SECONDS // 60} minutes).'
    except Exception as e:
        jobs[job_id]['status'] = 'error'
        jobs[job_id]['message'] = str(e)
    finally:
        shutil.rmtree(tif_path.parent, ignore_errors=True)


@app.route('/api/sites', methods=['GET'])
def list_sites():
    return jsonify({'sites': SITES})


@app.route('/api/upload-tif', methods=['POST'])
def upload_tif():
    if not require_auth():
        return jsonify({'error': 'Unauthorized'}), 401

    site = request.form.get('site', '').strip()
    if site not in SITES:
        return jsonify({'error': f'Invalid site. Must be one of: {", ".join(SITES)}'}), 400

    ortho_file = request.files.get('orthoFile') or request.files.get('file')
    if not ortho_file:
        return jsonify({'error': 'No ortho TIFF provided'}), 400
    if not ortho_file.filename.lower().endswith(('.tif', '.tiff')):
        return jsonify({'error': 'File must be a GeoTIFF (.tif or .tiff)'}), 400

    hillshade_file = request.files.get('hillshadeFile')
    if hillshade_file and hillshade_file.filename and not hillshade_file.filename.lower().endswith(('.tif', '.tiff')):
        return jsonify({'error': 'Hillshade file must be a GeoTIFF (.tif or .tiff)'}), 400

    try:
        hillshade_opacity = float(request.form.get('hillshadeOpacity', '0.6'))
    except ValueError:
        return jsonify({'error': 'hillshadeOpacity must be a number between 0 and 1'}), 400
    if hillshade_opacity < 0 or hillshade_opacity > 1:
        return jsonify({'error': 'hillshadeOpacity must be between 0 and 1'}), 400

    job_id = str(uuid.uuid4())[:8]
    work_dir = TEMP_DIR / job_id
    work_dir.mkdir(parents=True, exist_ok=True)

    tif_path = work_dir / 'input.tif'
    ortho_file.save(str(tif_path))
    hillshade_path = None
    if hillshade_file and hillshade_file.filename:
        hillshade_path = work_dir / 'hillshade.tif'
        hillshade_file.save(str(hillshade_path))

    output_dir = work_dir / 'tiles'
    output_dir.mkdir(exist_ok=True)

    input_bytes = tif_path.stat().st_size if tif_path.exists() else 0
    initial_eta = estimate_tiling_seconds(input_bytes)

    jobs[job_id] = {
        'status': 'queued',
        'message': f'Upload received, starting tile generation... ETA ~ {format_eta(initial_eta)}',
        'site': site,
        'startedAt': time.time(),
        'inputBytes': input_bytes,
        'progressPct': 5,
        'etaSeconds': initial_eta,
        'hillshadeUsed': bool(hillshade_path),
        'hillshadeOpacity': hillshade_opacity,
    }

    thread = threading.Thread(target=process_tif, args=(job_id, tif_path, hillshade_path, hillshade_opacity, site, output_dir))
    thread.daemon = True
    thread.start()

    return jsonify({'jobId': job_id, 'status': 'queued'}), 202


@app.route('/api/upload-kml', methods=['POST'])
def upload_kml():
    if not require_auth():
        return jsonify({'error': 'Unauthorized'}), 401

    site = request.form.get('site', '').strip()
    if site not in SITES:
        return jsonify({'error': f'Invalid site. Must be one of: {", ".join(SITES)}'}), 400

    layer_type = request.form.get('layerType', '').strip()
    if layer_type not in VALID_LAYER_TYPES:
        return jsonify({'error': f'Invalid layerType. Must be one of: {", ".join(VALID_LAYER_TYPES)}'}), 400

    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    if not file.filename.lower().endswith('.kml'):
        return jsonify({'error': 'File must be a KML (.kml)'}), 400

    s3_key = f"{S3_PREFIX}/{site}/{layer_type}.kml"

    try:
        s3.upload_fileobj(
            file, S3_BUCKET, s3_key,
            ExtraArgs={'ContentType': 'application/vnd.google-earth.kml+xml'},
        )
    except Exception as e:
        return jsonify({'error': f'S3 upload failed: {str(e)}'}), 500

    kml_url = f"https://{CLOUDFRONT_DOMAIN}/{site}/{layer_type}.kml"
    return jsonify({'url': kml_url, 'site': site, 'layerType': layer_type})


@app.route('/api/status/<job_id>', methods=['GET'])
def job_status(job_id):
    job = jobs.get(job_id)
    if not job:
        return jsonify({'error': 'Job not found'}), 404
    response = dict(job)
    if job.get('status') in ('queued', 'tiling'):
        elapsed = int(time.time() - job.get('startedAt', time.time()))
        eta = max(0, int(job.get('etaSeconds', 0)) - elapsed)
        response['etaSeconds'] = eta
        if job['status'] == 'tiling':
            base = 10
            span = 60
            total = max(1, int(job.get('etaSeconds', 1)) + elapsed)
            response['progressPct'] = min(70, base + int((elapsed / total) * span))
        eta_text = format_eta(eta)
        response['message'] = f"{job.get('message', job['status'])} (ETA ~ {eta_text})" if eta_text else job.get('message', job['status'])
    return jsonify(response)


if __name__ == '__main__':
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    app.run(host='0.0.0.0', port=5000, debug=True)
