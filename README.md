# Vector Conversion Helper

A backend API that converts raster images (JPG, PNG, HEIC) to vector formats (SVG, EPS, PDF) for print shops.

## Quick Start

1. Create virtual environment:
```bash
   python3 -m venv venv
   source venv/bin/activate
```

2. Install dependencies:
```bash
   pip install -r requirements.txt
```

3. Copy `.env.example` to `.env` and fill in your values

4. Run the server:
```bash
   uvicorn main:app --reload
```

## Tech Stack

- **Framework:** FastAPI
- **Image Processing:** Pillow, rembg, Potrace
- **Job Queue:** Redis + RQ
- **Storage:** Vercel Blob

## Project Structure
```
├── main.py              # FastAPI app entry
├── config.py            # Settings management
├── models.py            # Pydantic models
├── api/routes.py        # API endpoints
├── workers/processing.py # Background job functions
├── services/            # Business logic
└── utils/               # Helpers and validation
```