"""
Vectorization Service
Uses VTracer Python bindings for full-color raster-to-vector conversion.

VTracer supports full-color vectorization directly in Python.

Usage:
    from services.vectorization import VectorizationService
    
    service = VectorizationService()
    results = service.vectorize("/path/to/preprocessed.png", "/path/to/output_dir")
"""

from pathlib import Path
import vtracer
import cairosvg

from utils.errors import VectorizationError


class VectorizationService:
    """
    Converts raster images to vector formats using VTracer Python bindings.
    
    VTracer features:
    - Full color support (preserves original colors)
    - Fast O(n) algorithm
    - High quality output
    """
    
    def __init__(self):
        """Initialize VectorizationService."""
        pass
    
    def vectorize(self, input_path: str, output_dir: str) -> dict[str, str]:
        """
        Convert a preprocessed image to SVG, EPS, and PDF formats.
        
        Args:
            input_path: Path to preprocessed image (PNG with or without background)
            output_dir: Directory to save output files
            
        Returns:
            Dictionary with paths to generated files:
            {"svg": "path/to/output.svg", "eps": "...", "pdf": "..."}
            
        Raises:
            VectorizationError: If conversion fails
        """
        input_path = Path(input_path)
        output_dir = Path(output_dir)
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        svg_path = output_dir / "output.svg"
        self._run_vtracer(input_path, svg_path)
        
        eps_path = output_dir / "output.eps"
        pdf_path = output_dir / "output.pdf"
        
        self._convert_svg_to_eps(svg_path, eps_path)
        self._convert_svg_to_pdf(svg_path, pdf_path)
        
        return {
            "svg": str(svg_path),
            "eps": str(eps_path),
            "pdf": str(pdf_path),
        }
    
    def _run_vtracer(self, input_path: Path, output_path: Path) -> None:
        """
        Run VTracer to generate SVG vector file.
        
        VTracer parameters optimized for quality and speed:
        - colormode='color': Full color output
        - hierarchical='stacked': Layer colors for better quality
        - mode='spline': Smooth curves
        - filter_speckle=4: Remove noise smaller than 4px
        - color_precision=6: Balance between quality and file size
        """
        try:
            vtracer.convert_image_to_svg_py(
                image_path=str(input_path),
                out_path=str(output_path),
                colormode='color',
                hierarchical='stacked',
                mode='spline',
                filter_speckle=4,
                color_precision=6,
                corner_threshold=60,
                segment_length=10,
                splice_threshold=45,
            )
            
            if not output_path.exists():
                raise VectorizationError(
                    "VTracer completed but SVG file was not created"
                )
                
        except Exception as e:
            raise VectorizationError(f"VTracer failed: {e}")
    
    def _convert_svg_to_eps(self, svg_path: Path, eps_path: Path) -> None:
        """Convert SVG to EPS format using cairosvg."""
        try:
            cairosvg.svg2ps(
                url=str(svg_path),
                write_to=str(eps_path),
            )
            
            if not eps_path.exists():
                raise VectorizationError("EPS file was not created")
                
        except Exception as e:
            raise VectorizationError(f"Failed to convert SVG to EPS: {e}")
    
    def _convert_svg_to_pdf(self, svg_path: Path, pdf_path: Path) -> None:
        """Convert SVG to PDF format using cairosvg."""
        try:
            cairosvg.svg2pdf(
                url=str(svg_path),
                write_to=str(pdf_path),
            )
            
            if not pdf_path.exists():
                raise VectorizationError("PDF file was not created")
                
        except Exception as e:
            raise VectorizationError(f"Failed to convert SVG to PDF: {e}")
