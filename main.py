"""
FastAPI application entry point.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import get_settings
from api.routes import router

settings = get_settings()

# Create FastAPI app
app = FastAPI(
    title="Vector Conversion Helper",
    description="Convert raster images to vector formats for print shops",
    version="0.1.0",
)

# Configure CORS (allows frontend to call this API)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routes
app.include_router(router, prefix="/api")


@app.get("/")
async def root():
    """Root endpoint - confirms API is running."""
    return {
        "message": "Vector Conversion Helper API",
        "docs": "/docs",
        "health": "/api/health",
    }