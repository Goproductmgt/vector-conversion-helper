"""
API route definitions.
Defines the three main endpoints: upload, status, and result.
"""

from fastapi import APIRouter, UploadFile, File, HTTPException
from datetime import datetime, timezone
import uuid

from models import (
    UploadResponse,
    StatusResponse,
    ResultResponse,
    ErrorResponse,
    HealthResponse,
    JobStatus,
    ErrorCode,
)
from config import get_settings

router = APIRouter()
settings = get_settings()

# Temporary in-memory storage for jobs (will be replaced with Redis later)
jobs_db: dict = {}


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse()


@router.post("/upload", response_model=UploadResponse)
async def upload_file(file: UploadFile = File(...)):
    """
    Upload a raster image for conversion.
    
    Accepts: JPG, PNG, HEIC
    Returns: job_id to track progress
    """
    # Validate file size
    contents = await file.read()
    if len(contents) > settings.max_file_size_bytes:
        raise HTTPException(
            status_code=413,
            detail={
                "error_code": ErrorCode.FILE_TOO_LARGE.value,
                "error_message": f"File exceeds {settings.max_file_size_mb}MB limit",
            }
        )
    
    # Generate job ID
    job_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    
    # Store job info (temporary - will use Redis later)
    jobs_db[job_id] = {
        "status": JobStatus.QUEUED,
        "progress": 0,
        "stage": "Queued for processing",
        "created_at": now,
        "updated_at": now,
        "filename": file.filename,
        "file_size": len(contents),
        "contents": contents,  # Temporary - will use blob storage later
    }
    
    # TODO: Queue background job here
    
    return UploadResponse(
        job_id=job_id,
        status=JobStatus.QUEUED,
        created_at=now,
    )


@router.get("/status/{job_id}", response_model=StatusResponse)
async def get_status(job_id: str):
    """
    Check the status of a conversion job.
    """
    if job_id not in jobs_db:
        raise HTTPException(
            status_code=404,
            detail={
                "error_code": ErrorCode.JOB_NOT_FOUND.value,
                "error_message": f"Job {job_id} not found",
            }
        )
    
    job = jobs_db[job_id]
    
    return StatusResponse(
        job_id=job_id,
        status=job["status"],
        progress=job["progress"],
        stage=job["stage"],
        created_at=job["created_at"],
        updated_at=job["updated_at"],
    )


@router.get("/result/{job_id}")
async def get_result(job_id: str):
    """
    Get the result of a completed conversion job.
    
    Returns download URLs for all output files.
    """
    if job_id not in jobs_db:
        raise HTTPException(
            status_code=404,
            detail={
                "error_code": ErrorCode.JOB_NOT_FOUND.value,
                "error_message": f"Job {job_id} not found",
            }
        )
    
    job = jobs_db[job_id]
    
    if job["status"] == JobStatus.FAILED:
        raise HTTPException(
            status_code=400,
            detail={
                "error_code": job.get("error_code", ErrorCode.VECTORIZATION_FAILED.value),
                "error_message": job.get("error_message", "Job failed"),
            }
        )
    
    if job["status"] != JobStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail={
                "error_code": "JOB_NOT_COMPLETE",
                "error_message": f"Job is still {job['status'].value}. Check /status/{job_id}",
            }
        )
    
    # Return result (placeholder - will have real URLs later)
    return {
        "job_id": job_id,
        "status": "completed",
        "files": job.get("files", {}),
        "metadata": job.get("metadata", {}),
        "created_at": job["created_at"],
        "completed_at": job.get("completed_at", job["updated_at"]),
    }