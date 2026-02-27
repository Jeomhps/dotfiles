#!/usr/bin/env -S uv run --script
#
# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "pyyaml>=6.0.3",
# ]
# ///

from __future__ import annotations

import argparse
import re
import textwrap
from pathlib import Path

import yaml

START = "<!-- ACTION_DOCS:START -->"
END = "<!-- ACTION_DOCS:END -->"


def normalize_spaces(s: str) -> str:
    """Collapse whitespace/newlines to single spaces (good for table cells)."""
    return " ".join((s or "").strip().split())


def wrap_paragraph(s: str, width: int = 88) -> str:
    """
    Wrap text to a reasonable width for Markdown paragraphs.
    Preserves paragraph breaks if the YAML had blank lines.
    Avoids breaking long tokens (e.g., URLs / markdown links).
    """
    s = (s or "").strip()
    if not s:
        return ""

    paras = re.split(r"\n\s*\n", s)
    wrapped: list[str] = []

    wrapper = textwrap.TextWrapper(
        width=width,
        break_long_words=False,  # <-- critical: do not split URLs
        break_on_hyphens=False,  # <-- helps for long paths with hyphens
    )

    for p in paras:
        p = normalize_spaces(p)
        wrapped.append(wrapper.fill(p))

    return "\n\n".join(wrapped)


def md_escape_pipes(s: str) -> str:
    """Escape '|' for markdown tables."""
    return s.replace("|", r"\|")


def load_action(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path}: root must be a mapping")
    return data


def infer_input_type(meta: dict) -> str:
    """
    Infer input type for docs. GitHub Actions inputs are strings at runtime,
    but for documentation it's useful to show boolean when the default is true/false.
    """
    default = (meta or {}).get("default", None)

    # YAML booleans (default: true/false without quotes) become Python bool
    if isinstance(default, bool):
        return "boolean"

    # Sometimes people write default as a quoted string: "true"/"false"
    if isinstance(default, str) and default.strip().lower() in ("true", "false"):
        return "boolean"

    return "string"


def generate_inputs_table(inputs: dict) -> str:
    inputs = inputs or {}
    if not inputs:
        return "## Inputs\n\nNo inputs\n"

    header = (
        "## Inputs\n\n"
        "| Name | Description | type | default | required | secret |\n"
        "| --- | --- | --- | --- | --- | --- |\n"
    )

    rows: list[str] = []
    for name, meta in inputs.items():
        meta = meta or {}
        desc = normalize_spaces(meta.get("description", ""))
        required = bool(meta.get("required", False))
        default = meta.get("default", None)

        typ = infer_input_type(meta)

        if default is None:
            default_str = "N/A"
        elif isinstance(default, bool):
            # show as lowercase to match YAML/GitHub conventions
            default_str = "true" if default else "false"
        else:
            default_str = str(default)

        secret = "yes" if str(name).isupper() else "no"

        rows.append(
            "| {name} | {desc} | {typ} | {default} | {req} | {secret} |".format(
                name=md_escape_pipes(str(name)),
                desc=md_escape_pipes(desc) if desc else "—",
                typ=typ,
                default=md_escape_pipes(default_str),
                req="true" if required else "false",
                secret=secret,
            )
        )

    return header + "\n".join(rows) + "\n"


def generate_outputs_table(outputs: dict) -> str:
    outputs = outputs or {}
    if not outputs:
        return "## Outputs\n\nNo outputs\n"

    header = "## Outputs\n\n| Name | Description |\n| --- | --- |\n"

    rows: list[str] = []
    for name, meta in outputs.items():
        meta = meta or {}
        desc = normalize_spaces(meta.get("description", ""))
        rows.append(
            "| {name} | {desc} |".format(
                name=md_escape_pipes(str(name)),
                desc=md_escape_pipes(desc) if desc else "—",
            )
        )

    return header + "\n".join(rows) + "\n"


def generate_section(
    action: dict, include_name_h1: bool = True, wrap_width: int = 88
) -> str:
    name = (action.get("name") or "").strip()
    desc = wrap_paragraph(action.get("description", ""), width=wrap_width)

    parts: list[str] = []
    parts.append("<!-- (this section is generated; do not edit by hand) -->\n\n")

    # If you already have a manual H1 above the markers, pass --no-name-h1
    if include_name_h1 and name:
        parts.append(f"# {name}\n\n")

    parts.append("## Description\n\n")
    parts.append(f"{desc}\n\n" if desc else "—\n\n")

    parts.append(generate_inputs_table(action.get("inputs", {})))
    parts.append(generate_outputs_table(action.get("outputs", {})))

    return "".join(parts).rstrip() + "\n"


def replace_between_markers(
    readme_text: str, generated: str, start: str, end: str
) -> str:
    """
    Replace everything between start and end markers (markers remain).
    If markers don't exist, append a new marked block at the end.
    """
    pattern = re.compile(re.escape(start) + r".*?" + re.escape(end), re.DOTALL)
    replacement = f"{start}\n{generated}{end}"

    if pattern.search(readme_text):
        return pattern.sub(replacement, readme_text, count=1)

    if readme_text and not readme_text.endswith("\n"):
        readme_text += "\n"
    return (readme_text + "\n" + replacement + "\n").lstrip("\n")


def resolve_paths(
    action_file: str | None, readme_file: str | None, cwd: Path
) -> tuple[Path, Path]:
    """
    Defaults:
      - action file: ./action.yml
      - readme file: ./README.md
    If you pass a directory to --action or --readme, it resolves to action.yml / README.md inside it.
    """

    def _resolve(p: str | None, default_name: str) -> Path:
        if p is None:
            return cwd / default_name
        path = Path(p).expanduser()
        if path.is_dir():
            return path / default_name
        return path

    return _resolve(action_file, "action.yml"), _resolve(readme_file, "README.md")


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        prog="generate-readme",
        description="Generate a README section (between markers) from a GitHub action.yml.",
    )
    ap.add_argument(
        "-a",
        "--action",
        dest="action_file",
        default=None,
        help="Path to action.yml (or a directory containing it). Default: ./action.yml",
    )
    ap.add_argument(
        "-r",
        "--readme",
        dest="readme_file",
        default=None,
        help="Path to README.md to update (or a directory containing it). Default: ./README.md",
    )
    ap.add_argument(
        "--start",
        default=START,
        help=f"Start marker. Default: {START}",
    )
    ap.add_argument(
        "--end",
        default=END,
        help=f"End marker. Default: {END}",
    )
    ap.add_argument(
        "--no-name-h1",
        action="store_true",
        help="Do not emit a '# <action name>' heading in the generated section.",
    )
    ap.add_argument(
        "--wrap",
        type=int,
        default=88,
        help="Wrap width for the Description paragraph. Default: 88",
    )
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the updated README to stdout; do not write the file.",
    )
    return ap.parse_args()


def main() -> None:
    args = parse_args()
    cwd = Path.cwd()

    action_path, readme_path = resolve_paths(args.action_file, args.readme_file, cwd)

    # Meaningful error if run with no args in a dir without action.yml
    if not action_path.exists():
        if args.action_file is None:
            raise SystemExit(
                f"No action.yml found (looked for: {action_path}).\n"
                "Run this from your action folder, or pass --action <path-to-action.yml> "
                "(or --action <dir-containing-action.yml>)."
            )
        raise SystemExit(f"Action file not found: {action_path}")

    action = load_action(action_path)
    generated = generate_section(
        action,
        include_name_h1=not args.no_name_h1,
        wrap_width=args.wrap,
    )

    # README is allowed to not exist; we'll create it.
    existing = readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""
    updated = replace_between_markers(existing, generated, args.start, args.end)

    if args.dry_run:
        print(updated, end="")
        return

    readme_path.write_text(updated, encoding="utf-8")
    print(
        f"Updated {readme_path} using {action_path} between {args.start} and {args.end}"
    )


if __name__ == "__main__":
    main()
