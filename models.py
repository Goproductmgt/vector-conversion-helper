"""
Pydantic models for API requests and responses.
These define the "contract" between frontend and backend.
"""

from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class JobStatus(str, Enum):
    """Possible states for a conversion job."""
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ErrorCode(str, Enum):
    """Specific error codes for failed jobs."""
    INVALID_FILE_TYPE = "INVALID_FILE_TYPE"
    FILE_TOO_LARGE = "FILE_TOO_LARGE"
    PROCESSING_TIMEOUT = "PROCESSING_TIMEOUT"
    VECTORIZATION_FAILED = "VECTORIZATION_FAILED"
    BACKGROUND_REMOVAL_FAILED = "BACKGROUND_REMOVAL_FAILED"
    TOO_COMPLEX = "TOO_COMPLEX"
    JOB_NOT_FOUND = "JOB_NOT_FOUND"


# --- API Response Models ---

class UploadResponse(BaseModel):
    """Response returned after successful file upload."""
    job_id: str
    status: JobStatus = JobStatus.QUEUED
    created_at: datetime


class StatusResponse(BaseModel):
    """Response for job status check."""
    job_id: str
    status: JobStatus
    progress: int = Field(ge=0, le=100, description="Progress percentage 0-100")
    stage: str = Field(description="Current processing stage description")
    created_at: datetime
    updated_at: datetime


class FileUrls(BaseModel):
    """URLs for all output files."""
    original: str
    svg: str
    eps: str
    pdf: str


class JobMetadata(BaseModel):
    """Metadata about the completed job."""
    original_format: str
    original_size_bytes: int
    processing_time_seconds: float


class ResultResponse(BaseModel):
    """Response for completed job with download URLs."""
    job_id: str
    status: JobStatus = JobStatus.COMPLETED
    files: FileUrls
    metadata: JobMetadata
    created_at: datetime
    completed_at: datetime


class ErrorResponse(BaseModel):
    """Response for failed jobs or errors."""
    job_id: str | None = None
    status: JobStatus = JobStatus.FAILED
    error_code: ErrorCode
    error_message: str
    retry_allowed: bool = False


class HealthResponse(BaseModel):
    """Response for health check endpoint."""
    status: str = "healthy"
    version: str = "0.1.0"