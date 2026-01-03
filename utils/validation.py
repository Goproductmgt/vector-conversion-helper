"""
File validation utilities.
Uses magic bytes (not file extension) to verify file types.
"""

from utils.errors import InvalidFileTypeError, FileTooLargeError
from config import get_settings

# Magic bytes for supported file types
# These are the first bytes of a file that identify its format
MAGIC_BYTES = {
    "jpg": [
        bytes([0xFF, 0xD8, 0xFF, 0xE0]),  # JFIF
        bytes([0xFF, 0xD8, 0xFF, 0xE1]),  # EXIF
        bytes([0xFF, 0xD8, 0xFF, 0xDB]),  # Raw JPEG
    ],
    "png": [
        bytes([0x89, 0x50, 0x4E, 0x47]),  # PNG signature
    ],
    "heic": [
        b"ftypheic",  # HEIC
        b"ftypheix",  # HEIC
        b"ftypmif1",  # HEIF
        b"ftypmsf1",  # HEIF sequence
    ],
}


def detect_file_type(content: bytes) -> str | None:
    """
    Detect file type from magic bytes.
    
    Args:
        content: Raw file bytes
        
    Returns:
        File type string ('jpg', 'png', 'heic') or None if unknown
    """
    if len(content) < 12:
        return None
    
    # Check JPG (first 4 bytes)
    for magic in MAGIC_BYTES["jpg"]:
        if content[:4] == magic:
            return "jpg"
    
    # Check PNG (first 4 bytes)
    for magic in MAGIC_BYTES["png"]:
        if content[:4] == magic:
            return "png"
    
    # Check HEIC (bytes 4-12 contain the ftyp marker)
    for magic in MAGIC_BYTES["heic"]:
        if magic in content[4:12]:
            return "heic"
    
    return None


def validate_file(content: bytes, filename: str) -> str:
    """
    Validate uploaded file content.
    
    Args:
        content: Raw file bytes
        filename: Original filename (for error messages only)
        
    Returns:
        Detected file type ('jpg', 'png', 'heic')
        
    Raises:
        FileTooLargeError: If file exceeds size limit
        InvalidFileTypeError: If file is not a supported type
    """
    settings = get_settings()
    
    # Check size
    if len(content) > settings.max_file_size_bytes:
        raise FileTooLargeError(
            f"File is {len(content) / 1024 / 1024:.1f}MB, "
            f"max is {settings.max_file_size_mb}MB"
        )
    
    # Check type via magic bytes
    file_type = detect_file_type(content)
    
    if file_type is None:
        raise InvalidFileTypeError(
            f"'{filename}' is not a valid JPG, PNG, or HEIC file"
        )
    
    return file_type