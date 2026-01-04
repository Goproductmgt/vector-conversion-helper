# Vector Conversion Helper

## Overview
A backend API that converts raster images (JPG, PNG, HEIC) to vector formats (SVG, EPS, PDF) for print shops.

## Tech Stack
- **Framework:** FastAPI (Python 3.11)
- **Image Processing:** Pillow, rembg, pillow-heif
- **Job Queue:** Redis + RQ (optional, for background processing)
- **Storage:** Vercel Blob (optional, requires token)

## Project Structure
```
├── main.py              # FastAPI app entry point
├── config.py            # Settings management (pydantic-settings)
├── models.py            # Pydantic models
├── api/routes.py        # API endpoints
├── workers/processing.py # Background job functions
├── services/            # Business logic (image processing, storage, vectorization)
├── utils/               # Helpers and validation
└── tests/               # Test files
```

## Running the Project
The API server runs on port 5000 using uvicorn:
```bash
python -m uvicorn main:app --host 0.0.0.0 --port 5000 --reload
```

## API Endpoints
- `GET /` - Root endpoint, confirms API is running
- `GET /docs` - Swagger UI documentation
- `GET /api/health` - Health check endpoint

## Configuration
Settings are loaded from environment variables. Key configurations:
- `CORS_ORIGINS` - Allowed CORS origins (default: *)
- `REDIS_URL` - Redis connection URL (default: redis://localhost:6379)
- `BLOB_READ_WRITE_TOKEN` - Vercel Blob storage token (optional)
- `MAX_FILE_SIZE_MB` - Maximum upload file size (default: 10MB)
- `DEBUG` - Enable debug mode (default: false)

## Recent Changes
- 2026-01-04: Initial setup in Replit environment
  - Installed Python 3.11 and all dependencies
  - Configured workflow for API server on port 5000
  - Set default CORS origins to allow all hosts for Replit proxy compatibility
