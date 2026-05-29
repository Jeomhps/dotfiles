# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
Validate bounding boxes in a fields.json file.

Checks for:
- Overlapping label/entry boxes within the same field
- Overlapping boxes across different fields on the same page
- Entry boxes too short for the specified font size
"""

import json
import sys
from dataclasses import dataclass


@dataclass
class Box:
    rect: list[float]
    kind: str  # "label" or "entry"
    field_desc: str
    page: int


def rects_overlap(a: list[float], b: list[float]) -> bool:
    # Each rect is [x0, y0, x1, y1]
    return not (a[2] <= b[0] or b[2] <= a[0] or a[3] <= b[1] or b[3] <= a[1])


def validate(fields_json_path: str) -> list[str]:
    with open(fields_json_path) as f:
        data = json.load(f)

    fields = data.get("form_fields", [])
    messages = [f"Read {len(fields)} fields"]
    boxes: list[Box] = []

    for field in fields:
        page = field["page_number"]
        desc = field.get("description", "?")
        boxes.append(Box(field["label_bounding_box"], "label", desc, page))
        boxes.append(Box(field["entry_bounding_box"], "entry", desc, page))

    has_error = False

    # Check intersections
    for i, a in enumerate(boxes):
        for b in boxes[i + 1 :]:
            if a.page != b.page:
                continue
            if rects_overlap(a.rect, b.rect):
                has_error = True
                if a.field_desc == b.field_desc:
                    messages.append(
                        f"FAIL: label and entry boxes overlap for '{a.field_desc}' "
                        f"({a.rect} vs {b.rect})"
                    )
                else:
                    messages.append(
                        f"FAIL: {a.kind} box for '{a.field_desc}' overlaps "
                        f"{b.kind} box for '{b.field_desc}' "
                        f"({a.rect} vs {b.rect})"
                    )
                if len(messages) >= 22:
                    messages.append("Too many errors — fix these and re-run.")
                    return messages

    # Check entry boxes are tall enough for their font
    for field in fields:
        entry = field.get("entry_text", {})
        font_size = entry.get("font_size", 0)
        if font_size:
            box = field["entry_bounding_box"]
            height = box[3] - box[1]
            if height < font_size:
                has_error = True
                messages.append(
                    f"FAIL: entry box for '{field.get('description', '?')}' is too short "
                    f"(height={height:.1f}, font_size={font_size})"
                )

    if not has_error:
        messages.append("OK: all bounding boxes are valid")

    return messages


def main():
    if len(sys.argv) != 2:
        print("Usage: uv run check_bounding_boxes.py fields.json")
        sys.exit(1)

    for msg in validate(sys.argv[1]):
        print(msg)


if __name__ == "__main__":
    main()
