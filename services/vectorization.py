"""
Vectorization Service
Wraps VTracer CLI to convert raster images to vector formats (SVG, EPS, PDF).

VTracer supports full-color vectorization and accepts PNG/JPG directly.
No intermediate format conversion needed.

Usage:
    from services.vectorization import VectorizationService
    
    service = VectorizationService()
    results = service.vectorize("/path/to/preprocessed.png", "/path/to/output_dir")
    # results = {"svg": "/path/to/output.svg", "eps": "/path/to/output.eps", "pdf": "/path/to/output.pdf"}
"""

import subprocess
import shutil
from pathlib import Path
import cairosvg

from utils.errors import VectorizationError


class VectorizationService:
    """
    Converts raster images to vector formats using VTracer CLI.
    
    VTracer features:
    - Full color support (preserves original colors)
    - No preprocessing required (accepts PNG/JPG directly)
    - Fast O(n) algorithm
    - High quality output
    """
    
    def __init__(self):
        """Initialize and verify VTracer is available."""
        self._verify_vtracer_installed()
    
    def _verify_vtracer_installed(self) -> None:
        """Check that VTracer CLI is available on the system."""
        if not shutil.which("vtracer"):
            raise VectorizationError(
                "VTracer CLI not found. Install with: cargo install vtracer"
            )
    
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
        
        # Ensure output directory exists
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Step 1: Generate SVG using VTracer
        svg_path = output_dir / "output.svg"
        self._run_vtracer(input_path, svg_path)
        
        # Step 2: Convert SVG to EPS and PDF
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
        Run VTracer CLI to generate SVG vector file.
        
        VTracer parameters:
        --colormode color: Full color output (default, preserves colors)
        --hierarchical stacked: Layer colors for better quality
        --mode spline: Smooth curves (better than polygon mode)
        --filter_speckle 4: Remove noise smaller than 4px
        --color_precision 6: Balance between quality and file size
        --corner_threshold 60: Smooth corners (good for logos/graphics)
        --segment_length 10: Curve smoothness
        --splice_threshold 45: Join nearby segments
        
        Args:
            input_path: Path to input image (PNG/JPG)
            output_path: Path for output SVG file
        """
        cmd = [
            "vtracer",
            "--input", str(input_path),
            "--output", str(output_path),
            "--colormode", "color",
            "--hierarchical", "stacked",
            "--mode", "spline",
            "--filter_speckle", "4",
            "--color_precision", "6",
            "--corner_threshold", "60",
            "--segment_length", "10",
            "--splice_threshold", "45",
        ]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,  # 30 second timeout
            )
            
            if result.returncode != 0:
                raise VectorizationError(
                    f"VTracer failed: {result.stderr}"
                )
            
            # Verify output file was created
            if not output_path.exists():
                raise VectorizationError(
                    "VTracer completed but SVG file was not created"
                )
                
        except subprocess.TimeoutExpired:
            raise VectorizationError(
                "VTracer timed out while generating SVG"
            )
        except FileNotFoundError:
            raise VectorizationError(
                "VTracer CLI not found. Is it installed? Run: cargo install vtracer"
            )
    
    def _convert_svg_to_eps(self, svg_path: Path, eps_path: Path) -> None:
        """
        Convert SVG to EPS format using cairosvg.
        
        Args:
            svg_path: Path to input SVG file
            eps_path: Path for output EPS file
        """
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
        """
        Convert SVG to PDF format using cairosvg.
        
        Args:
            svg_path: Path to input SVG file
            pdf_path: Path for output PDF file
        """
        try:
            cairosvg.svg2pdf(
                url=str(svg_path),
                write_to=str(pdf_path),
            )
            
            if not pdf_path.exists():
                raise VectorizationError("PDF file was not created")
                
        except Exception as e:
            raise VectorizationError(f"Failed to convert SVG to PDF: {e}")
    
    def vectorize_single(self, input_path: str, output_path: str, fmt: str) -> str:
        """
        Convert to a single format (useful for testing).
        
        Args:
            input_path: Path to preprocessed image
            output_path: Path for output file
            fmt: Output format (svg, eps, or pdf)
            
        Returns:
            Path to generated file
        """
        valid_formats = ["svg", "eps", "pdf"]
        if fmt not in valid_formats:
            raise VectorizationError(f"Unsupported format: {fmt}. Use: {valid_formats}")
        
        input_path = Path(input_path)
        output_path = Path(output_path)
        
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        if fmt == "svg":
            # Direct SVG generation
            self._run_vtracer(input_path, output_path)
        else:
            # Generate SVG first, then convert
            svg_path = output_path.parent / "temp_output.svg"
            self._run_vtracer(input_path, svg_path)
            
            try:
                if fmt == "eps":
                    self._convert_svg_to_eps(svg_path, output_path)
                elif fmt == "pdf":
                    self._convert_svg_to_pdf(svg_path, output_path)
            finally:
                # Clean up temporary SVG
                if svg_path.exists():
                    svg_path.unlink()
        
        return str(output_path)