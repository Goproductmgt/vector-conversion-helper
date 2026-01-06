"""
File Validation Utilities
Validates uploaded files using magic bytes (not file extensions).

Magic bytes are the first few bytes of a file that identify its type.
This is more reliable than checking file extensions.
"""

from utils.errors import ValidationError

# Maximum file size in bytes (10MB)
MAX_FILE_SIZE = 10 * 1024 * 1024

# Magic bytes for supported image formats
# Format: {bytes_pattern: (mime_type, description)}
MAGIC_BYTES = {
    # JPEG: Starts with FF D8 FF
    b'\xff\xd8\xff': ("image/jpeg", "JPEG"),
    
    # PNG: Starts with 89 50 4E 47 0D 0A 1A 0A
    b'\x89PNG\r\n\x1a\n': ("image/png", "PNG"),
    
    # HEIC/HEIF: Starts with various ftyp signatures
    # Usually: XX XX XX XX 66 74 79 70 68 65 69 63 (ftyp heic)
    # or:      XX XX XX XX 66 74 79 70 6D 69 66 31 (ftyp mif1)
    b'ftypheic': ("image/heic", "HEIC"),
    b'ftypmif1': ("image/heic", "HEIC"),
    b'ftypheix': ("image/heic", "HEIC"),
}


def validate_file_type(content: bytes) -> str:
    """
    Validate file type using magic bytes.
    
    Args:
        content: File content as bytes
        
    Returns:
        MIME type string (e.g., "image/jpeg")
        
    Raises:
        ValidationError: If file type is not supported
    """
    if len(content) < 12:
        raise ValidationError("File too small to identify type")
    
    # Check standard magic bytes (JPEG, PNG)
    for magic, (mime_type, description) in MAGIC_BYTES.items():
        if magic in (b'\xff\xd8\xff', b'\x89PNG\r\n\x1a\n'):
            if content.startswith(magic):
                return mime_type
    
    # Check HEIC (magic bytes at offset 4)
    # HEIC files have "ftyp" at bytes 4-8, then format identifier
    if len(content) >= 12:
        ftyp_section = content[4:12]
        for magic, (mime_type, description) in MAGIC_BYTES.items():
            if magic.startswith(b'ftyp') and magic in ftyp_section:
                return mime_type
        
        # Additional HEIC check - look for "ftyp" marker
        if content[4:8] == b'ftyp':
            brand = content[8:12]
            heic_brands = [b'heic', b'heix', b'hevc', b'hevx', b'mif1', b'msf1']
            if brand in heic_brands:
                return "image/heic"
    
    # If we get here, file type is not supported
    raise ValidationError(
        "Unsupported file type. Please upload a JPG, PNG, or HEIC image."
    )


def validate_file_size(content: bytes, max_size: int = MAX_FILE_SIZE) -> int:
    """
    Validate file size.
    
    Args:
        content: File content as bytes
        max_size: Maximum allowed size in bytes (default 10MB)
        
    Returns:
        File size in bytes
        
    Raises:
        ValidationError: If file exceeds max size
    """
    size = len(content)
    
    if size > max_size:
        max_mb = max_size / (1024 * 1024)
        actual_mb = size / (1024 * 1024)
        raise ValidationError(
            f"File too large ({actual_mb:.1f}MB). Maximum size is {max_mb:.0f}MB."
        )
    
    if size == 0:
        raise ValidationError("File is empty.")
    
    return size


def get_file_extension(mime_type: str) -> str:
    """
    Get file extension for a MIME type.
    
    Args:
        mime_type: MIME type string
        
    Returns:
        File extension including dot (e.g., ".jpg")
    """
    extensions = {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/heic": ".heic",
    }
    return extensions.get(mime_type, ".bin")