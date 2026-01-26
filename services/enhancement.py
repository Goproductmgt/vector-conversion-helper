"""
Enhancement Service
Uses Real-ESRGAN via Replicate API to upscale and clean images before vectorization.

This addresses VTracer's main limitation: quality degrades on low-resolution
or JPEG-compressed images. Real-ESRGAN provides:
- 4x upscaling (more pixels for VTracer to trace)
- JPEG artifact removal
- Edge sharpening

Usage:
    from services.enhancement import EnhancementService
    
    service = EnhancementService()
    result = service.enhance("/path/to/input.png", "/path/to/output_dir", "job123")
    # result = {"enhanced_path": "...", "scale": 4, "processing_time": 12.3}
"""

import time
from pathlib import Path
from typing import Optional

from config import get_settings
from utils.errors import ProcessingError


class EnhancementService:
    """
    Enhances images using Real-ESRGAN via Replicate API.
    
    Configuration (from config.py):
    - replicate_api_token: API authentication
    - replicate_model: Model to use (default: nightmareai/real-esrgan)
    - replicate_scale: Upscale factor 2, 3, or 4 (default: 4)
    - enhancement_timeout_seconds: Max wait time (default: 120)
    """
    
    def __init__(self):
        """Initialize service and validate configuration."""
        self.settings = get_settings()
        self._client = None
        
        if not self.settings.replicate_api_token:
            print("Warning: REPLICATE_API_TOKEN not set. Enhancement will fail.")
    
    @property
    def client(self):
        """Lazy load Replicate client to avoid import if not used."""
        if self._client is None:
            try:
                import replicate
                self._client = replicate
            except ImportError:
                raise ProcessingError(
                    "Replicate package not installed. Run: pip install replicate"
                )
        return self._client
    
    def enhance(
        self,
        input_path: str,
        output_dir: str,
        job_id: str,
        scale: Optional[int] = None
    ) -> dict:
        """
        Enhance an image using Real-ESRGAN.
        
        Args:
            input_path: Path to image file (PNG recommended)
            output_dir: Directory to save enhanced image
            job_id: Unique job identifier (used in filename)
            scale: Upscale factor (2, 3, or 4). Defaults to config setting.
            
        Returns:
            Dictionary with results:
            {
                "enhanced_path": "/path/to/enhanced.png",
                "original_path": "/path/to/input.png",
                "scale": 4,
                "processing_time_seconds": 12.3
            }
            
        Raises:
            ProcessingError: If enhancement fails
        """
        start_time = time.time()
        
        input_path = Path(input_path)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Validate input exists
        if not input_path.exists():
            raise ProcessingError(f"Input file not found: {input_path}")
        
        # Use provided scale or fall back to config
        scale = scale or self.settings.replicate_scale
        if scale not in (2, 3, 4):
            raise ProcessingError(f"Invalid scale {scale}. Must be 2, 3, or 4.")
        
        # Check API token
        if not self.settings.replicate_api_token:
            raise ProcessingError(
                "REPLICATE_API_TOKEN not configured. "
                "Add it to .env (local) or Replit Secrets (production)."
            )
        
        try:
            # Call Replicate API
            enhanced_url = self._call_replicate(input_path, scale)
            
            # Download the enhanced image
            enhanced_path = output_dir / f"{job_id}_enhanced.png"
            self._download_result(enhanced_url, enhanced_path)
            
            processing_time = round(time.time() - start_time, 2)
            
            return {
                "enhanced_path": str(enhanced_path),
                "original_path": str(input_path),
                "scale": scale,
                "processing_time_seconds": processing_time,
            }
            
        except ProcessingError:
            raise
        except Exception as e:
            raise ProcessingError(f"Enhancement failed: {str(e)}")
    
    def _call_replicate(self, input_path: Path, scale: int) -> str:
        """
        Call Replicate API with the image.
        
        Returns:
            URL of the enhanced image
        """
        import os
        
        # Set API token for replicate library
        os.environ["REPLICATE_API_TOKEN"] = self.settings.replicate_api_token
        
        try:
            # Open file and send to Replicate
            with open(input_path, "rb") as f:
                output = self.client.run(
                    self.settings.replicate_model,
                    input={
                        "image": f,
                        "scale": scale,
                        "face_enhance": False,  # Not needed for logos/graphics
                    }
                )
            
            # Output is typically a URL string or FileOutput object
            if hasattr(output, 'url'):
                return output.url
            elif isinstance(output, str):
                return output
            else:
                # Some models return the URL directly
                return str(output)
                
        except Exception as e:
            error_msg = str(e).lower()
            
            if "authentication" in error_msg or "unauthorized" in error_msg:
                raise ProcessingError(
                    "Replicate API authentication failed. Check your API token."
                )
            elif "rate limit" in error_msg:
                raise ProcessingError(
                    "Replicate rate limit exceeded. Please try again later."
                )
            elif "timeout" in error_msg:
                raise ProcessingError(
                    "Enhancement timed out. The image may be too large."
                )
            else:
                raise ProcessingError(f"Replicate API error: {str(e)}")
    
    def _download_result(self, url: str, output_path: Path) -> None:
        """Download enhanced image from Replicate's CDN."""
        import requests
        
        try:
            response = requests.get(url, timeout=60)
            response.raise_for_status()
            
            with open(output_path, "wb") as f:
                f.write(response.content)
                
        except requests.RequestException as e:
            raise ProcessingError(f"Failed to download enhanced image: {str(e)}")
    
    def is_available(self) -> bool:
        """Check if enhancement service is properly configured."""
        return bool(self.settings.replicate_api_token)