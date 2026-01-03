"""
Custom exceptions for Vector Conversion Helper.
These provide clear, specific error handling throughout the app.
"""

from models import ErrorCode


class VectorConversionError(Exception):
    """Base exception for all app errors."""
    
    def __init__(self, message: str, error_code: ErrorCode):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class InvalidFileTypeError(VectorConversionError):
    """Raised when uploaded file is not JPG, PNG, or HEIC."""
    
    def __init__(self, message: str = "File must be JPG, PNG, or HEIC"):
        super().__init__(message, ErrorCode.INVALID_FILE_TYPE)


class FileTooLargeError(VectorConversionError):
    """Raised when file exceeds size limit."""
    
    def __init__(self, message: str = "File exceeds size limit"):
        super().__init__(message, ErrorCode.FILE_TOO_LARGE)


class ProcessingTimeoutError(VectorConversionError):
    """Raised when processing takes too long."""
    
    def __init__(self, message: str = "Processing timed out"):
        super().__init__(message, ErrorCode.PROCESSING_TIMEOUT)


class VectorizationFailedError(VectorConversionError):
    """Raised when potrace fails to convert the image."""
    
    def __init__(self, message: str = "Vectorization failed"):
        super().__init__(message, ErrorCode.VECTORIZATION_FAILED)


class ImageTooComplexError(VectorConversionError):
    """Raised when image has too many colors/gradients for good vectorization."""
    
    def __init__(self, message: str = "Image too complex for vectorization"):
        super().__init__(message, ErrorCode.TOO_COMPLEX)