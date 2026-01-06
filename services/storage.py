"""
Storage Service
Handles file storage for the Vector Conversion Helper.

MVP Implementation: Local filesystem storage on Replit.
Files are stored in a structured directory and served via the API.

Future: Can be swapped for Vercel Blob, Cloudflare R2, or S3
by implementing the same interface.

Usage:
    from services.storage import StorageService
    
    storage = StorageService()
    
    # Save a file
    url = storage.save_file(job_id="abc123", filename="output.svg", file_bytes=b"...")
    
    # Get file path
    path = storage.get_file_path(job_id="abc123", filename="output.svg")
    
    # List job files
    files = storage.list_job_files(job_id="abc123")
    
    # Clean up old jobs
    storage.cleanup_old_jobs(max_age_hours=24)
"""

import os
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional



class StorageService:
    """
    Local filesystem storage for job files.
    
    Directory structure:
        storage/
        └── jobs/
            └── {job_id}/
                ├── original.png
                ├── normalized.png
                ├── preprocessed.png
                ├── output.svg
                ├── output.eps
                └── output.pdf
    """
    
    def __init__(self, base_path: Optional[str] = None):
        """
        Initialize storage service.
        
        Args:
            base_path: Root directory for storage. Defaults to ./storage
        """
        if base_path:
            self.base_path = Path(base_path)
        else:
            self.base_path = Path("storage")
        
        self.jobs_path = self.base_path / "jobs"
        
        # Ensure directories exist
        self.jobs_path.mkdir(parents=True, exist_ok=True)
    
    def get_job_dir(self, job_id: str) -> Path:
        """
        Get the directory path for a job, creating it if needed.
        
        Args:
            job_id: Unique job identifier
            
        Returns:
            Path to job directory
        """
        job_dir = self.jobs_path / job_id
        job_dir.mkdir(parents=True, exist_ok=True)
        return job_dir
    
    def save_file(self, job_id: str, filename: str, file_bytes: bytes) -> str:
        """
        Save a file for a job.
        
        Args:
            job_id: Unique job identifier
            filename: Name of file (e.g., "output.svg")
            file_bytes: File content as bytes
            
        Returns:
            URL path to access the file (e.g., "/api/files/abc123/output.svg")
        """
        job_dir = self.get_job_dir(job_id)
        file_path = job_dir / filename
        
        file_path.write_bytes(file_bytes)
        
        # Return URL path (will be served by API)
        return f"/api/files/{job_id}/{filename}"
    
    def save_file_from_path(self, job_id: str, source_path: str, filename: Optional[str] = None) -> str:
        """
        Copy a file from a source path to job storage.
        
        Args:
            job_id: Unique job identifier
            source_path: Path to source file
            filename: Optional new filename (defaults to source filename)
            
        Returns:
            URL path to access the file
        """
        source = Path(source_path)
        
        if not source.exists():
            raise FileNotFoundError(f"Source file not found: {source_path}")
        
        if filename is None:
            filename = source.name
        
        job_dir = self.get_job_dir(job_id)
        dest_path = job_dir / filename
        
        shutil.copy2(source, dest_path)
        
        return f"/api/files/{job_id}/{filename}"
    
    def get_file_path(self, job_id: str, filename: str) -> Optional[Path]:
        """
        Get the filesystem path for a stored file.
        
        Args:
            job_id: Unique job identifier
            filename: Name of file
            
        Returns:
            Path to file, or None if not found
        """
        file_path = self.jobs_path / job_id / filename
        
        if file_path.exists():
            return file_path
        return None
    
    def get_file_bytes(self, job_id: str, filename: str) -> Optional[bytes]:
        """
        Read a stored file's contents.
        
        Args:
            job_id: Unique job identifier
            filename: Name of file
            
        Returns:
            File contents as bytes, or None if not found
        """
        file_path = self.get_file_path(job_id, filename)
        
        if file_path:
            return file_path.read_bytes()
        return None
    
    def list_job_files(self, job_id: str) -> list[str]:
        """
        List all files for a job.
        
        Args:
            job_id: Unique job identifier
            
        Returns:
            List of filenames
        """
        job_dir = self.jobs_path / job_id
        
        if not job_dir.exists():
            return []
        
        return [f.name for f in job_dir.iterdir() if f.is_file()]
    
    def job_exists(self, job_id: str) -> bool:
        """Check if a job directory exists."""
        return (self.jobs_path / job_id).exists()
    
    def delete_job(self, job_id: str) -> bool:
        """
        Delete all files for a job.
        
        Args:
            job_id: Unique job identifier
            
        Returns:
            True if deleted, False if job didn't exist
        """
        job_dir = self.jobs_path / job_id
        
        if job_dir.exists():
            shutil.rmtree(job_dir)
            return True
        return False
    
    def get_job_urls(self, job_id: str, base_url: str = "") -> dict[str, str]:
        """
        Get download URLs for all files in a job.
        
        Args:
            job_id: Unique job identifier
            base_url: Optional base URL to prepend (e.g., "https://your-app.repl.co")
            
        Returns:
            Dictionary mapping filename to URL
        """
        files = self.list_job_files(job_id)
        
        return {
            filename: f"{base_url}/api/files/{job_id}/{filename}"
            for filename in files
        }
    
    def cleanup_old_jobs(self, max_age_hours: int = 24) -> int:
        """
        Delete jobs older than max_age_hours.
        
        Args:
            max_age_hours: Maximum age in hours before deletion
            
        Returns:
            Number of jobs deleted
        """
        cutoff = datetime.now() - timedelta(hours=max_age_hours)
        deleted_count = 0
        
        for job_dir in self.jobs_path.iterdir():
            if not job_dir.is_dir():
                continue
            
            # Check directory modification time
            mtime = datetime.fromtimestamp(job_dir.stat().st_mtime)
            
            if mtime < cutoff:
                shutil.rmtree(job_dir)
                deleted_count += 1
        
        return deleted_count
    
    def get_storage_stats(self) -> dict:
        """
        Get storage statistics.
        
        Returns:
            Dictionary with storage stats
        """
        total_size = 0
        job_count = 0
        file_count = 0
        
        for job_dir in self.jobs_path.iterdir():
            if not job_dir.is_dir():
                continue
            
            job_count += 1
            
            for file_path in job_dir.iterdir():
                if file_path.is_file():
                    file_count += 1
                    total_size += file_path.stat().st_size
        
        return {
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "job_count": job_count,
            "file_count": file_count,
            "storage_path": str(self.base_path.absolute()),
        }