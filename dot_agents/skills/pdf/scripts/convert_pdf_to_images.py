# /// script
# requires-python = ">=3.11"
# dependencies = ["pymupdf"]
# ///

import os
import sys

import fitz  # pymupdf


def convert(pdf_path, output_dir, zoom=1.5):
    """Render each page of a PDF to a PNG image.

    Args:
        pdf_path: Path to the input PDF.
        output_dir: Directory where page images will be saved (created if needed).
        zoom: Render scale factor. 1.5 ≈ 108 DPI, 2.0 ≈ 144 DPI, 3.0 ≈ 216 DPI.
    """
    os.makedirs(output_dir, exist_ok=True)
    doc = fitz.open(pdf_path)
    mat = fitz.Matrix(zoom, zoom)

    for i, page in enumerate(doc):
        pix = page.get_pixmap(matrix=mat)
        image_path = os.path.join(output_dir, f"page_{i + 1:02d}.png")
        pix.save(image_path)
        print(f"Saved page {i + 1} as {image_path} ({pix.width}x{pix.height})")

    print(f"Converted {len(doc)} pages to PNG images")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(
            "Usage: uv run convert_pdf_to_images.py <input.pdf> <output_directory> [zoom]"
        )
        print(
            "  zoom: render scale factor (default 1.5). Use 2.0 for higher resolution."
        )
        sys.exit(1)
    pdf_path = sys.argv[1]
    output_directory = sys.argv[2]
    zoom = float(sys.argv[3]) if len(sys.argv) > 3 else 1.5
    convert(pdf_path, output_directory, zoom)
