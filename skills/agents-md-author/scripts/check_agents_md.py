#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Check a generated AGENTS.md and its prompt templates against the agents-md-author assets.

AGENTS.md errors (exit 1):
  - a section heading from the template is missing
  - an unfilled {{PLACEHOLDER}} remains
Prompt template errors (exit 1), for each assets/pi-prompts/<name>.md:
  - <prompts-dir>/<name>.md is missing
  - an unfilled {{PLACEHOLDER}} remains
  - the frontmatter has no description
Warnings (exit 0), for every checked file:
  - canonical lines from the template were changed or removed
  - TODO/TBD/FIXME markers
  - AGENTS.md longer than --max-lines

The prompts directory defaults to <AGENTS.md dir>/.pi/prompts. Use --no-prompts to check
AGENTS.md alone. Prints one JSON object to stdout.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

PLACEHOLDER = re.compile(r"\{\{[A-Z0-9_]+\}\}")
MARKER = re.compile(r"\b(TODO|TBD|FIXME)\b")
ASSETS = Path(__file__).resolve().parent.parent / "assets"
DEFAULT_TEMPLATE = ASSETS / "AGENTS.md.template"
DEFAULT_PROMPT_TEMPLATES = ASSETS / "pi-prompts"


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


def common_checks(label: str, out_lines: list[str], tpl_lines: list[str], errors: list[str], warnings: list[str]) -> None:
    """Placeholder, marker, and canonical-line checks shared by every generated file."""
    for number, line in enumerate(out_lines, 1):
        for match in PLACEHOLDER.findall(line):
            errors.append(f"{label}:{number}: unfilled placeholder {match}")
        if MARKER.search(line):
            warnings.append(f"{label}:{number}: marker: {line.strip()[:80]}")

    output_set = {line.strip() for line in out_lines}
    changed = [line for line in canonical_lines(tpl_lines) if line not in output_set]
    if changed:
        warnings.append(
            f"{label}: {len(changed)} canonical line(s) changed or removed; "
            "record intended changes under 'Project deviations' in AGENTS.md"
        )
        warnings.extend(f"{label}: changed: {line[:100]}" for line in changed[:15])


def has_description(lines: list[str]) -> bool:
    """True when the file opens with YAML frontmatter containing a non-empty description."""
    if not lines or lines[0].strip() != "---":
        return False
    for line in lines[1:]:
        if line.strip() == "---":
            return False
        if re.match(r"^description:\s*\S", line):
            return True
    return False


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("agents_md", type=Path, help="Path to the generated AGENTS.md")
    parser.add_argument("--template", type=Path, default=DEFAULT_TEMPLATE, help="AGENTS.md template to compare against")
    parser.add_argument("--prompts-dir", type=Path, help="Generated prompt templates (default: <AGENTS.md dir>/.pi/prompts)")
    parser.add_argument("--prompt-templates", type=Path, default=DEFAULT_PROMPT_TEMPLATES, help="Prompt template assets to compare against")
    parser.add_argument("--no-prompts", action="store_true", help="Check AGENTS.md only")
    parser.add_argument("--max-lines", type=int, default=400, help="Warn when AGENTS.md exceeds this many lines (default 400)")
    args = parser.parse_args()

    for path in (args.agents_md, args.template):
        if not path.is_file():
            print(f"error: file not found: {path}", file=sys.stderr)
            return 2

    errors: list[str] = []
    warnings: list[str] = []

    out_lines = args.agents_md.read_text(encoding="utf-8").splitlines()
    tpl_lines = args.template.read_text(encoding="utf-8").splitlines()
    present = set(headings(out_lines))
    for heading in headings(tpl_lines):
        if heading not in present:
            errors.append(f"AGENTS.md: missing heading: {heading}")
    common_checks("AGENTS.md", out_lines, tpl_lines, errors, warnings)
    if len(out_lines) > args.max_lines:
        warnings.append(f"AGENTS.md: {len(out_lines)} lines exceeds {args.max_lines}; trim project sections, not rules")

    prompts_checked: list[str] = []
    if not args.no_prompts:
        prompts_dir = args.prompts_dir or args.agents_md.resolve().parent / ".pi" / "prompts"
        templates = sorted(args.prompt_templates.glob("*.md"))
        if not templates:
            print(f"error: no prompt templates in {args.prompt_templates}", file=sys.stderr)
            return 2
        for template in templates:
            target = prompts_dir / template.name
            label = f".pi/prompts/{template.name}"
            if not target.is_file():
                errors.append(f"{label}: missing (expected {target})")
                continue
            prompt_lines = target.read_text(encoding="utf-8").splitlines()
            if not has_description(prompt_lines):
                errors.append(f"{label}: frontmatter has no description")
            common_checks(label, prompt_lines, template.read_text(encoding="utf-8").splitlines(), errors, warnings)
            prompts_checked.append(label)

    result = {
        "ok": not errors,
        "lines": len(out_lines),
        "prompts": prompts_checked,
        "errors": errors,
        "warnings": warnings,
    }
    print(json.dumps(result, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
