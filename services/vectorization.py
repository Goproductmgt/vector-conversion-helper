"""
Vectorization Service
Wraps Potrace CLI to convert raster images to vector formats (SVG, EPS, PDF).

Potrace converts bitmap images to scalable vector graphics.
Works best for logos, icons, and graphics with clear edges.

Usage:
    from services.vectorization import VectorizationService
    
    service = VectorizationService()
    results = service.vectorize("/path/to/preprocessed.png", "/path/to/output_dir")
"""

import subprocess
import shutil
from pathlib import Path
from PIL import Image
import cairosvg

from utils.errors import VectorizationError


class VectorizationService:
    """
    Converts raster images to vector formats using Potrace CLI.
    
    Potrace features:
    - Fast and reliable vectorization
    - Available as a system package (no compilation needed)
    - High quality output for logos and graphics
    """
    
    def __init__(self):
        """Initialize and verify Potrace is available."""
        self.potrace_path = shutil.which("potrace")
        if not self.potrace_path:
            raise VectorizationError(
                "Potrace CLI not found. Please install it via the system package manager."
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
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        bmp_path = output_dir / "temp_input.bmp"
        self._convert_to_bmp(input_path, bmp_path)
        
        try:
            svg_path = output_dir / "output.svg"
            self._run_potrace(bmp_path, svg_path, "svg")
            
            eps_path = output_dir / "output.eps"
            pdf_path = output_dir / "output.pdf"
            
            self._convert_svg_to_eps(svg_path, eps_path)
            self._convert_svg_to_pdf(svg_path, pdf_path)
            
            return {
                "svg": str(svg_path),
                "eps": str(eps_path),
                "pdf": str(pdf_path),
            }
        finally:
            if bmp_path.exists():
                bmp_path.unlink()
    
    def _convert_to_bmp(self, input_path: Path, bmp_path: Path) -> None:
        """
        Convert input image to BMP format for Potrace.
        Converts to grayscale and applies threshold for better vectorization.
        """
        try:
            with Image.open(input_path) as img:
                if img.mode == 'RGBA':
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    background.paste(img, mask=img.split()[3])
                    img = background
                elif img.mode != 'RGB':
                    img = img.convert('RGB')
                
                gray = img.convert('L')
                bw = gray.point(lambda x: 0 if x < 128 else 255, '1')
                bw.save(bmp_path, 'BMP')
                
        except Exception as e:
            raise VectorizationError(f"Failed to convert image to BMP: {e}")
    
    def _run_potrace(self, input_path: Path, output_path: Path, fmt: str) -> None:
        """
        Run Potrace CLI to generate vector output.
        
        Args:
            input_path: Path to input BMP file
            output_path: Path for output file
            fmt: Output format (svg, eps, pdf)
        """
        format_flags = {
            "svg": ["-s"],
            "eps": ["-e"],
            "pdf": ["-b", "pdf"],
        }
        
        cmd = [
            self.potrace_path,
            str(input_path),
            "-o", str(output_path),
            "--turdsize", "2",
            "--alphamax", "1",
            "--opttolerance", "0.2",
        ] + format_flags.get(fmt, ["-s"])
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
            )
            
            if result.returncode != 0:
                raise VectorizationError(
                    f"Potrace failed: {result.stderr}"
                )
            
            if not output_path.exists():
                raise VectorizationError(
                    f"Potrace completed but {fmt.upper()} file was not created"
                )
                
        except subprocess.TimeoutExpired:
            raise VectorizationError(
                "Potrace timed out while generating vector output"
            )
        except FileNotFoundError:
            raise VectorizationError(
                f"Potrace CLI not found at {self.potrace_path}"
            )
    
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
    
    def vectorize_single(self, input_path: str, output_path: str, fmt: str) -> str:
        """
        Convert to a single format.
        
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
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        bmp_path = output_path.parent / "temp_input.bmp"
        self._convert_to_bmp(input_path, bmp_path)
        
        try:
            if fmt == "svg":
                self._run_potrace(bmp_path, output_path, "svg")
            else:
                svg_path = output_path.parent / "temp_output.svg"
                self._run_potrace(bmp_path, svg_path, "svg")
                
                try:
                    if fmt == "eps":
                        self._convert_svg_to_eps(svg_path, output_path)
                    elif fmt == "pdf":
                        self._convert_svg_to_pdf(svg_path, output_path)
                finally:
                    if svg_path.exists():
                        svg_path.unlink()
        finally:
            if bmp_path.exists():
                bmp_path.unlink()
        
        return str(output_path)
