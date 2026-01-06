# GoVector

## Overview
GoVector is a free image-to-vector converter that transforms raster images (JPG, PNG, HEIC) into print-ready vector formats (SVG, EPS, PDF). Built for designers, print shops, and anyone who needs scalable graphics.

**Tagline:** Scale up. Never blur.

## Tech Stack
- **Backend:** FastAPI (Python 3.11)
- **Frontend:** React + Vite + Tailwind CSS (TypeScript)
- **Image Processing:** Pillow, rembg (background removal), pillow-heif
- **Vectorization:** VTracer (Rust-based CLI tool)
- **Format Conversion:** CairoSVG (SVG to EPS/PDF)

## Project Structure
```
├── main.py              # FastAPI app entry point (serves frontend + API)
├── config.py            # Settings management (pydantic-settings)
├── models.py            # Pydantic models
├── api/routes.py        # API endpoints
├── workers/processing.py # Background job functions
├── services/            # Business logic
│   ├── image_processing.py  # Image preprocessing
│   ├── vectorization.py     # VTracer wrapper
│   └── storage.py           # File storage
├── utils/               # Helpers and validation
├── tests/               # Test files
└── frontend/            # React frontend
    ├── src/App.tsx      # Main React component
    └── dist/            # Built frontend (served by FastAPI)
```

## Running the Project
The server runs on port 5000 and serves both the API and frontend:
```bash
python -m uvicorn main:app --host 0.0.0.0 --port 5000 --reload
```

## API Endpoints
- `GET /` - Frontend app (GoVector UI)
- `GET /docs` - Swagger API documentation
- `GET /api/health` - Health check
- `POST /api/upload` - Upload image for conversion
- `GET /api/status/{job_id}` - Check conversion status
- `GET /api/result/{job_id}` - Get conversion results
- `GET /api/files/{job_id}/{filename}` - Download converted files

## Configuration
Settings loaded from environment variables:
- `CORS_ORIGINS` - Allowed CORS origins (default: *)
- `REDIS_URL` - Redis connection URL (optional, for async processing)
- `BLOB_READ_WRITE_TOKEN` - Vercel Blob storage token (optional)
- `MAX_FILE_SIZE_MB` - Maximum upload file size (default: 10MB)
- `DEBUG` - Enable debug mode (default: false)

## Frontend Features
- Drag-and-drop file upload
- Progress bar with processing stages
- Before/after image preview
- Download buttons for SVG, EPS, PDF
- Educational content about vector formats
- Mobile-responsive design
- Branded by GoProductmgt

## Branding
- **Name:** GoVector
- **Domain:** govector.ink
- **Tagline:** "Scale up. Never blur."
- **Parent brand:** GoProductmgt (goproductmgt.com)
- **Color scheme:** Emerald green (#10B981) as primary

## Recent Changes
- 2026-01-06: Rebranded to GoVector
  - New emerald green color scheme
  - Educational content about SVG, EPS, PDF formats
  - "Why go vector?" section explaining benefits
  - Clever taglines and improved copy
  - Updated meta tags for SEO
- 2026-01-06: Added React frontend with full conversion workflow
- 2026-01-06: Installed VTracer CLI for vectorization
- 2026-01-04: Initial Replit environment setup
