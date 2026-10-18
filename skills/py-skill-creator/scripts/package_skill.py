#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml"]
# ///
"""
Validate and package a skill directory into a distributable .skill file.

Usage:
    package_skill.py <skill-directory> [output-directory]

Examples:
    package_skill.py ~/.claude/skills/my-skill
    package_skill.py ~/.claude/skills/my-skill ~/Downloads
"""

from __future__ import annotations

import argparse
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from validate_skill import iter_packaged_files, validate_skill


def package_skill(skill_path: Path, output_dir: Path | None = None) -> Path | None:
    skill_path = skill_path.expanduser().resolve()
    if not skill_path.is_dir():
        print(f"Error: not a directory: {skill_path}")
        return None

    ok, msg = validate_skill(skill_path)
    if not ok:
        print(f"Validation failed: {msg}")
        return None
    print(f"Validation: {msg}")

    out = (output_dir or Path.cwd()).expanduser().resolve()
    out.mkdir(parents=True, exist_ok=True)
    skill_file = out / f"{skill_path.name}.skill"

    with zipfile.ZipFile(skill_file, "w", zipfile.ZIP_DEFLATED) as archive:
        for file_path in iter_packaged_files(skill_path, exclude_paths={skill_file}):
            arcname = file_path.relative_to(skill_path.parent)
            archive.write(file_path, arcname)
            print(f"  + {arcname}")

    print(f"\nPackaged: {skill_file}")
    return skill_file


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate and package a skill directory into a .skill archive."
    )
    parser.add_argument("skill_directory", help="Path to the skill directory")
    parser.add_argument(
        "output_directory",
        nargs="?",
        help="Directory where the .skill archive should be written (defaults to cwd)",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    skill_path = Path(args.skill_directory)
    output_dir = Path(args.output_directory) if args.output_directory else None

    result = package_skill(skill_path, output_dir)
    sys.exit(0 if result else 1)


if __name__ == "__main__":
    main()
