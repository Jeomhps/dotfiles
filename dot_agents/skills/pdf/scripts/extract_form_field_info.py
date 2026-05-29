# /// script
# requires-python = ">=3.11"
# dependencies = ["pypdf"]
# ///
"""
Extract field information from a fillable PDF form.

Outputs a JSON file describing each field: its ID, type, page, bounding rect,
and type-specific options (checked values for checkboxes, options for choice/radio).

Usage: uv run extract_form_field_info.py input.pdf field_info.json
"""

import json
import sys

from pypdf import PdfReader


def full_field_id(annotation) -> str | None:
    """Walk up the parent chain to build a dot-separated field ID."""
    parts = []
    node = annotation
    while node:
        name = node.get("/T")
        if name:
            parts.append(str(name))
        node = node.get("/Parent")
    return ".".join(reversed(parts)) if parts else None


def field_type_info(field) -> dict:
    ft = field.get("/FT")
    if ft == "/Tx":
        return {"type": "text"}
    if ft == "/Btn":
        states = field.get("/_States_", [])
        off = "/Off"
        if len(states) == 2 and off in states:
            checked = states[0] if states[0] != off else states[1]
            return {
                "type": "checkbox",
                "checked_value": checked,
                "unchecked_value": off,
            }
        return {
            "type": "checkbox",
            "checked_value": states[0] if states else "/On",
            "unchecked_value": "/Off",
        }
    if ft == "/Ch":
        states = field.get("/_States_", [])
        options = [
            {"value": s[0], "text": s[1]}
            if isinstance(s, list)
            else {"value": s, "text": s}
            for s in states
        ]
        return {"type": "choice", "choice_options": options}
    return {"type": f"unknown ({ft})"}


def extract_fields(pdf_path: str) -> list[dict]:
    reader = PdfReader(pdf_path)
    raw_fields = reader.get_fields() or {}

    # Identify which field IDs are radio group children (no /T of their own at leaf level)
    possible_radio_parents: set[str] = set()
    for fid, field in raw_fields.items():
        if field.get("/FT") is None and field.get("/Kids"):
            possible_radio_parents.add(fid)

    info_by_id: dict[str, dict] = {}
    for fid, field in raw_fields.items():
        if fid in possible_radio_parents:
            continue
        entry = {"field_id": fid}
        entry.update(field_type_info(field))
        info_by_id[fid] = entry

    radio_groups: dict[str, dict] = {}

    for page_idx, page in enumerate(reader.pages):
        annotations = page.get("/Annots") or []
        for ann in annotations:
            fid = full_field_id(ann)
            if not fid:
                continue

            if fid in info_by_id:
                info_by_id[fid]["page"] = page_idx + 1
                rect = ann.get("/Rect")
                if rect:
                    info_by_id[fid]["rect"] = [float(v) for v in rect]
                continue

            # Could be a radio button option
            parent = ann.get("/Parent")
            if not parent:
                continue
            parent_id = full_field_id(parent)
            if not parent_id:
                continue

            try:
                on_values = [v for v in ann["/AP"]["/N"] if v != "/Off"]
            except (KeyError, TypeError):
                continue

            rect = ann.get("/Rect")
            rect_list = [float(v) for v in rect] if rect else None

            if parent_id not in radio_groups:
                radio_groups[parent_id] = {
                    "field_id": parent_id,
                    "type": "radio_group",
                    "page": page_idx + 1,
                    "radio_options": [],
                }
            if on_values and rect_list:
                radio_groups[parent_id]["radio_options"].append(
                    {
                        "value": on_values[0],
                        "rect": rect_list,
                    }
                )

    # Collect fields that have a resolved page location
    result = []
    for entry in info_by_id.values():
        if "page" in entry:
            result.append(entry)
        else:
            print(
                f"Warning: could not locate field '{entry['field_id']}' on any page — skipping",
                file=sys.stderr,
            )

    result.extend(radio_groups.values())

    # Sort by page then top-to-bottom
    def sort_key(f):
        page = f.get("page", 0)
        if "radio_options" in f and f["radio_options"]:
            y = -f["radio_options"][0]["rect"][1]
        elif "rect" in f:
            y = -f["rect"][1]
        else:
            y = 0
        return (page, y)

    result.sort(key=sort_key)
    return result


def main():
    if len(sys.argv) != 3:
        print("Usage: uv run extract_form_field_info.py input.pdf field_info.json")
        sys.exit(1)

    fields = extract_fields(sys.argv[1])
    with open(sys.argv[2], "w") as f:
        json.dump(fields, f, indent=2)
    print(f"Wrote {len(fields)} fields to {sys.argv[2]}")


if __name__ == "__main__":
    main()
