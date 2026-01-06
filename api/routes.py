"""
API Routes
Handles all HTTP endpoints for GoVector.

Endpoints:
- POST /api/upload - Upload an image for conversion
- GET /api/status/{job_id} - Check job status
- GET /api/result/{job_id} - Get job result and file URLs
- GET /api/files/{job_id}/{filename} - Download a file
- POST /api/email - Email converted files
"""

import shutil
import tempfile
from pathlib import Path
from typing import Optional

import requests
from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, EmailStr

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
from config import get_settings


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
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "govector",
    }


class EmailRequest(BaseModel):
    job_id: str
    recipient_email: EmailStr
    file_format: str


@router.post("/email")
async def email_file(request: EmailRequest):
    """
    Email a converted file to the specified recipient.
    
    Requires: MAILGUN_API_KEY, MAILGUN_DOMAIN, MAILGUN_FROM_EMAIL env vars
    """
    settings = get_settings()
    
    if not settings.mailgun_api_key or not settings.mailgun_domain:
        raise HTTPException(
            status_code=503,
            detail="Email service not configured. Please set MAILGUN_API_KEY and MAILGUN_DOMAIN."
        )
    
    status = get_job_status(request.job_id)
    if not status:
        raise HTTPException(status_code=404, detail=f"Job not found: {request.job_id}")
    
    if status["status"] != "completed":
        raise HTTPException(status_code=400, detail="Job not completed yet")
    
    format_to_filename = {
        "svg": "output.svg",
        "eps": "output.eps",
        "pdf": "output.pdf",
    }
    
    filename = format_to_filename.get(request.file_format.lower())
    if not filename:
        raise HTTPException(status_code=400, detail=f"Invalid format: {request.file_format}")
    
    file_path = storage.get_file_path(request.job_id, filename)
    if not file_path:
        raise HTTPException(status_code=404, detail=f"File not found: {filename}")
    
    content_types = {
        "svg": "image/svg+xml",
        "eps": "application/postscript",
        "pdf": "application/pdf",
    }
    
    from_email = settings.mailgun_from_email or f"GoVector <noreply@{settings.mailgun_domain}>"
    
    try:
        with open(file_path, "rb") as f:
            response = requests.post(
                settings.mailgun_api_url,
                auth=("api", settings.mailgun_api_key),
                files=[
                    ("attachment", (f"govector-output.{request.file_format.lower()}", f, content_types.get(request.file_format.lower(), "application/octet-stream")))
                ],
                data={
                    "from": from_email,
                    "to": [request.recipient_email],
                    "subject": "Your GoVector file is ready",
                    "html": f"""
                        <div style="font-family: Georgia, serif; max-width: 600px; margin: 0 auto;">
                            <h1 style="color: #10B981;">GoVector</h1>
                            <p>Your vector file is attached and ready to use.</p>
                            <p style="color: #666;">
                                <strong>Format:</strong> {request.file_format.upper()}<br>
                                <strong>File:</strong> govector-output.{request.file_format.lower()}
                            </p>
                            <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
                            <p style="color: #999; font-size: 12px;">
                                Sent from <a href="https://govector.ink" style="color: #10B981;">GoVector</a> - Free image to vector converter
                            </p>
                        </div>
                    """,
                },
                timeout=30,
            )
        
        if response.status_code == 200:
            return {
                "success": True,
                "message": f"File sent to {request.recipient_email}",
            }
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to send email: {response.text}"
            )
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Email service error: {str(e)}")