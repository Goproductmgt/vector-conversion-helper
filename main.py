"""
FastAPI application entry point.
"""

from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from config import get_settings
from api.routes import router

settings = get_settings()

app = FastAPI(
    title="Vector Conversion Helper",
    description="Convert raster images to vector formats for print shops",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")

@app.get("/health")
async def root_health():
    """Fast health check for deployment."""
    return {"status": "ok"}

FRONTEND_DIR = Path(__file__).parent / "frontend" / "dist"

INDEX_FILE = FRONTEND_DIR / "index.html"
ASSETS_DIR = FRONTEND_DIR / "assets"

if ASSETS_DIR.exists():
    app.mount("/assets", StaticFiles(directory=ASSETS_DIR), name="assets")

@app.get("/")
async def serve_index():
    """Serve the frontend or fallback to API info."""
    if INDEX_FILE.exists():
        return FileResponse(INDEX_FILE, headers={"Cache-Control": "no-cache"})
    return {"status": "ok", "message": "GoVector API", "docs": "/docs"}

@app.head("/")
async def health_check_head():
    """Fast HEAD response for health checks."""
    return {"status": "ok"}

@app.get("/{full_path:path}")
async def serve_frontend(full_path: str):
    """Serve static files or fallback to index.html for client-side routing."""
    if not INDEX_FILE.exists():
        return {"status": "ok", "message": "GoVector API"}
    file_path = FRONTEND_DIR / full_path
    if file_path.exists() and file_path.is_file():
        return FileResponse(file_path)
    return FileResponse(INDEX_FILE)
