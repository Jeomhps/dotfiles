#!/usr/bin/env -S uv run --script
#
# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "pyyaml>=6.0.3",
# ]
# ///

from __future__ import annotations

import re
from pathlib import Path

import yaml

START = "<!-- ACTION_DOCS:START -->"
END = "<!-- ACTION_DOCS:END -->"


def one_line(s: str) -> str:
    return " ".join((s or "").strip().split())


def md_escape_pipes(s: str) -> str:
    return s.replace("|", r"\|")


def load_action(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("action.yml root must be a mapping")
    return data


def generate_inputs_table(inputs: dict) -> str:
    header = (
        "## Inputs\n\n"
        "| Name | Description | type | default | required | secret |\n"
        "| --- | --- | --- | --- | --- | --- |\n"
    )

    rows = []
    for name, meta in (inputs or {}).items():
        meta = meta or {}
        desc = one_line(meta.get("description", ""))
        required = bool(meta.get("required", False))
        default = meta.get("default", None)

        typ = "string"
        default_str = "N/A" if default is None else str(default)

        # Your convention: ALL CAPS inputs are secrets
        secret = "yes" if name.isupper() else "no"

        rows.append(
            "| {name} | {desc} | {typ} | {default} | {req} | {secret} |".format(
                name=md_escape_pipes(name),
                desc=md_escape_pipes(desc) if desc else "—",
                typ=typ,
                default=md_escape_pipes(default_str),
                req="true" if required else "false",
                secret=secret,
            )
        )

    return header + "\n".join(rows) + "\n"


def generate_section(action: dict) -> str:
    name = (action.get("name") or "").strip()
    desc = one_line(action.get("description", ""))

    parts = []
    parts.append("<!-- (this section is generated; do not edit by hand) -->\n")

    parts.append("## Description\n\n")
    parts.append(f"{desc}\n\n" if desc else "—\n\n")

    parts.append(generate_inputs_table(action.get("inputs", {})))

    parts.append("## Outputs\n\nNo outputs\n")

    return "".join(parts).rstrip() + "\n"


def replace_between_markers(readme_text: str, generated: str) -> str:
    # Replace everything between START and END (inclusive markers stay)
    pattern = re.compile(
        re.escape(START) + r".*?" + re.escape(END),
        re.DOTALL,
    )

    replacement = f"{START}\n{generated}{END}"

    if pattern.search(readme_text):
        return pattern.sub(replacement, readme_text, count=1)

    # If markers are missing, append them at the end
    if not readme_text.endswith("\n"):
        readme_text += "\n"
    return readme_text + "\n" + replacement + "\n"


def main() -> None:
    action_path = Path("action.yml")  # adjust if needed
    readme_path = Path("README.md")

    action = load_action(action_path)
    generated = generate_section(action)

    existing = readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""
    updated = replace_between_markers(existing, generated)

    readme_path.write_text(updated, encoding="utf-8")
    print(f"Updated {readme_path} between {START} and {END}")


if __name__ == "__main__":
    main()
