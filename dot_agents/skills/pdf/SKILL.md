---
name: pdf
description: Use this skill whenever the user wants to do anything with PDF files. This includes reading or extracting text/tables from PDFs, combining or merging multiple PDFs into one, splitting PDFs apart, rotating pages, adding watermarks, creating new PDFs, filling PDF forms, encrypting/decrypting PDFs, extracting images, and OCR on scanned PDFs to make them searchable. If the user mentions a .pdf file or asks to produce one, use this skill.
---

# PDF Processing Skill

## Package Management

Always use `uv` to run Python. Every script should declare its own Python version and dependencies
using a PEP 723 inline metadata block — then running it is always just:

```bash
uv run script.py
```

No installs, no `--with` flags needed. Template:

```python
# /// script
# requires-python = ">=3.11"
# dependencies = ["pymupdf", "pdfplumber"]
# ///
```

All scripts in `scripts/` already include this block. Always add it to new scripts before any imports.

---

## Libraries

| Library | Purpose | PyPI name |
|---------|---------|-----------|
| pymupdf | Render PDF pages to images | `pymupdf` |
| pdfplumber | Extract text and tables with layout | `pdfplumber` |
| pypdf | Read/write/merge/split/encrypt PDFs | `pypdf` |
| reportlab | Create PDFs from scratch | `reportlab` |
| Pillow | Image manipulation | `Pillow` |

---

## Convert PDF Pages to Images (pymupdf)

This is the preferred way to render pages. No system dependencies required.

```python
# /// script
# requires-python = ">=3.11"
# dependencies = ["pymupdf"]
# ///
import fitz
import os

def pdf_to_images(pdf_path, output_dir, zoom=1.5):
    """
    zoom=1.0 → ~72 DPI, zoom=1.5 → ~108 DPI, zoom=2.0 → ~144 DPI
    """
    os.makedirs(output_dir, exist_ok=True)
    doc = fitz.open(pdf_path)
    mat = fitz.Matrix(zoom, zoom)
    for i, page in enumerate(doc):
        pix = page.get_pixmap(matrix=mat)
        path = os.path.join(output_dir, f"page_{i+1:02d}.png")
        pix.save(path)
        print(f"page {i+1}: {path} ({pix.width}x{pix.height})")
    print(f"done — {len(doc)} pages")

pdf_to_images("input.pdf", "pages/")
```

Or use the ready-made script:
```bash
uv run scripts/convert_pdf_to_images.py input.pdf pages/ [zoom]
```

### Visual Analysis in Zed

After rendering, display pages with markdown and analyze them with `read_file`:
```markdown
![Page 1](pages/page_01.png)
```

---

## Extract Text (pdfplumber)

```python
# /// script
# requires-python = ">=3.11"
# dependencies = ["pdfplumber"]
# ///
import pdfplumber

with pdfplumber.open("input.pdf") as pdf:
    for i, page in enumerate(pdf.pages):
        text = page.extract_text()
        print(f"--- page {i+1} ---")
        print(text)
```

### Extract Tables

```python
import pdfplumber

with pdfplumber.open("input.pdf") as pdf:
    for i, page in enumerate(pdf.pages):
        for j, table in enumerate(page.extract_tables()):
            print(f"page {i+1}, table {j+1}:")
            for row in table:
                print(row)
```

---

## Read / Write PDFs (pypdf)

### Merge

```python
# /// script
# requires-python = ">=3.11"
# dependencies = ["pypdf"]
# ///
from pypdf import PdfReader, PdfWriter

writer = PdfWriter()
for path in ["a.pdf", "b.pdf", "c.pdf"]:
    reader = PdfReader(path)
    for page in reader.pages:
        writer.add_page(page)

with open("merged.pdf", "wb") as f:
    writer.write(f)
```

### Split

```python
from pypdf import PdfReader, PdfWriter

reader = PdfReader("input.pdf")
for i, page in enumerate(reader.pages):
    w = PdfWriter()
    w.add_page(page)
    with open(f"page_{i+1}.pdf", "wb") as f:
        w.write(f)
```

### Rotate Pages

```python
from pypdf import PdfReader, PdfWriter

reader = PdfReader("input.pdf")
writer = PdfWriter()
page = reader.pages[0]
page.rotate(90)
writer.add_page(page)
with open("rotated.pdf", "wb") as f:
    writer.write(f)
```

### Metadata

```python
from pypdf import PdfReader

reader = PdfReader("input.pdf")
meta = reader.metadata
print(meta.title, meta.author, meta.creator)
```

### Encrypt / Decrypt

```python
from pypdf import PdfReader, PdfWriter

# Encrypt
reader = PdfReader("input.pdf")
writer = PdfWriter()
for page in reader.pages:
    writer.add_page(page)
writer.encrypt("userpass", "ownerpass")
with open("encrypted.pdf", "wb") as f:
    writer.write(f)

# Decrypt
reader = PdfReader("encrypted.pdf")
reader.decrypt("userpass")
```

---

## Create PDFs (reportlab)

```python
# /// script
# requires-python = ">=3.11"
# dependencies = ["reportlab"]
# ///
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

doc = SimpleDocTemplate("output.pdf", pagesize=A4)
styles = getSampleStyleSheet()
story = [
    Paragraph("My Title", styles["Title"]),
    Spacer(1, 12),
    Paragraph("Body text goes here.", styles["Normal"]),
]
doc.build(story)
```

> **Note:** Never use Unicode subscript/superscript characters (₀¹²) in reportlab — use
> `<sub>` / `<super>` XML tags in `Paragraph` objects instead, or adjust position manually
> for canvas text. Built-in fonts don't include those glyphs.

---

## Watermark

```python
from pypdf import PdfReader, PdfWriter

watermark_page = PdfReader("watermark.pdf").pages[0]
reader = PdfReader("input.pdf")
writer = PdfWriter()
for page in reader.pages:
    page.merge_page(watermark_page)
    writer.add_page(page)
with open("watermarked.pdf", "wb") as f:
    writer.write(f)
```

---

## OCR (scanned PDFs)

Fully self-contained — `easyocr` bundles its own models, no system packages needed.
`pymupdf` renders the pages, `easyocr` reads the text.

```python
# /// script
# requires-python = ">=3.11"
# dependencies = ["pymupdf", "easyocr"]
# ///
import fitz
import easyocr

# Languages to recognise — downloads models on first run (~200MB)
reader = easyocr.Reader(["fr", "en"])

doc = fitz.open("scanned.pdf")
for i, page in enumerate(doc):
    pix = page.get_pixmap(matrix=fitz.Matrix(2.0, 2.0))
    results = reader.readtext(pix.tobytes("png"))
    print(f"--- page {i+1} ---")
    for _, text, confidence in results:
        if confidence > 0.3:
            print(text)
```

> First run downloads easyocr language models (~200 MB). Subsequent runs are instant.
> Adjust the language list as needed: `["en"]`, `["fr", "en"]`, etc.

---

---

## Quick Reference

| Task | Tool | How |
|------|------|-----|
| Pages → images | pymupdf | `uv run scripts/convert_pdf_to_images.py` |
| Extract text | pdfplumber | `uv run script.py` |
| Extract tables | pdfplumber | `uv run script.py` |
| Merge / split | pypdf | `uv run script.py` |
| Create PDF | reportlab | `uv run script.py` |
| Encrypt | pypdf | `uv run script.py` |
| OCR | easyocr + pymupdf | `uv run script.py` (downloads models ~200MB on first run) |
| Fill forms | pypdf | See FORMS.md |

---

## See Also

- `FORMS.md` — step-by-step guide for filling PDF forms (fillable and non-fillable)
- `REFERENCE.md` — advanced techniques, coordinate systems, batch processing, optional CLI tools (qpdf, pdftotext)
