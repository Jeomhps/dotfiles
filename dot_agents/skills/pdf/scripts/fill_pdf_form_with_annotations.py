# /// script
# requires-python = ">=3.11"
# dependencies = ["pypdf"]
# ///
"""
Fill a non-fillable PDF by adding FreeText annotations from a fields.json file.

Supports two coordinate systems — auto-detected from fields.json:
  - pdf_width / pdf_height  → coordinates are already in PDF points
  - image_width / image_height → coordinates are image pixels, converted automatically

Usage: uv run fill_pdf_form_with_annotations.py input.pdf fields.json output.pdf
"""

import json
import sys

from pypdf import PdfReader, PdfWriter
from pypdf.annotations import FreeText


def image_to_pdf_coords(
    bbox: list[float],
    image_w: float,
    image_h: float,
    pdf_w: float,
    pdf_h: float,
) -> tuple[float, float, float, float]:
    """Convert image pixel bbox [x0,y0,x1,y1] to PDF points (left,bottom,right,top)."""
    x_scale = pdf_w / image_w
    y_scale = pdf_h / image_h
    left = bbox[0] * x_scale
    right = bbox[2] * x_scale
    top = pdf_h - bbox[1] * y_scale  # image y0 → pdf top
    bottom = pdf_h - bbox[3] * y_scale  # image y1 → pdf bottom
    return left, bottom, right, top


def pdf_to_pypdf_coords(
    bbox: list[float],
    pdf_h: float,
) -> tuple[float, float, float, float]:
    """Convert PDF-coordinate bbox [x0,y0,x1,y1] (y from top) to pypdf (y from bottom)."""
    left = bbox[0]
    right = bbox[2]
    top = pdf_h - bbox[1]
    bottom = pdf_h - bbox[3]
    return left, bottom, right, top


def fill(input_path: str, fields_path: str, output_path: str):
    with open(fields_path) as f:
        data: dict = json.load(f)

    reader = PdfReader(input_path)
    writer = PdfWriter()
    writer.append(reader)

    # Get actual PDF page dimensions
    pdf_dims: dict[int, tuple[float, float]] = {}
    for i, page in enumerate(reader.pages):
        mb = page.mediabox
        pdf_dims[i + 1] = (float(mb.width), float(mb.height))

    # Build page_info lookup
    page_info_map: dict[int, dict] = {p["page_number"]: p for p in data["pages"]}

    added = 0
    for field in data["form_fields"]:
        entry_text = field.get("entry_text", {})
        text = entry_text.get("text", "")
        if not text:
            continue

        page_num = field["page_number"]
        pdf_w, pdf_h = pdf_dims[page_num]
        page_info = page_info_map[page_num]
        bbox = field["entry_bounding_box"]

        if "pdf_width" in page_info:
            left, bottom, right, top = pdf_to_pypdf_coords(bbox, pdf_h)
        else:
            left, bottom, right, top = image_to_pdf_coords(
                bbox,
                float(page_info["image_width"]),
                float(page_info["image_height"]),
                pdf_w,
                pdf_h,
            )

        font_size = str(entry_text.get("font_size", 12)) + "pt"
        font_color = entry_text.get("font_color", "000000")
        font_name = entry_text.get("font", "Arial")

        annotation = FreeText(
            text=text,
            rect=(left, bottom, right, top),
            font=font_name,
            bold=entry_text.get("bold", False),
            italic=entry_text.get("italic", False),
            font_size=font_size,
            font_color=font_color,
            border_color=entry_text.get("border_color", None),
            background_color=entry_text.get("background_color", None),
        )
        writer.add_annotation(page_number=page_num - 1, annotation=annotation)
        added += 1

    with open(output_path, "wb") as f:
        writer.write(f)

    print(f"Added {added} annotation(s) → {output_path}")


def main():
    if len(sys.argv) != 4:
        print(
            "Usage: uv run fill_pdf_form_with_annotations.py input.pdf fields.json output.pdf"
        )
        sys.exit(1)
    fill(sys.argv[1], sys.argv[2], sys.argv[3])


if __name__ == "__main__":
    main()
