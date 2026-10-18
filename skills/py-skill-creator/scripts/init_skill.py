#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
Initialize a new skill directory with a lean scaffold.

Usage:
    init_skill.py <skill-name> --path <output-directory>

Examples:
    init_skill.py my-skill --path ~/.claude/skills
    init_skill.py api-helper --path /tmp --with-references --with-assets
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

MAX_NAME_LENGTH = 64

SKILL_MD_TEMPLATE = """\
---
name: {skill_name}
description: >-
  TODO: Describe what this skill does and when to use it. Include specific triggers
  and contexts. This is the primary mechanism that determines when the skill activates.
---

# {skill_title}

## Overview

TODO: 1-2 sentences explaining what this skill enables.

## [First Section]

TODO: Add content. Choose a structure that fits:
- **Workflow-based**: numbered steps for sequential processes
- **Task-based**: sections per operation for tool collections
- **Reference/guidelines**: specifications or standards
"""

EXAMPLE_SCRIPT_TEMPLATE = """\
#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
\"\"\"
Example script for {skill_name}.

Usage:
    example.py --input <value>
\"\"\"

import argparse


def main():
    parser = argparse.ArgumentParser(description="Example script for {skill_name}")
    parser.add_argument("--input", required=True, help="Input value")
    args = parser.parse_args()

    print(f"Processing: {{args.input}}")


if __name__ == "__main__":
    main()
"""


def title_case(skill_name: str) -> str:
    return " ".join(word.capitalize() for word in skill_name.split("-"))


def validate_name(name: str) -> str | None:
    if not re.match(r"^[a-z0-9-]+$", name):
        return "must be hyphen-case (lowercase letters, digits, hyphens only)"
    if name.startswith("-") or name.endswith("-") or "--" in name:
        return "cannot start/end with hyphens or contain consecutive hyphens"
    if len(name) > MAX_NAME_LENGTH:
        return f"too long ({len(name)} chars, max {MAX_NAME_LENGTH})"
    return None


def init_skill(
    skill_name: str,
    path: str | Path,
    *,
    include_example_script: bool = True,
    include_references: bool = False,
    include_assets: bool = False,
) -> Path | None:
    error = validate_name(skill_name)
    if error:
        print(f"Error: skill name {error}")
        return None

    skill_dir = Path(path).expanduser().resolve() / skill_name
    if skill_dir.exists():
        print(f"Error: directory already exists: {skill_dir}")
        return None

    try:
        skill_dir.mkdir(parents=True)

        skill_title = title_case(skill_name)
        (skill_dir / "SKILL.md").write_text(
            SKILL_MD_TEMPLATE.format(skill_name=skill_name, skill_title=skill_title),
            encoding="utf-8",
        )
        print("  Created SKILL.md")

        scripts_dir = skill_dir / "scripts"
        scripts_dir.mkdir()
        print("  Created scripts/")

        if include_example_script:
            example = scripts_dir / "example.py"
            example.write_text(
                EXAMPLE_SCRIPT_TEMPLATE.format(skill_name=skill_name),
                encoding="utf-8",
            )
            example.chmod(0o755)
            print("  Created scripts/example.py")

        if include_references:
            (skill_dir / "references").mkdir()
            print("  Created references/")

        if include_assets:
            (skill_dir / "assets").mkdir()
            print("  Created assets/")

        print(f"\nInitialized '{skill_name}' at {skill_dir}")
        print("Next: edit SKILL.md, implement scripts, validate, then package.")
        return skill_dir

    except Exception as exc:
        print(f"Error: {exc}")
        return None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Initialize a new skill directory scaffold.")
    parser.add_argument("skill_name", help="Skill name in hyphen-case")
    parser.add_argument("--path", required=True, help="Parent directory where the skill will be created")
    parser.add_argument(
        "--no-example-script",
        action="store_true",
        help="Create scripts/ without scripts/example.py",
    )
    parser.add_argument(
        "--with-references",
        action="store_true",
        help="Create an empty references/ directory",
    )
    parser.add_argument(
        "--with-assets",
        action="store_true",
        help="Create an empty assets/ directory",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    result = init_skill(
        args.skill_name,
        args.path,
        include_example_script=not args.no_example_script,
        include_references=args.with_references,
        include_assets=args.with_assets,
    )
    sys.exit(0 if result else 1)


if __name__ == "__main__":
    main()
