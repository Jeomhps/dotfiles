# /// script
# requires-python = ">=3.11"
# dependencies = ["pypdf"]
# ///

import sys

from pypdf import PdfReader


def main():
    if len(sys.argv) != 2:
        print("Usage: uv run check_fillable_fields.py <input.pdf>")
        sys.exit(1)

    path = sys.argv[1]
    reader = PdfReader(path)
    fields = reader.get_fields()

    if fields:
        print(f"This PDF has fillable form fields ({len(fields)} found).")
    else:
        print(
            "This PDF has no fillable form fields. Use visual annotation approach — see FORMS.md."
        )


if __name__ == "__main__":
    main()
