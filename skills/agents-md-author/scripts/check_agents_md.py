#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Check a generated AGENTS.md against the agents-md-author template.

Errors (exit 1):
  - a section heading from the template is missing
  - an unfilled {{PLACEHOLDER}} remains
Warnings (exit 0):
  - canonical rule lines from the template were changed or removed
  - TODO/TBD/FIXME markers
  - file longer than --max-lines

Prints one JSON object to stdout.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

PLACEHOLDER = re.compile(r"\{\{[A-Z0-9_]+\}\}")
MARKER = re.compile(r"\b(TODO|TBD|FIXME)\b")
DEFAULT_TEMPLATE = Path(__file__).resolve().parent.parent / "assets" / "AGENTS.md.template"


def headings(lines: list[str]) -> list[str]:
    """Markdown headings outside fenced code blocks."""
    found, fenced = [], False
    for line in lines:
        if line.lstrip().startswith("```"):
            fenced = not fenced
            continue
        if not fenced and re.match(r"^#{1,6} ", line):
            found.append(line.strip())
    return found


def canonical_lines(lines: list[str]) -> list[str]:
    """Template lines that carry fixed rule text (no placeholder, not blank)."""
    return [
        line.strip()
        for line in lines
        if line.strip() and not PLACEHOLDER.search(line) and not re.fullmatch(r"[|\s:-]+", line.strip())
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("agents_md", type=Path, help="Path to the generated AGENTS.md")
    parser.add_argument("--template", type=Path, default=DEFAULT_TEMPLATE, help="Template to compare against")
    parser.add_argument("--max-lines", type=int, default=400, help="Warn above this many lines (default 400)")
    args = parser.parse_args()

    for path in (args.agents_md, args.template):
        if not path.is_file():
            print(f"error: file not found: {path}", file=sys.stderr)
            return 2

    out_lines = args.agents_md.read_text(encoding="utf-8").splitlines()
    tpl_lines = args.template.read_text(encoding="utf-8").splitlines()
    errors: list[str] = []
    warnings: list[str] = []

    present = set(headings(out_lines))
    for heading in headings(tpl_lines):
        if heading not in present:
            errors.append(f"missing heading: {heading}")

    for number, line in enumerate(out_lines, 1):
        for match in PLACEHOLDER.findall(line):
            errors.append(f"line {number}: unfilled placeholder {match}")
        if MARKER.search(line):
            warnings.append(f"line {number}: marker: {line.strip()[:80]}")

    output_set = {line.strip() for line in out_lines}
    changed = [line for line in canonical_lines(tpl_lines) if line not in output_set]
    if changed:
        warnings.append(
            f"{len(changed)} canonical rule line(s) changed or removed; "
            "record intended changes under 'Project deviations'"
        )
        warnings.extend(f"changed: {line[:100]}" for line in changed[:15])

    if len(out_lines) > args.max_lines:
        warnings.append(f"{len(out_lines)} lines exceeds {args.max_lines}; trim project sections, not rules")

    print(json.dumps({"ok": not errors, "lines": len(out_lines), "errors": errors, "warnings": warnings}, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
