"""
Image Processing Service
Handles preprocessing of uploaded images before vectorization.

Pipeline:
1. Normalize input (HEIC → PNG, resize if needed)
2. Remove background (rembg)
3. Save preprocessed image with colors preserved for VTracer

Usage:
    from services.image_processing import ImageProcessingService
    
    service = ImageProcessingService()
    preprocessed_path = service.preprocess("/path/to/input.jpg", "/path/to/output_dir")
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
REMBG_AVAILABLE = None  # None = not checked yet, True/False after first use
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
    - THRESHOLD: Grayscale value for black/white cutoff (0-255)
    """
    
    MAX_DIMENSION = 2000  # Max width or height in pixels
    THRESHOLD = 128       # Values below this become black, above become white
    
    def __init__(self):
        """Initialize service and check dependencies."""
        if not HEIC_SUPPORTED:
            print("Warning: HEIC support not available. Install pillow-heif.")
        if not REMBG_AVAILABLE:
            print("Warning: rembg not available. Background removal disabled.")
    
    def preprocess(self, input_path: str, output_dir: str, job_id: str = "temp") -> dict:
        """
        Full preprocessing pipeline for an uploaded image.
        
        Args:
            input_path: Path to uploaded image (JPG, PNG, or HEIC)
            output_dir: Directory to save processed files
            job_id: Unique identifier for this job (used in filenames)
            
        Returns:
            Dictionary with paths and metadata:
            {
                "normalized_path": "/path/to/normalized.png",
                "preprocessed_path": "/path/to/preprocessed.png",
                "original_format": "jpg",
                "original_size": (800, 600),
                "background_removed": True
            }
            
        Raises:
            ProcessingError: If processing fails
        """
        input_path = Path(input_path)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        result = {
            "original_format": input_path.suffix.lower().strip("."),
            "background_removed": False,
        }
        
        # Step 1: Load and normalize
        try:
            img = Image.open(input_path)
            result["original_size"] = img.size
        except Exception as e:
            raise ProcessingError(f"Failed to open image: {e}")
        
        # Convert HEIC/other formats to RGB
        if img.mode in ("RGBA", "LA", "P"):
            # Handle transparency - composite on white background
            background = Image.new("RGB", img.size, (255, 255, 255))
            if img.mode == "P":
                img = img.convert("RGBA")
            background.paste(img, mask=img.split()[-1] if img.mode == "RGBA" else None)
            img = background
        elif img.mode != "RGB":
            img = img.convert("RGB")
        
        # Strip EXIF metadata by copying pixel data only
        img_data = list(img.getdata())
        img_clean = Image.new(img.mode, img.size)
        img_clean.putdata(img_data)
        img = img_clean
        
        # Step 2: Resize if too large
        img = self._resize_if_needed(img)
        
        # Save normalized version
        normalized_path = output_dir / f"{job_id}_normalized.png"
        img.save(normalized_path, format="PNG")
        result["normalized_path"] = str(normalized_path)
        
        # Step 3: Remove background (if available)
        try:
            processed_img = self._remove_background(img)
            if processed_img is not img:  # Only update if background was actually removed
                img = processed_img
                result["background_removed"] = True
        except Exception as e:
            # Background removal failed - continue without it
            print(f"Warning: Background removal failed: {e}")
        
        # Note: VTracer supports full color - no B&W conversion needed
        # Colors are preserved for vectorization
        
        # Save preprocessed version (ready for vectorization)
        preprocessed_path = output_dir / f"{job_id}_preprocessed.png"
        img.save(preprocessed_path, format="PNG")
        result["preprocessed_path"] = str(preprocessed_path)
        
        return result
    
    def _resize_if_needed(self, img: Image.Image) -> Image.Image:
        """
        Resize image if either dimension exceeds MAX_DIMENSION.
        Preserves aspect ratio.
        """
        width, height = img.size
        
        if width <= self.MAX_DIMENSION and height <= self.MAX_DIMENSION:
            return img
        
        # Calculate new size preserving aspect ratio
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
        
        # Convert PIL Image to bytes for rembg
        img_bytes = io.BytesIO()
        img.save(img_bytes, format="PNG")
        img_bytes.seek(0)
        
        # Remove background
        output_bytes = remove_bg_func(img_bytes.read())
        
        # Convert back to PIL Image
        result = Image.open(io.BytesIO(output_bytes))
        
        # Convert transparency to white background
        if result.mode == "RGBA":
            background = Image.new("RGB", result.size, (255, 255, 255))
            background.paste(result, mask=result.split()[3])
            return background
        
        return result.convert("RGB")
    
    def _convert_to_bw(self, img: Image.Image) -> Image.Image:
        """
        Convert image to high-contrast black and white.
        
        Process:
        1. Convert to grayscale
        2. Apply threshold - pixels become pure black or pure white
        """
        # Convert to grayscale
        gray = img.convert("L")
        
        # Apply threshold
        bw = gray.point(lambda x: 255 if x > self.THRESHOLD else 0, mode="1")
        
        # Convert back to grayscale (for PNG saving compatibility)
        return bw.convert("L")
    
    def normalize_only(self, input_path: str, output_path: str) -> str:
        """
        Just normalize an image without full preprocessing.
        Useful for keeping original quality in storage.
        
        Args:
            input_path: Path to input image
            output_path: Path for normalized output
            
        Returns:
            Path to normalized image
        """
        input_path = Path(input_path)
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        img = Image.open(input_path)
        
        # Convert to RGB if needed
        if img.mode in ("RGBA", "LA", "P"):
            background = Image.new("RGB", img.size, (255, 255, 255))
            if img.mode == "P":
                img = img.convert("RGBA")
            background.paste(img, mask=img.split()[-1] if img.mode == "RGBA" else None)
            img = background
        elif img.mode != "RGB":
            img = img.convert("RGB")
        
        # Resize if needed
        img = self._resize_if_needed(img)
        
        # Save as PNG
        img.save(output_path, format="PNG")
        return str(output_path)