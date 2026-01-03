"""
Test script to verify the vectorization pipeline works.
Run with: python test_vectorization.py
"""

import subprocess
import tempfile
from pathlib import Path
from PIL import Image
import requests

# Create a simple test image (black circle on white background)
def create_test_image() -> Path:
    """Create a simple test image for vectorization."""
    img = Image.new("RGB", (200, 200), "white")
    
    # Draw a simple black shape (filled rectangle as a logo placeholder)
    from PIL import ImageDraw
    draw = ImageDraw.Draw(img)
    draw.ellipse([40, 40, 160, 160], fill="black")
    draw.rectangle([80, 100, 120, 180], fill="black")  # Stem
    
    # Save to temp file
    temp_path = Path(tempfile.gettempdir()) / "test_input.png"
    img.save(temp_path)
    print(f"✓ Created test image: {temp_path}")
    return temp_path


def convert_to_bitmap(input_path: Path) -> Path:
    """Convert image to PBM (bitmap) format for Potrace."""
    img = Image.open(input_path)
    
    # Convert to grayscale
    img = img.convert("L")
    
    # Apply threshold (convert to pure black and white)
    threshold = 128
    img = img.point(lambda x: 255 if x > threshold else 0, mode="1")
    
    # Save as PBM (Potrace's required input format)
    pbm_path = input_path.with_suffix(".pbm")
    img.save(pbm_path)
    print(f"✓ Converted to bitmap: {pbm_path}")
    return pbm_path


def run_potrace(pbm_path: Path) -> dict[str, Path]:
    """Run Potrace to generate SVG, EPS, and PDF."""
    outputs = {}
    
    base = pbm_path.with_suffix("")
    
    # Generate SVG
    svg_path = base.with_suffix(".svg")
    result = subprocess.run(
        ["potrace", str(pbm_path), "-s", "-o", str(svg_path)],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        outputs["svg"] = svg_path
        print(f"✓ Generated SVG: {svg_path}")
    else:
        print(f"✗ SVG failed: {result.stderr}")
    
    # Generate EPS
    eps_path = base.with_suffix(".eps")
    result = subprocess.run(
        ["potrace", str(pbm_path), "-e", "-o", str(eps_path)],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        outputs["eps"] = eps_path
        print(f"✓ Generated EPS: {eps_path}")
    else:
        print(f"✗ EPS failed: {result.stderr}")
    
    # Generate PDF
    pdf_path = base.with_suffix(".pdf")
    result = subprocess.run(
        ["potrace", str(pbm_path), "-b", "pdf", "-o", str(pdf_path)],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        outputs["pdf"] = pdf_path
        print(f"✓ Generated PDF: {pdf_path}")
    else:
        print(f"✗ PDF failed: {result.stderr}")
    
    return outputs


def show_svg_preview(svg_path: Path):
    """Show first few lines of SVG to verify it's valid."""
    content = svg_path.read_text()
    lines = content.split("\n")[:10]
    print("\n--- SVG Preview (first 10 lines) ---")
    for line in lines:
        print(line)
    print("---")
    print(f"\nTotal SVG size: {len(content)} bytes")


if __name__ == "__main__":
    print("\n=== Vector Conversion Pipeline Test ===\n")
    
    # Step 1: Create test image
    input_path = create_test_image()
    
    # Step 2: Convert to bitmap
    pbm_path = convert_to_bitmap(input_path)
    
    # Step 3: Run Potrace
    outputs = run_potrace(pbm_path)
    
    # Step 4: Verify outputs
    if outputs:
        print(f"\n✅ SUCCESS! Generated {len(outputs)} files")
        show_svg_preview(outputs["svg"])
        print(f"\nFiles are in: {pbm_path.parent}")
        print("You can open the SVG in a browser to see it!")
    else:
        print("\n❌ FAILED - no outputs generated")