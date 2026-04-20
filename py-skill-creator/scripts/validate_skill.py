#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml"]
# ///
"""
Validate a skill directory.

Usage:
    validate_skill.py <skill-directory>
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

import yaml

MAX_NAME_LENGTH = 64
MAX_DESCRIPTION_LENGTH = 1024
MAX_BODY_LINES = 500
ALLOWED_FRONTMATTER_KEYS = {"name", "description"}
ALLOWED_TOP_LEVEL = {"SKILL.md", "scripts", "references", "assets"}
IGNORED_NAMES = {"__pycache__", ".DS_Store"}
IGNORED_SUFFIXES = {".pyc", ".pyo"}
REQUIRED_SHEBANG = "#!/usr/bin/env -S uv run"


def normalize_text(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def validate_name(name: str) -> str | None:
    if not re.match(r"^[a-z0-9-]+$", name):
        return "must be hyphen-case (lowercase letters, digits, hyphens only)"
    if name.startswith("-") or name.endswith("-") or "--" in name:
        return "cannot start/end with hyphens or contain consecutive hyphens"
    if len(name) > MAX_NAME_LENGTH:
        return f"too long ({len(name)} chars, max {MAX_NAME_LENGTH})"
    return None


def is_ignored_path(path: Path, root: Path) -> bool:
    try:
        parts = path.relative_to(root).parts
    except ValueError:
        return False

    for part in parts:
        if part in IGNORED_NAMES:
            return True
        if part.startswith("."):
            return True
        if part.endswith("~"):
            return True

    return path.suffix in IGNORED_SUFFIXES or path.name.endswith(".skill")


def is_within(root: Path, candidate: Path) -> bool:
    try:
        candidate.relative_to(root)
        return True
    except ValueError:
        return False


def parse_frontmatter(content: str) -> tuple[dict, str]:
    normalized = normalize_text(content)
    if not normalized.startswith("---\n"):
        raise ValueError("No YAML frontmatter (must start with ---)")

    match = re.match(r"^---\n(.*?)\n---(?:\n|$)", normalized, re.DOTALL)
    if not match:
        raise ValueError("Invalid frontmatter format")

    try:
        frontmatter = yaml.safe_load(match.group(1))
    except yaml.YAMLError as exc:
        raise ValueError(f"Invalid YAML: {exc}") from exc

    if not isinstance(frontmatter, dict):
        raise ValueError("Frontmatter must be a YAML dictionary")

    body = normalized[match.end() :]
    return frontmatter, body


def load_skill_metadata(skill_path: Path) -> tuple[dict, str]:
    skill_md = skill_path / "SKILL.md"
    if not skill_md.exists():
        raise ValueError("SKILL.md not found")
    return parse_frontmatter(skill_md.read_text(encoding="utf-8"))


def iter_packaged_files(skill_path: Path, *, exclude_paths: set[Path] | None = None):
    excluded = {path.resolve() for path in (exclude_paths or set())}

    skill_md = skill_path / "SKILL.md"
    if skill_md.exists() and skill_md.resolve() not in excluded and not is_ignored_path(skill_md, skill_path):
        yield skill_md

    for top_level_name in ("scripts", "references", "assets"):
        top_level = skill_path / top_level_name
        if not top_level.exists():
            continue

        for path in sorted(top_level.rglob("*")):
            if path.resolve() in excluded:
                continue
            if is_ignored_path(path, skill_path) or path.is_dir():
                continue
            yield path


def collect_markdown_links(body: str) -> list[str]:
    targets: list[str] = []
    for raw_target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", body):
        target = raw_target.strip()
        if target.startswith("<") and target.endswith(">"):
            target = target[1:-1].strip()
        if not target:
            continue
        if any(target.startswith(prefix) for prefix in ("http://", "https://", "mailto:", "#")):
            continue
        target = target.split("#", 1)[0].strip()
        if not target:
            continue
        if " " in target:
            target = target.split(" ", 1)[0]
        if target:
            targets.append(target)
    return targets


def collect_script_invocations(body: str) -> list[str]:
    seen: set[str] = set()
    results: list[str] = []
    for match in re.finditer(r"uv run\s+(scripts/[\w./-]+\.py)\b", body):
        target = match.group(1)
        if target not in seen:
            seen.add(target)
            results.append(target)
    return results


def validate_script_file(path: Path, skill_path: Path) -> str | None:
    relative = path.relative_to(skill_path)

    if path.suffix != ".py":
        return f"{relative}: only Python files are allowed under scripts/"

    try:
        content = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return f"{relative}: must be valid UTF-8 text"

    lines = content.splitlines()
    if not lines:
        return f"{relative}: file is empty"
    if lines[0].strip() != REQUIRED_SHEBANG:
        return f"{relative}: shebang must be exactly '{REQUIRED_SHEBANG}'"
    if len(lines) < 4 or lines[1].strip() != "# /// script":
        return f"{relative}: missing PEP 723 script metadata block"

    end_index = None
    for index, line in enumerate(lines[2:], start=2):
        if line.strip() == "# ///":
            end_index = index
            break
    if end_index is None:
        return f"{relative}: unterminated PEP 723 script metadata block"

    metadata_lines = lines[2:end_index]
    if not any(line.strip().startswith("# requires-python") for line in metadata_lines):
        return f"{relative}: PEP 723 metadata must declare requires-python"
    if not any(line.strip().startswith("# dependencies") for line in metadata_lines):
        return f"{relative}: PEP 723 metadata must declare dependencies"

    if os.name != "nt" and not os.access(path, os.X_OK):
        return f"{relative}: script must be executable"

    return None


def validate_skill(skill_path: Path) -> tuple[bool, str]:
    if not skill_path.is_dir():
        return False, f"Not a directory: {skill_path}"

    try:
        frontmatter, body = load_skill_metadata(skill_path)
    except ValueError as exc:
        return False, str(exc)

    unexpected_top_level = []
    for entry in sorted(skill_path.iterdir(), key=lambda item: item.name):
        if is_ignored_path(entry, skill_path):
            continue
        if entry.name not in ALLOWED_TOP_LEVEL:
            unexpected_top_level.append(entry.name)
    if unexpected_top_level:
        return False, f"Unexpected top-level entries: {', '.join(unexpected_top_level)}"

    unexpected_keys = sorted(set(frontmatter) - ALLOWED_FRONTMATTER_KEYS)
    if unexpected_keys:
        return False, f"Unexpected frontmatter keys: {', '.join(unexpected_keys)}"

    name = frontmatter.get("name", "")
    if not isinstance(name, str) or not name.strip():
        return False, "Missing or invalid 'name'"
    name = name.strip()
    error = validate_name(name)
    if error:
        return False, f"Name '{name}' {error}"
    if skill_path.name != name:
        return False, f"Directory name '{skill_path.name}' must match frontmatter name '{name}'"

    description = frontmatter.get("description", "")
    if not isinstance(description, str) or not description.strip():
        return False, "Missing or empty 'description'"
    description = description.strip()
    if "<" in description or ">" in description:
        return False, "Description cannot contain angle brackets"
    if len(description) > MAX_DESCRIPTION_LENGTH:
        return False, f"Description too long ({len(description)} chars, max {MAX_DESCRIPTION_LENGTH})"

    if not body.strip():
        return False, "SKILL.md body cannot be empty"
    body_line_count = len(body.strip("\n").splitlines())
    if body_line_count > MAX_BODY_LINES:
        return False, f"SKILL.md body too long ({body_line_count} lines, max {MAX_BODY_LINES})"

    scripts_dir = skill_path / "scripts"
    if scripts_dir.exists():
        for path in sorted(scripts_dir.rglob("*")):
            if is_ignored_path(path, skill_path):
                continue
            if path.is_dir():
                continue
            error = validate_script_file(path, skill_path)
            if error:
                return False, error

    referenced_paths = set(collect_markdown_links(body))
    referenced_paths.update(collect_script_invocations(body))
    for reference in sorted(referenced_paths):
        ref_path = (skill_path / reference).resolve()
        if not is_within(skill_path.resolve(), ref_path):
            return False, f"Referenced path escapes skill directory: {reference}"
        if not ref_path.exists():
            return False, f"Referenced path not found: {reference}"

    return True, "Valid"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate a skill directory.")
    parser.add_argument("skill_directory", help="Path to the skill directory")
    return parser



def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    path = Path(args.skill_directory).expanduser().resolve()
    ok, msg = validate_skill(path)
    print(msg)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
