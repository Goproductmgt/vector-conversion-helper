"""
API Routes
Handles all HTTP endpoints for the Vector Conversion Helper.

Endpoints:
- POST /api/upload - Upload an image for conversion
- GET /api/status/{job_id} - Check job status
- GET /api/result/{job_id} - Get job result and file URLs
- GET /api/files/{job_id}/{filename} - Download a file
"""

import shutil
import tempfile
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import FileResponse

from models import (
    UploadResponse,
    StatusResponse,
    ResultResponse,
    ErrorResponse,
)
from utils.validation import validate_file_type, validate_file_size
from utils.errors import ValidationError
from workers.processing import (
    create_job,
    process_job,
    get_job_status,
)
from services.storage import StorageService


router = APIRouter(tags=["conversion"])

# Initialize storage service
storage = StorageService()


@router.post("/upload", response_model=UploadResponse)
async def upload_file(file: UploadFile = File(...)):
    """
    Upload an image for vector conversion.
    
    Accepts: JPG, PNG, HEIC (max 10MB)
    Returns: job_id to track processing status
    """
    # Read file content
    content = await file.read()
    
    # Validate file type (magic bytes)
    try:
        detected_type = validate_file_type(content)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Validate file size
    try:
        validate_file_size(content)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Create job
    original_filename = file.filename or "upload"
    job_id = create_job(original_filename)
    
    # Save uploaded file to temp location
    job_dir = storage.get_job_dir(job_id)
    
    # Determine extension from detected type
    ext_map = {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/heic": ".heic",
    }
    ext = ext_map.get(detected_type, ".png")
    temp_upload_path = job_dir / f"upload{ext}"
    
    # Write file
    temp_upload_path.write_bytes(content)
    
    # Process synchronously for MVP (async with RQ later)
    # This blocks but keeps MVP simple
    result = process_job(job_id, str(temp_upload_path))
    
    # Get final status
    status = get_job_status(job_id)
    
    return UploadResponse(
        job_id=job_id,
        status=status["status"],
        created_at=status["created_at"],
    )


@router.get("/status/{job_id}", response_model=StatusResponse)
async def get_status(job_id: str):
    """
    Get the current status of a conversion job.
    
    Returns: status, progress percentage, current stage
    """
    status = get_job_status(job_id)
    
    if not status:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")
    
    return StatusResponse(
        job_id=job_id,
        status=status["status"],
        progress=status.get("progress", 0),
        stage=status.get("stage", "Unknown"),
        created_at=status["created_at"],
        updated_at=status["updated_at"],
    )


@router.get("/result/{job_id}")
async def get_result(job_id: str):
    """
    Get the result of a completed conversion job.
    
    Returns: file URLs for original and converted files
    """
    status = get_job_status(job_id)
    
    if not status:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")
    
    if status["status"] == "failed":
        return {
            "job_id": job_id,
            "status": "failed",
            "error_code": status.get("error_code", "UNKNOWN"),
            "error_message": status.get("error_message", "Processing failed"),
        }
    
    if status["status"] != "completed":
        return {
            "job_id": job_id,
            "status": status["status"],
            "message": "Job is still processing. Check /api/status/{job_id} for progress.",
        }
    
    return {
        "job_id": job_id,
        "status": "completed",
        "files": status.get("files", {}),
        "metadata": status.get("metadata", {}),
        "created_at": status["created_at"],
        "completed_at": status.get("completed_at"),
    }


@router.get("/files/{job_id}/{filename}")
async def download_file(job_id: str, filename: str):
    """
    Download a file from a completed job.
    
    Files available:
    - original.{jpg,png,heic} - Original uploaded file
    - output.svg - Vector SVG output
    - output.eps - Vector EPS output
    - output.pdf - Vector PDF output
    """
    file_path = storage.get_file_path(job_id, filename)
    
    if not file_path:
        raise HTTPException(status_code=404, detail=f"File not found: {filename}")
    
    # Determine content type
    content_types = {
        ".svg": "image/svg+xml",
        ".eps": "application/postscript",
        ".pdf": "application/pdf",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".heic": "image/heic",
    }
    
    suffix = file_path.suffix.lower()
    content_type = content_types.get(suffix, "application/octet-stream")
    
    return FileResponse(
        path=file_path,
        media_type=content_type,
        filename=filename,
    )


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "vector-conversion-helper",
    }