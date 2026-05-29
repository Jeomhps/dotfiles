# /// script
# requires-python = ">=3.11"
# dependencies = ["pypdf"]
# ///
"""
Fill a PDF's native form fields from a JSON values file.

Usage: uv run fill_fillable_fields.py input.pdf field_values.json output.pdf

field_values.json format:
[
  { "field_id": "last_name", "page": 1, "value": "Stoll" },
  { "field_id": "agree_cb",  "page": 1, "value": "/On"  }
]
"""

import json
import sys

from pypdf import PdfReader, PdfWriter


def load_existing_fields(reader: PdfReader) -> dict[str, dict]:
    """Return a flat map of field_id → field info including page number."""
    raw = reader.get_fields() or {}
    result: dict[str, dict] = {}

    for page_idx, page in enumerate(reader.pages):
        for ann in page.get("/Annots") or []:
            fid = _full_id(ann)
            if fid and fid in raw:
                entry = dict(raw[fid])
                entry["page"] = page_idx + 1
                result[fid] = entry

    return result


def _full_id(annotation) -> str | None:
    parts = []
    node = annotation
    while node:
        name = node.get("/T")
        if name:
            parts.append(str(name))
        node = node.get("/Parent")
    return ".".join(reversed(parts)) if parts else None


def validate_value(field_info: dict, value: str) -> str | None:
    ft = str(field_info.get("/FT", ""))
    fid = field_info.get("field_id", "?")

    if ft == "/Btn":
        states = field_info.get("/_States_", ["/On", "/Off"])
        if value not in states:
            return (
                f"'{value}' is not a valid state for checkbox '{fid}'. Valid: {states}"
            )
    elif ft == "/Ch":
        states = field_info.get("/_States_", [])
        valid = [s[0] if isinstance(s, list) else s for s in states]
        if value not in valid:
            return f"'{value}' is not a valid choice for '{fid}'. Valid: {valid}"
    return None


def fill(input_path: str, values_path: str, output_path: str):
    with open(values_path) as f:
        values: list[dict] = json.load(f)

    reader = PdfReader(input_path)
    existing = load_existing_fields(reader)

    # Validate
    has_error = False
    updates: dict[int, dict[str, str]] = {}  # page → {field_id: value}

    for entry in values:
        fid = entry["field_id"]
        page = entry["page"]
        value = entry.get("value")

        if value is None:
            continue

        if fid not in existing:
            print(f"ERROR: unknown field id '{fid}'")
            has_error = True
            continue

        field_info = existing[fid]
        if field_info.get("page") != page:
            print(
                f"ERROR: field '{fid}' is on page {field_info.get('page')}, not {page}"
            )
            has_error = True
            continue

        err = validate_value(field_info, value)
        if err:
            print(f"ERROR: {err}")
            has_error = True
            continue

        updates.setdefault(page, {})[fid] = value

    if has_error:
        print("Aborting — fix the errors above and re-run.")
        sys.exit(1)

    # Write
    writer = PdfWriter(clone_from=reader)
    for page_num, field_values in updates.items():
        writer.update_page_form_field_values(
            writer.pages[page_num - 1],
            field_values,
            auto_regenerate=False,
        )
    writer.set_need_appearances_writer(True)

    with open(output_path, "wb") as f:
        writer.write(f)

    total = sum(len(v) for v in updates.values())
    print(f"Filled {total} field(s) → {output_path}")


def main():
    if len(sys.argv) != 4:
        print(
            "Usage: uv run fill_fillable_fields.py input.pdf field_values.json output.pdf"
        )
        sys.exit(1)
    fill(sys.argv[1], sys.argv[2], sys.argv[3])


if __name__ == "__main__":
    main()
