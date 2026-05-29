# PDF Processing — Advanced Reference

## pymupdf — Advanced Rendering

### Render to JPEG

```python
# /// script
# requires-python = ">=3.11"
# dependencies = ["pymupdf"]
# ///
import fitz

doc = fitz.open("input.pdf")
mat = fitz.Matrix(2.0, 2.0)
for i, page in enumerate(doc):
    pix = page.get_pixmap(matrix=mat)
    pix.save(f"page_{i+1:02d}.jpg", jpg_quality=90)
```

### Render a Specific Region (crop)

```python
import fitz

doc = fitz.open("input.pdf")
page = doc[0]
# Clip to a rectangle (x0, y0, x1, y1) in PDF points
clip = fitz.Rect(50, 100, 400, 300)
mat = fitz.Matrix(2.0, 2.0)
pix = page.get_pixmap(matrix=mat, clip=clip)
pix.save("cropped.png")
```

### Extract Text with pymupdf

```python
import fitz

doc = fitz.open("input.pdf")
for i, page in enumerate(doc):
    text = page.get_text()
    print(f"Page {i+1}: {len(text)} chars")
```

---

## pdfplumber — Advanced Text Extraction

### Text with Coordinates

```python
import pdfplumber

with pdfplumber.open("input.pdf") as pdf:
    page = pdf.pages[0]
    for char in page.chars[:20]:
        print(f"'{char['text']}' x={char['x0']:.1f} y={char['top']:.1f}")
```

### Extract Text from a Bounding Box

```python
with pdfplumber.open("input.pdf") as pdf:
    page = pdf.pages[0]
    # (left, top, right, bottom)
    region = page.within_bbox((50, 100, 400, 300))
    print(region.extract_text())
```

### Table Extraction with Custom Settings

```python
with pdfplumber.open("input.pdf") as pdf:
    page = pdf.pages[0]
    settings = {
        "vertical_strategy": "lines",
        "horizontal_strategy": "lines",
        "snap_tolerance": 3,
        "intersection_tolerance": 15,
    }
    tables = page.extract_tables(settings)
```

### Debug Table Layout

```python
with pdfplumber.open("input.pdf") as pdf:
    page = pdf.pages[0]
    img = page.to_image(resolution=150)
    img.save("debug.png")
```

---

## reportlab — Tables and Styling

```python
# /// script
# requires-python = ">=3.11"
# dependencies = ["reportlab"]
# ///
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4

data = [
    ["Product", "Q1", "Q2", "Q3"],
    ["Widget",  "10", "12", "15"],
    ["Gadget",  "8",  "9",  "11"],
]

doc = SimpleDocTemplate("table.pdf", pagesize=A4)
styles = getSampleStyleSheet()

table = Table(data)
table.setStyle(TableStyle([
    ("BACKGROUND",   (0, 0), (-1, 0),  colors.grey),
    ("TEXTCOLOR",    (0, 0), (-1, 0),  colors.whitesmoke),
    ("FONTNAME",     (0, 0), (-1, 0),  "Helvetica-Bold"),
    ("ALIGN",        (0, 0), (-1, -1), "CENTER"),
    ("GRID",         (0, 0), (-1, -1), 1, colors.black),
    ("BACKGROUND",   (0, 1), (-1, -1), colors.beige),
]))

doc.build([Paragraph("Sales Report", styles["Title"]), table])
```

---

## Optional CLI Tools

> These require system packages (`brew install qpdf poppler`) and are not needed for
> normal workflows — everything in `SKILL.md` and `scripts/` works without them.
> Use these only when you specifically need CLI-level control.

### qpdf

```bash
# Install: brew install qpdf
# Extract a page range
qpdf input.pdf --pages . 2-5 -- pages2to5.pdf

# Cherry-pick pages from multiple files
qpdf --empty --pages a.pdf 1-3 b.pdf 5,7 -- combined.pdf

# Split into chunks of N pages
qpdf --split-pages=5 input.pdf chunk_%02d.pdf

# Linearize for web streaming
qpdf --linearize input.pdf web.pdf

# Show PDF structure
qpdf --show-all-pages input.pdf

# Repair corrupted PDF
qpdf --check input.pdf
qpdf --replace-input input.pdf
```

### pdftotext / pdfimages (poppler)

```bash
# Install: brew install poppler

# Extract text preserving layout
pdftotext -layout input.pdf output.txt
pdftotext -f 1 -l 5 input.pdf output.txt   # pages 1–5

# Extract embedded images
pdfimages -all input.pdf images/img

# Convert pages to images (alternative to pymupdf)
pdftoppm -png -r 150 input.pdf pages/page
```

---

## Batch Processing

```python
# /// script
# requires-python = ">=3.11"
# dependencies = ["pypdf"]
# ///
import glob
import logging
from pypdf import PdfReader, PdfWriter

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

writer = PdfWriter()
for path in sorted(glob.glob("docs/*.pdf")):
    try:
        reader = PdfReader(path)
        for page in reader.pages:
            writer.add_page(page)
        log.info("merged %s (%d pages)", path, len(reader.pages))
    except Exception as e:
        log.error("skipping %s: %s", path, e)

with open("all_merged.pdf", "wb") as f:
    writer.write(f)
```

---

## Coordinate Systems

Two coordinate systems appear throughout PDF work:

| System | Origin | Y direction | Used by |
|--------|--------|-------------|---------|
| PDF points | bottom-left | up | pypdf, reportlab, qpdf |
| Image pixels | top-left | down | pymupdf renders, Pillow, pdfplumber |

**Converting image pixels → PDF points:**
```python
pdf_x = pixel_x * (pdf_width  / image_width)
pdf_y = pdf_height - pixel_y * (pdf_height / image_height)
```

**Converting PDF points → image pixels:**
```python
pixel_x = pdf_x * (image_width  / pdf_width)
pixel_y = (pdf_height - pdf_y) * (image_height / pdf_height)
```

---

## Memory-Efficient Large PDF Processing

```python
from pypdf import PdfReader, PdfWriter

def process_in_chunks(path, chunk_size=10):
    reader = PdfReader(path)
    total = len(reader.pages)
    for start in range(0, total, chunk_size):
        end = min(start + chunk_size, total)
        writer = PdfWriter()
        for i in range(start, end):
            writer.add_page(reader.pages[i])
        out = f"chunk_{start//chunk_size:03d}.pdf"
        with open(out, "wb") as f:
            writer.write(f)
        print(f"wrote {out} (pages {start+1}–{end})")
```

---

## Troubleshooting

**Encrypted PDF:**
```python
from pypdf import PdfReader
reader = PdfReader("locked.pdf")
if reader.is_encrypted:
    reader.decrypt("password")
```

**Text extraction returns garbage / "(cid:X)" patterns:**
The PDF is likely a scanned image. Use OCR with `easyocr` (fully self-contained, no system deps):
```python
# /// script
# requires-python = ">=3.11"
# dependencies = ["pymupdf", "easyocr"]
# ///
import fitz, easyocr
reader = easyocr.Reader(["en"])  # downloads models on first run
doc = fitz.open("scanned.pdf")
for i, page in enumerate(doc):
    pix = page.get_pixmap(matrix=fitz.Matrix(2.0, 2.0))
    for _, text, conf in reader.readtext(pix.tobytes("png")):
        if conf > 0.3:
            print(text)
```

**pdfplumber extracts no tables:**
Try `"vertical_strategy": "text"` and `"horizontal_strategy": "text"` in table settings —
useful when the PDF uses whitespace rather than lines for table structure.

**reportlab text renders as black boxes:**
You used Unicode subscript/superscript characters. Replace with `<sub>` / `<super>` tags
in `Paragraph` objects.
