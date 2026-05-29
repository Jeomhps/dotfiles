# /// script
# requires-python = ">=3.11"
# dependencies = ["pdfplumber"]
# ///
"""
Extract structural elements from a non-fillable PDF:
  - text labels with exact coordinates
  - horizontal lines (row separators)
  - small square rectangles (checkboxes)
  - derived row boundaries

Output is a JSON file consumable by fill_pdf_form_with_annotations.py.

Usage: uv run extract_form_structure.py input.pdf structure.json
"""

import json
import sys

import pdfplumber


def extract(pdf_path: str) -> dict:
    result: dict = {
        "pages": [],
        "labels": [],
        "lines": [],
        "checkboxes": [],
        "row_boundaries": [],
    }

    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            result["pages"].append(
                {
                    "page_number": page_num,
                    "width": float(page.width),
                    "height": float(page.height),
                }
            )

            # Text words
            for word in page.extract_words():
                result["labels"].append(
                    {
                        "page": page_num,
                        "text": word["text"],
                        "x0": round(float(word["x0"]), 1),
                        "top": round(float(word["top"]), 1),
                        "x1": round(float(word["x1"]), 1),
                        "bottom": round(float(word["bottom"]), 1),
                    }
                )

            # Horizontal lines spanning more than half the page width
            for line in page.lines:
                width = float(line["x1"]) - float(line["x0"])
                if width > page.width * 0.5:
                    result["lines"].append(
                        {
                            "page": page_num,
                            "y": round(float(line["top"]), 1),
                            "x0": round(float(line["x0"]), 1),
                            "x1": round(float(line["x1"]), 1),
                        }
                    )

            # Small square rectangles → checkboxes (5–15 pt, roughly square)
            for rect in page.rects:
                w = float(rect["x1"]) - float(rect["x0"])
                h = float(rect["bottom"]) - float(rect["top"])
                if 5 <= w <= 15 and 5 <= h <= 15 and abs(w - h) < 2:
                    result["checkboxes"].append(
                        {
                            "page": page_num,
                            "x0": round(float(rect["x0"]), 1),
                            "top": round(float(rect["top"]), 1),
                            "x1": round(float(rect["x1"]), 1),
                            "bottom": round(float(rect["bottom"]), 1),
                            "center_x": round(
                                (float(rect["x0"]) + float(rect["x1"])) / 2, 1
                            ),
                            "center_y": round(
                                (float(rect["top"]) + float(rect["bottom"])) / 2, 1
                            ),
                        }
                    )

    # Derive row boundaries from horizontal lines, per page
    lines_by_page: dict[int, list[float]] = {}
    for line in result["lines"]:
        lines_by_page.setdefault(line["page"], []).append(line["y"])

    for page, ys in lines_by_page.items():
        ys = sorted(set(ys))
        for i in range(len(ys) - 1):
            result["row_boundaries"].append(
                {
                    "page": page,
                    "row_top": ys[i],
                    "row_bottom": ys[i + 1],
                    "row_height": round(ys[i + 1] - ys[i], 1),
                }
            )

    return result


def main():
    if len(sys.argv) != 3:
        print("Usage: uv run extract_form_structure.py input.pdf structure.json")
        sys.exit(1)

    data = extract(sys.argv[1])
    with open(sys.argv[2], "w") as f:
        json.dump(data, f, indent=2)

    print(
        f"Extracted {len(data['labels'])} labels, "
        f"{len(data['lines'])} lines, "
        f"{len(data['checkboxes'])} checkboxes across "
        f"{len(data['pages'])} page(s) → {sys.argv[2]}"
    )


if __name__ == "__main__":
    main()
