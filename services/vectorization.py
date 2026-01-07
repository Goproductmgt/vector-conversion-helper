"""
Vectorization Service
Uses VTracer Python bindings for full-color raster-to-vector conversion.

Quality settings optimized for print shop output.
"""
from pathlib import Path
import vtracer
import cairosvg
from utils.errors import VectorizationError


class VectorizationService:
    """
    Converts raster images to vector formats using VTracer Python bindings.
    
    Tuned for high-quality output suitable for professional printing.
    """
    
    def __init__(self):
        pass
    
    def vectorize(self, input_path: str, output_dir: str) -> dict[str, str]:
        input_path = Path(input_path)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        svg_path = output_dir / "output.svg"
        self._run_vtracer(input_path, svg_path)
        
        eps_path = output_dir / "output.eps"
        pdf_path = output_dir / "output.pdf"
        
        self._convert_svg_to_eps(svg_path, eps_path)
        self._convert_svg_to_pdf(svg_path, pdf_path)
        
        return {"svg": str(svg_path), "eps": str(eps_path), "pdf": str(pdf_path)}
    
    def _run_vtracer(self, input_path: Path, output_path: Path) -> None:
        """
        VTracer with HIGH-QUALITY settings for print shop output.
        
        Settings explained:
        - colormode='color': Full color preservation (not binary B/W)
        - hierarchical='stacked': Layer colors on top of each other (better for gradients)
        - mode='spline': Smooth bezier curves (not jagged polygons)
        - filter_speckle=1: Keep almost all details (only remove 1px noise)
        - color_precision=8: Maximum color fidelity (1-8 scale)
        - corner_threshold=120: Smoother curves, fewer sharp corners
        - length_threshold=4.0: Keep shorter path segments for detail
        - splice_threshold=90: Smoother curve connections
        """
        try:
            vtracer.convert_image_to_svg_py(
                image_path=str(input_path),
                out_path=str(output_path),
                colormode='color',
                hierarchical='stacked',
                mode='spline',
                filter_speckle=1,
                color_precision=8,
                corner_threshold=120,
                length_threshold=4.0,
                splice_threshold=90,
            )
        except Exception as e:
            raise VectorizationError(f"VTracer failed: {e}")
    
    def _convert_svg_to_eps(self, svg_path: Path, eps_path: Path) -> None:
        cairosvg.svg2ps(url=str(svg_path), write_to=str(eps_path))
    
    def _convert_svg_to_pdf(self, svg_path: Path, pdf_path: Path) -> None:
        cairosvg.svg2pdf(url=str(svg_path), write_to=str(pdf_path))