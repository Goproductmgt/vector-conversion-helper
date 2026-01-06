"""
Custom Exception Classes
Provides clear, specific errors for different failure modes.

Usage:
    from utils.errors import ValidationError, ProcessingError, VectorizationError
    
    raise ValidationError("File type not supported")
    raise ProcessingError("Background removal failed")
    raise VectorizationError("Potrace timed out")
"""


class VectorConversionError(Exception):
    """Base exception for all Vector Conversion Helper errors."""
    
    def __init__(self, message: str, code: str = "UNKNOWN_ERROR"):
        self.message = message
        self.code = code
        super().__init__(self.message)


class ValidationError(VectorConversionError):
    """
    Raised when input validation fails.
    
    Examples:
    - Unsupported file type
    - File too large
    - Empty file
    """
    
    def __init__(self, message: str):
        super().__init__(message, code="VALIDATION_ERROR")


class ProcessingError(VectorConversionError):
    """
    Raised when image processing fails.
    
    Examples:
    - Failed to open image
    - Background removal failed
    - Image conversion failed
    """
    
    def __init__(self, message: str):
        super().__init__(message, code="PROCESSING_ERROR")


class VectorizationError(VectorConversionError):
    """
    Raised when vectorization fails.
    
    Examples:
    - Potrace not installed
    - Potrace timed out
    - Output file not created
    """
    
    def __init__(self, message: str):
        super().__init__(message, code="VECTORIZATION_ERROR")


class StorageError(VectorConversionError):
    """
    Raised when storage operations fail.
    
    Examples:
    - Failed to save file
    - File not found
    - Permission denied
    """
    
    def __init__(self, message: str):
        super().__init__(message, code="STORAGE_ERROR")


class JobNotFoundError(VectorConversionError):
    """
    Raised when a job ID is not found.
    """
    
    def __init__(self, job_id: str):
        super().__init__(f"Job not found: {job_id}", code="JOB_NOT_FOUND")
        self.job_id = job_id