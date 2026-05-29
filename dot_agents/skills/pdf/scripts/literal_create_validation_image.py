# /// script
# requires-python = ">=3.11"
# dependencies = ["Pillow"]
# ///
"""
Draw bounding boxes from fields.json onto a rendered page image for visual verification.

Label bounding boxes are drawn in blue; entry bounding boxes in red.

Usage: uv run create_validation_image.py <page_number> fields.json page_image.png output.png
"""

import json
import sys

from PIL import Image, ImageDraw


def draw_boxes(page_number: int, fields_path: str, image_path: str, output_path: str):
    with open(fields_path) as f:
        data: dict = json.load(f)

    img = Image.open(image_path).convert("RGBA")
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    count = 0
    for field in data.get("form_fields", []):
        if field["page_number"] != page_number:
            continue

        label_box = field["label_bounding_box"]
        entry_box = field["entry_bounding_box"]

        # Blue for labels, red for entry areas (semi-transparent fill)
        draw.rectangle(label_box, outline=(0, 80, 200, 255), width=2)
        draw.rectangle(
            [label_box[0], label_box[1], label_box[2], label_box[3]],
            fill=(0, 80, 200, 30),
        )
        draw.rectangle(entry_box, outline=(200, 0, 0, 255), width=2)
        draw.rectangle(
            [entry_box[0], entry_box[1], entry_box[2], entry_box[3]],
            fill=(200, 0, 0, 30),
        )
        count += 2

    result = Image.alpha_composite(img, overlay).convert("RGB")
    result.save(output_path)
    print(f"Saved validation image with {count} boxes → {output_path}")
    print("Blue = label bounding box, Red = entry bounding box")


def main():
    if len(sys.argv) != 5:
        print(
            "Usage: uv run create_validation_image.py <page> fields.json input.png output.png"
        )
        sys.exit(1)

    draw_boxes(
        page_number=int(sys.argv[1]),
        fields_path=sys.argv[2],
        image_path=sys.argv[3],
        output_path=sys.argv[4],
    )


if __name__ == "__main__":
    main()
