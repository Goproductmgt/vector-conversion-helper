"""
Image Processing Service
Handles preprocessing of uploaded images before vectorization.

Pipeline:
1. Normalize input (HEIC → PNG, resize if needed)
2. Optionally remove background (disabled by default)
3. Save preprocessed image ready for VTracer

Usage:
    from services.image_processing import ImageProcessingService
    
    service = ImageProcessingService()
    result = service.preprocess("/path/to/input.jpg", "/path/to/output_dir")
"""

import io
from pathlib import Path
from PIL import Image

# HEIC support
try:
    import pillow_heif
    pillow_heif.register_heif_opener()
    HEIC_SUPPORTED = True
except ImportError:
    HEIC_SUPPORTED = False

# Background removal - lazy loaded to avoid slow startup
REMBG_AVAILABLE = None
_remove_background = None

def get_remove_background():
    """Lazy load rembg to avoid slow startup."""
    global REMBG_AVAILABLE, _remove_background
    if REMBG_AVAILABLE is None:
        try:
            from rembg import remove as remove_bg
            _remove_background = remove_bg
            REMBG_AVAILABLE = True
        except ImportError:
            REMBG_AVAILABLE = False
    return _remove_background if REMBG_AVAILABLE else None

from utils.errors import ProcessingError


class ImageProcessingService:
    """
    Preprocesses images for vectorization.
    
    Configuration:
    - MAX_DIMENSION: Images larger than this are resized (preserves aspect ratio)
    - REMOVE_BACKGROUND: Whether to attempt background removal (default: False)
    """
    
    MAX_DIMENSION = 2000  # Max width or height in pixels
    REMOVE_BACKGROUND = False  # Disabled by default - can harm gradient images
    
    def __init__(self):
        """Initialize service and check dependencies."""
        if not HEIC_SUPPORTED:
            print("Warning: HEIC support not available. Install pillow-heif.")
    
    def preprocess(self, input_path: str, output_dir: str, job_id: str = "temp", remove_background: bool = None) -> dict:
        """
        Full preprocessing pipeline for an uploaded image.
        
        Args:
            input_path: Path to uploaded image (JPG, PNG, or HEIC)
            output_dir: Directory to save processed files
            job_id: Unique identifier for this job (used in filenames)
            remove_background: Override default background removal setting
            
        Returns:
            Dictionary with paths and metadata:
            {
                "normalized_path": "/path/to/normalized.png",
                "preprocessed_path": "/path/to/preprocessed.png",
                "original_format": "jpg",
                "original_size": (800, 600),
                "background_removed": True/False
            }
            
        Raises:
            ProcessingError: If processing fails
        """
        input_path = Path(input_path)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Use parameter if provided, otherwise use class default
        should_remove_bg = remove_background if remove_background is not None else self.REMOVE_BACKGROUND
        
        result = {
            "original_format": input_path.suffix.lower().strip("."),
            "background_removed": False,
        }
        
        # Step 1: Load image
        try:
            img = Image.open(input_path)
            result["original_size"] = img.size
        except Exception as e:
            raise ProcessingError(f"Failed to open image: {e}")
        
        # Step 2: Convert to RGB (handle HEIC, RGBA, etc.)
        img = self._normalize_format(img)
        
        # Strip EXIF metadata by copying pixel data only
        img_data = list(img.getdata())
        img_clean = Image.new(img.mode, img.size)
        img_clean.putdata(img_data)
        img = img_clean
        
        # Step 3: Resize if too large
        img = self._resize_if_needed(img)
        
        # Save normalized version
        normalized_path = output_dir / f"{job_id}_normalized.png"
        img.save(normalized_path, format="PNG")
        result["normalized_path"] = str(normalized_path)
        
        # Step 4: Optionally remove background
        if should_remove_bg:
            try:
                processed_img = self._remove_background(img)
                if processed_img is not img:
                    img = processed_img
                    result["background_removed"] = True
            except Exception as e:
                print(f"Warning: Background removal failed: {e}")
        
        # Step 5: Save preprocessed version (NO B/W conversion - VTracer handles color)
        preprocessed_path = output_dir / f"{job_id}_preprocessed.png"
        img.save(preprocessed_path, format="PNG")
        result["preprocessed_path"] = str(preprocessed_path)
        
        return result
    
    def _normalize_format(self, img: Image.Image) -> Image.Image:
        """Convert image to RGB format, handling transparency."""
        if img.mode in ("RGBA", "LA", "P"):
            # Handle transparency - composite on white background
            background = Image.new("RGB", img.size, (255, 255, 255))
            if img.mode == "P":
                img = img.convert("RGBA")
            if img.mode in ("RGBA", "LA"):
                background.paste(img, mask=img.split()[-1])
            else:
                background.paste(img)
            return background
        elif img.mode != "RGB":
            return img.convert("RGB")
        return img
    
    def _resize_if_needed(self, img: Image.Image) -> Image.Image:
        """
        Resize image if either dimension exceeds MAX_DIMENSION.
        Preserves aspect ratio.
        """
        width, height = img.size
        
        if width <= self.MAX_DIMENSION and height <= self.MAX_DIMENSION:
            return img
        
        if width > height:
            new_width = self.MAX_DIMENSION
            new_height = int(height * (self.MAX_DIMENSION / width))
        else:
            new_height = self.MAX_DIMENSION
            new_width = int(width * (self.MAX_DIMENSION / height))
        
        return img.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    def _remove_background(self, img: Image.Image) -> Image.Image:
        """
        Remove background using rembg (U-2-Net model).
        Returns image with transparent background converted to white.
        """
        remove_bg_func = get_remove_background()
        if remove_bg_func is None:
            return img
        
        img_bytes = io.BytesIO()
        img.save(img_bytes, format="PNG")
        img_bytes.seek(0)
        
        output_bytes = remove_bg_func(img_bytes.read())
        result = Image.open(io.BytesIO(output_bytes))
        
        if result.mode == "RGBA":
            background = Image.new("RGB", result.size, (255, 255, 255))
            background.paste(result, mask=result.split()[3])
            return background
        
        return result.convert("RGB")
    
    def normalize_only(self, input_path: str, output_path: str) -> str:
        """
        Just normalize an image without full preprocessing.
        Useful for keeping original quality in storage.
        """
        input_path = Path(input_path)
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        img = Image.open(input_path)
        img = self._normalize_format(img)
        img = self._resize_if_needed(img)
        img.save(output_path, format="PNG")
        return str(output_path)