import os
import uuid
import shutil
import subprocess
import threading
from pathlib import Path

from flask import Flask, request, jsonify
from flask_cors import CORS
import boto3

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
    uploaded = 0
    for file_path in local_path.rglob('*'):
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
    return uploaded


def process_tif(job_id, tif_path, site, output_dir):
    """Run gdal2tiles in a background thread and upload results to S3."""
    try:
        jobs[job_id]['status'] = 'tiling'
        jobs[job_id]['message'] = 'Generating tiles with gdal2tiles...'

        result = subprocess.run(
            [
                'gdal2tiles.py',
                '-p', 'mercator',
                '-z', '14-21',
                '--xyz',
                '-w', 'none',
                str(tif_path),
                str(output_dir),
            ],
            capture_output=True, text=True, timeout=3600,
        )

        if result.returncode != 0:
            jobs[job_id]['status'] = 'error'
            jobs[job_id]['message'] = f'gdal2tiles failed: {result.stderr[:500]}'
            return

        jobs[job_id]['status'] = 'uploading'
        jobs[job_id]['message'] = 'Uploading tiles to S3...'

        uploaded = upload_directory_to_s3(output_dir, f"{S3_PREFIX}/{site}")

        tile_url = f"https://{CLOUDFRONT_DOMAIN}/{site}/{{z}}/{{x}}/{{y}}.png"
        jobs[job_id]['status'] = 'complete'
        jobs[job_id]['message'] = f'Done. {uploaded} tiles uploaded.'
        jobs[job_id]['tileUrl'] = tile_url

    except subprocess.TimeoutExpired:
        jobs[job_id]['status'] = 'error'
        jobs[job_id]['message'] = 'Tile generation timed out (max 1 hour).'
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

    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    if not file.filename.lower().endswith(('.tif', '.tiff')):
        return jsonify({'error': 'File must be a GeoTIFF (.tif or .tiff)'}), 400

    job_id = str(uuid.uuid4())[:8]
    work_dir = TEMP_DIR / job_id
    work_dir.mkdir(parents=True, exist_ok=True)

    tif_path = work_dir / 'input.tif'
    file.save(str(tif_path))

    output_dir = work_dir / 'tiles'
    output_dir.mkdir(exist_ok=True)

    jobs[job_id] = {
        'status': 'queued',
        'message': 'Upload received, starting tile generation...',
        'site': site,
    }

    thread = threading.Thread(target=process_tif, args=(job_id, tif_path, site, output_dir))
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
    return jsonify(job)


if __name__ == '__main__':
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    app.run(host='0.0.0.0', port=5000, debug=True)
