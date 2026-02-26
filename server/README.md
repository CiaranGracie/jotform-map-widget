# Tile Processing Server

Flask server that handles GeoTIFF tile generation and KML uploads to S3/CloudFront.

## Prerequisites

- Docker (recommended) or Python 3.10+ with GDAL installed
- AWS credentials with S3 write access to the tile bucket

## Quick Start (Docker)

```bash
cp .env.example .env
# Edit .env with your AWS credentials and config

docker build -t tile-server .
docker run -d -p 5000:5000 --env-file .env tile-server
```

## Quick Start (Local)

```bash
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your AWS credentials

# Source environment variables
export $(cat .env | xargs)

python app.py
```

## API Endpoints

### POST /api/upload-tif
Upload a GeoTIFF for tile generation.

- **Headers:** `X-Upload-Secret: <your-secret>`
- **Body:** multipart/form-data with `file` (TIF) and `site` (site slug)
- **Returns:** `{ "jobId": "abc123", "status": "queued" }`

### POST /api/upload-kml
Upload a KML overlay file.

- **Headers:** `X-Upload-Secret: <your-secret>`
- **Body:** multipart/form-data with `file` (KML), `site` (site slug), `layerType` (boundaries|infrastructure|nfz-daily|nfz-permanent)
- **Returns:** `{ "url": "https://...", "site": "...", "layerType": "..." }`

### GET /api/status/:jobId
Poll tile generation progress.

- **Returns:** `{ "status": "tiling|uploading|complete|error", "message": "..." }`

### GET /api/sites
List available site slugs.
