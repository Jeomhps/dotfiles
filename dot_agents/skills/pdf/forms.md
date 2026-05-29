# PDF Forms — Filling Guide

## Overview

This guide walks through filling PDF forms. The approach depends on whether the PDF has
native fillable fields or not.

**Step 0 — check what you're dealing with:**
```bash
uv run scripts/check_fillable_fields.py input.pdf
```

- If it prints **"has fillable fields"** → follow [Fillable Fields](#fillable-fields)
- If it prints **"no fillable fields"** → follow [Non-Fillable Fields](#non-fillable-fields)

---

## Fillable Fields

### Step 1 — Extract field info

```bash
uv run scripts/extract_form_field_info.py input.pdf field_info.json
```

This produces `field_info.json` — a list of all fields with their IDs, types, page numbers,
and bounding boxes. Field types: `text`, `checkbox`, `radio_group`, `choice`.

Checkbox fields include `checked_value` and `unchecked_value`.
Radio groups include a `radio_options` list with `value` and `rect` per option.
Choice fields include a `choice_options` list with `value` and `text` per option.

### Step 2 — Render pages to identify fields visually

```bash
uv run scripts/convert_pdf_to_images.py input.pdf pages/
```

Analyze the images alongside `field_info.json` to understand what each field is for.
Convert bounding box PDF coordinates to image coordinates to match fields to visuals.

### Step 3 — Create `field_values.json`

```json
[
  {
    "field_id": "last_name",
    "description": "User last name",
    "page": 1,
    "value": "Stoll"
  },
  {
    "field_id": "Checkbox12",
    "description": "Confirm agreement",
    "page": 1,
    "value": "/On"
  }
]
```

- `field_id` must match exactly what `extract_form_field_info.py` output
- For checkboxes: use the `checked_value` from `field_info.json` to check, `unchecked_value` to uncheck
- For radio groups: use one of the `value` entries from `radio_options`
- For choice fields: use one of the `value` entries from `choice_options`

### Step 4 — Fill the form

```bash
uv run scripts/fill_fillable_fields.py input.pdf field_values.json output.pdf
```

The script validates field IDs and values before writing. Fix any reported errors and re-run.

### Step 5 — Verify

```bash
uv run scripts/convert_pdf_to_images.py output.pdf verify/
```

Visually confirm that all fields are filled correctly.

---

## Non-Fillable Fields

For scanned or image-based PDFs with no native form fields, we add text annotations
at the correct positions.

### Step 1 — Try structure extraction first

```bash
uv run scripts/extract_form_structure.py input.pdf structure.json
```

This extracts text labels, horizontal lines, and checkbox rectangles with exact PDF
coordinates. If `structure.json` contains useful labels → use **Approach A**.
If the PDF is a scan with no extractable text → use **Approach B**.

---

### Approach A — Structure-Based (preferred)

Use when `extract_form_structure.py` found text labels.

**Coordinate system:** PDF coordinates — y=0 is at the **top** of the page, increasing downward.

For each field, calculate positions from `structure.json`:
- Text field entry starts just after the label (`entry_x0 = label.x1 + 5`)
- Entry bottom aligns with the next horizontal line below

Create `fields.json` using `pdf_width` / `pdf_height` to signal PDF coordinates:

```json
{
  "pages": [
    { "page_number": 1, "pdf_width": 595, "pdf_height": 842 }
  ],
  "form_fields": [
    {
      "page_number": 1,
      "description": "Last name",
      "field_label": "Nom",
      "label_bounding_box": [43, 63, 87, 73],
      "entry_bounding_box": [92, 63, 260, 79],
      "entry_text": { "text": "Stoll", "font_size": 10 }
    },
    {
      "page_number": 1,
      "description": "Checkbox — agree",
      "field_label": "Oui",
      "label_bounding_box": [260, 200, 280, 210],
      "entry_bounding_box": [285, 197, 292, 205],
      "entry_text": { "text": "X" }
    }
  ]
}
```

Validate before filling:
```bash
uv run scripts/check_bounding_boxes.py fields.json
```

Then fill:
```bash
uv run scripts/fill_pdf_form_with_annotations.py input.pdf fields.json output.pdf
```

---

### Approach B — Visual Estimation (fallback)

Use when the PDF is a scan and structure extraction found no usable text.

**Step 1 — Render pages:**
```bash
uv run scripts/convert_pdf_to_images.py input.pdf pages/
```

**Step 2 — Estimate field positions visually.** For each field, note approximate pixel
coordinates from the rendered images.

**Step 3 — Refine with crops.** Use ImageMagick to zoom into each field area:
```bash
magick pages/page_01.png -crop 300x80+50+120 +repage crop_name.png
# or: convert pages/page_01.png -crop 300x80+50+120 +repage crop_name.png
```
Examine the crop to get precise pixel coordinates, then add back the crop offset:
- `full_x = crop_x_within_image + crop_offset_x`
- `full_y = crop_y_within_image + crop_offset_y`

**Step 4 — Create `fields.json`** using `image_width` / `image_height` to signal image coordinates:

```json
{
  "pages": [
    { "page_number": 1, "image_width": 893, "image_height": 1263 }
  ],
  "form_fields": [
    {
      "page_number": 1,
      "description": "Last name",
      "field_label": "Nom",
      "label_bounding_box": [120, 175, 242, 198],
      "entry_bounding_box": [255, 175, 720, 218],
      "entry_text": { "text": "Stoll", "font_size": 10 }
    }
  ]
}
```

**Step 5 — Validate:**
```bash
uv run scripts/check_bounding_boxes.py fields.json
```

**Step 6 — Fill:**
```bash
uv run scripts/fill_pdf_form_with_annotations.py input.pdf fields.json output.pdf
```

**Step 7 — Verify:**
```bash
uv run scripts/convert_pdf_to_images.py output.pdf verify/
```

---

### Hybrid Approach

Use when structure extraction works for most fields but misses some (e.g. circular checkboxes).

1. Use Approach A for fields found in `structure.json`
2. Use Approach B zoom refinement for the missing fields
3. Convert visually-estimated image coordinates to PDF coordinates before combining:
   - `pdf_x = image_x × (pdf_width / image_width)`
   - `pdf_y = image_y × (pdf_height / image_height)`
4. Use a single `pdf_width` / `pdf_height` coordinate system in `fields.json`

---

## Troubleshooting

**Text is misplaced after filling:**
- Approach A: confirm you used coordinates from `structure.json` with `pdf_width`/`pdf_height`
- Approach B: confirm image dimensions match the actual rendered PNG size
- Hybrid: double-check coordinate conversions

**`check_bounding_boxes.py` reports intersections:**
- Adjust `entry_bounding_box` values so fields don't overlap
- Reduce font size or shrink box dimensions

**Field not found by `fill_fillable_fields.py`:**
- Re-run `extract_form_field_info.py` and copy the `field_id` exactly as printed
