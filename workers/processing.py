"""
Processing Worker
Orchestrates the full image-to-vector conversion pipeline.

This module ties together:
- ImageProcessingService: Normalize, remove background
- VectorizationService: Convert to SVG, EPS, PDF via VTracer
- EnhancementService: Upscale/clean images via Real-ESRGAN (Tier 2)
- StorageService: Save all files and generate URLs

Usage:
    from workers.processing import process_job, process_enhanced_job
    
    # Tier 1: Basic vectorization (free)
    result = process_job(job_id="abc123", input_path="/path/to/upload.jpg")
    
    # Tier 2: Enhanced vectorization (~$0.003)
    result = process_enhanced_job(job_id="abc123")

For background processing with RQ:
    from redis import Redis
    from rq import Queue
    
    q = Queue(connection=Redis())
    job = q.enqueue(process_job, job_id="abc123", input_path="/path/to/file")
"""

import time
import traceback
from pathlib import Path
from datetime import datetime
from typing import Optional
from uuid import uuid4

from services.image_processing import ImageProcessingService
from services.vectorization import VectorizationService
from services.storage import StorageService
from utils.errors import ProcessingError, VectorizationError


# Job status tracking (in-memory for MVP, Redis for production)
# Structure: {job_id: {status, progress, stage, error, created_at, ...}}
_job_status: dict[str, dict] = {}


def get_job_status(job_id: str) -> Optional[dict]:
    """Get current status of a job."""
    return _job_status.get(job_id)


def set_job_status(job_id: str, **kwargs) -> None:
    """Update job status fields."""
    if job_id not in _job_status:
        _job_status[job_id] = {
            "job_id": job_id,
            "status": "queued",
            "progress": 0,
            "stage": "Initializing...",
            "created_at": datetime.utcnow().isoformat() + "Z",
            "updated_at": datetime.utcnow().isoformat() + "Z",
        }
    
    _job_status[job_id].update(kwargs)
    _job_status[job_id]["updated_at"] = datetime.utcnow().isoformat() + "Z"


def create_job(original_filename: str) -> str:
    """
    Create a new job and return its ID.
    
    Args:
        original_filename: Name of uploaded file
        
    Returns:
        Unique job ID
    """
    job_id = str(uuid4())
    
    set_job_status(
        job_id,
        status="queued",
        progress=0,
        stage="Queued for processing",
        original_filename=original_filename,
    )
    
    return job_id


def process_job(job_id: str, input_path: str) -> dict:
    """
    Process an uploaded image through the full pipeline (Tier 1 - Free).
    
    Pipeline stages:
    1. Initialize (0-10%)
    2. Preprocess image (10-40%)
    3. Vectorize (40-80%)
    4. Save files (80-100%)
    
    Args:
        job_id: Unique job identifier
        input_path: Path to uploaded file
        
    Returns:
        Dictionary with job result:
        {
            "status": "completed",
            "files": {"original": "...", "svg": "...", "eps": "...", "pdf": "..."},
            "metadata": {"processing_time_seconds": 5.2, ...}
        }
    """
    start_time = time.time()
    
    # Initialize services
    storage = StorageService()
    image_processor = ImageProcessingService()
    vectorizer = VectorizationService()
    
    try:
        # Stage 1: Initialize
        set_job_status(job_id, status="processing", progress=5, stage="Starting...")
        
        input_path = Path(input_path)
        if not input_path.exists():
            raise ProcessingError(f"Input file not found: {input_path}")
        
        # Get job directory for intermediate files
        job_dir = storage.get_job_dir(job_id)
        
        # Save original file
        set_job_status(job_id, progress=10, stage="Saving original...")
        original_ext = input_path.suffix.lower()
        original_filename = f"original{original_ext}"
        storage.save_file_from_path(job_id, str(input_path), original_filename)
        
        # Stage 2: Preprocess
        set_job_status(job_id, progress=20, stage="Preprocessing image...")
        
        preprocess_result = image_processor.preprocess(
            input_path=str(input_path),
            output_dir=str(job_dir),
            job_id=job_id,
        )
        
        set_job_status(job_id, progress=40, stage="Image preprocessed")
        
        # Stage 3: Vectorize
        set_job_status(job_id, progress=50, stage="Converting to vectors...")
        
        vector_result = vectorizer.vectorize(
            input_path=preprocess_result["preprocessed_path"],
            output_dir=str(job_dir),
        )
        
        set_job_status(job_id, progress=80, stage="Vectorization complete")
        
        # Stage 4: Finalize
        set_job_status(job_id, progress=90, stage="Finalizing...")
        
        # Calculate processing time
        processing_time = round(time.time() - start_time, 2)
        
        # Build file URLs
        files = {
            "original": f"/api/files/{job_id}/{original_filename}",
            "svg": f"/api/files/{job_id}/output.svg",
            "eps": f"/api/files/{job_id}/output.eps",
            "pdf": f"/api/files/{job_id}/output.pdf",
        }
        
        # Build metadata
        metadata = {
            "original_format": preprocess_result["original_format"],
            "original_size": preprocess_result["original_size"],
            "background_removed": preprocess_result["background_removed"],
            "processing_time_seconds": processing_time,
            "tier": "basic",
        }
        
        # Mark complete
        set_job_status(
            job_id,
            status="completed",
            progress=100,
            stage="Complete",
            files=files,
            metadata=metadata,
            completed_at=datetime.utcnow().isoformat() + "Z",
        )
        
        return {
            "status": "completed",
            "job_id": job_id,
            "files": files,
            "metadata": metadata,
        }
        
    except (ProcessingError, VectorizationError) as e:
        # Known error - report clearly
        set_job_status(
            job_id,
            status="failed",
            progress=0,
            stage="Failed",
            error_code=type(e).__name__,
            error_message=str(e),
        )
        
        return {
            "status": "failed",
            "job_id": job_id,
            "error_code": type(e).__name__,
            "error_message": str(e),
        }
        
    except Exception as e:
        # Unexpected error - log full traceback
        error_trace = traceback.format_exc()
        print(f"Unexpected error processing job {job_id}:\n{error_trace}")
        
        set_job_status(
            job_id,
            status="failed",
            progress=0,
            stage="Failed",
            error_code="UNEXPECTED_ERROR",
            error_message=f"An unexpected error occurred: {str(e)}",
        )
        
        return {
            "status": "failed",
            "job_id": job_id,
            "error_code": "UNEXPECTED_ERROR",
            "error_message": str(e),
        }


def process_enhanced_job(job_id: str) -> dict:
    """
    Enhance an existing job's image and re-vectorize (Tier 2 - ~$0.003).
    
    This takes a completed job, runs the original image through Real-ESRGAN
    for 4x upscaling and noise removal, then re-vectorizes the enhanced image.
    
    Pipeline stages:
    1. Load original image (0-10%)
    2. Enhance with Real-ESRGAN (10-60%)
    3. Re-vectorize enhanced image (60-90%)
    4. Save enhanced files (90-100%)
    
    Args:
        job_id: ID of an existing completed job
        
    Returns:
        Dictionary with enhanced job result:
        {
            "status": "completed",
            "files": {
                "original": "...",
                "svg": "...",              # Original vectorization
                "eps": "...",
                "pdf": "...",
                "enhanced_svg": "...",     # Enhanced vectorization
                "enhanced_eps": "...",
                "enhanced_pdf": "..."
            },
            "metadata": {..., "enhancement_time_seconds": 15.2}
        }
    """
    # Lazy import to avoid loading Replicate unless needed
    from services.enhancement import EnhancementService
    
    start_time = time.time()
    
    # Initialize services
    storage = StorageService()
    image_processor = ImageProcessingService()
    vectorizer = VectorizationService()
    enhancer = EnhancementService()
    
    try:
        # Check if enhancement is available
        if not enhancer.is_available():
            raise ProcessingError(
                "Enhancement service not configured. "
                "REPLICATE_API_TOKEN is missing."
            )
        
        # Get existing job status
        existing_status = get_job_status(job_id)
        if not existing_status:
            raise ProcessingError(f"Job not found: {job_id}")
        
        if existing_status.get("status") != "completed":
            raise ProcessingError(
                f"Job must be completed before enhancement. "
                f"Current status: {existing_status.get('status')}"
            )
        
        # Stage 1: Load original image
        set_job_status(job_id, status="enhancing", progress=5, stage="Loading original image...")
        
        job_dir = storage.get_job_dir(job_id)
        
        # Find the original file (could be .jpg, .png, .heic)
        original_path = _find_original_file(job_dir)
        if not original_path:
            raise ProcessingError(f"Original file not found for job: {job_id}")
        
        # Stage 2: Enhance with Real-ESRGAN
        set_job_status(job_id, progress=10, stage="Enhancing image (this may take 15-20 seconds)...")
        
        enhance_result = enhancer.enhance(
            input_path=str(original_path),
            output_dir=str(job_dir),
            job_id=job_id,
        )
        
        set_job_status(job_id, progress=60, stage="Image enhanced, preprocessing...")
        
        # Stage 3: Preprocess the enhanced image (normalize, optional bg removal)
        enhanced_preprocess = image_processor.preprocess(
            input_path=enhance_result["enhanced_path"],
            output_dir=str(job_dir),
            job_id=f"{job_id}_enhanced",
        )
        
        set_job_status(job_id, progress=70, stage="Re-vectorizing enhanced image...")
        
        # Stage 4: Vectorize the enhanced image
        enhanced_vector_result = vectorizer.vectorize(
            input_path=enhanced_preprocess["preprocessed_path"],
            output_dir=str(job_dir),
            output_prefix="enhanced_",
        )
        
        set_job_status(job_id, progress=90, stage="Saving enhanced files...")
        
        # Calculate times
        enhancement_time = round(time.time() - start_time, 2)
        
        # Preserve existing files, add enhanced files
        existing_files = existing_status.get("files", {})
        files = {
            **existing_files,
            "enhanced_svg": f"/api/files/{job_id}/enhanced_output.svg",
            "enhanced_eps": f"/api/files/{job_id}/enhanced_output.eps",
            "enhanced_pdf": f"/api/files/{job_id}/enhanced_output.pdf",
        }
        
        # Update metadata
        existing_metadata = existing_status.get("metadata", {})
        metadata = {
            **existing_metadata,
            "enhanced": True,
            "enhancement_scale": enhance_result["scale"],
            "enhancement_time_seconds": enhancement_time,
            "tier": "enhanced",
        }
        
        # Mark complete
        set_job_status(
            job_id,
            status="completed",
            progress=100,
            stage="Enhancement complete",
            files=files,
            metadata=metadata,
            enhanced_at=datetime.utcnow().isoformat() + "Z",
        )
        
        return {
            "status": "completed",
            "job_id": job_id,
            "files": files,
            "metadata": metadata,
        }
        
    except ProcessingError as e:
        # Known error - report clearly
        set_job_status(
            job_id,
            status="enhancement_failed",
            stage="Enhancement failed",
            error_code="ProcessingError",
            error_message=str(e),
        )
        
        return {
            "status": "failed",
            "job_id": job_id,
            "error_code": "ProcessingError",
            "error_message": str(e),
        }
        
    except Exception as e:
        # Unexpected error
        error_trace = traceback.format_exc()
        print(f"Unexpected error enhancing job {job_id}:\n{error_trace}")
        
        set_job_status(
            job_id,
            status="enhancement_failed",
            stage="Enhancement failed",
            error_code="UNEXPECTED_ERROR",
            error_message=f"An unexpected error occurred: {str(e)}",
        )
        
        return {
            "status": "failed",
            "job_id": job_id,
            "error_code": "UNEXPECTED_ERROR",
            "error_message": str(e),
        }


def _find_original_file(job_dir: Path) -> Optional[Path]:
    """
    Find the original uploaded file in a job directory.
    
    Looks for files matching: original.jpg, original.png, original.heic, etc.
    """
    job_dir = Path(job_dir)
    
    # Check common extensions
    for ext in [".png", ".jpg", ".jpeg", ".heic", ".webp"]:
        original_path = job_dir / f"original{ext}"
        if original_path.exists():
            return original_path
    
    # Fallback: look for any file starting with "original"
    for file_path in job_dir.glob("original.*"):
        return file_path
    
    return None


def cleanup_temp_files(job_id: str) -> None:
    """
    Remove intermediate files for a job, keeping only final outputs.
    
    Keeps: original.*, output.svg, output.eps, output.pdf, enhanced_output.*
    Removes: *_normalized.png, *_preprocessed.png, temp_*, *_enhanced.png
    """
    storage = StorageService()
    job_dir = storage.jobs_path / job_id
    
    if not job_dir.exists():
        return
    
    # Patterns to remove
    remove_patterns = [
        "*_normalized.png",
        "*_preprocessed.png",
        "*_enhanced.png",
        "temp_*",
    ]
    
    for pattern in remove_patterns:
        for file_path in job_dir.glob(pattern):
            file_path.unlink()