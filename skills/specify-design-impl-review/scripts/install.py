#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Install the specify-design-impl-review workflow globally for pi and Codex.

Per harness it writes the five workflow steps (specify, design, design-review, impl,
impl-review) and the sections of assets/global-instructions.md in the global instructions file:

  pi      <PI_CODING_AGENT_DIR or ~/.pi/agent>/prompts/<step>.md      /<step>
          <PI_CODING_AGENT_DIR or ~/.pi/agent>/AGENTS.md              owned sections
  codex   ~/.agents/skills/wf-<step>/SKILL.md + agents/openai.yaml    $wf-<step>, explicit only
          <CODEX_HOME or ~/.codex>/AGENTS.md                          owned sections

Sources are assets/steps/*.md, assets/task-files.md, and assets/global-instructions.md.
Re-run after editing them. Without --harness, only harnesses whose config directory exists
are installed.

Behaviour:
  - Idempotent: unchanged files are left alone; files written by an earlier run are
    updated, and ones no longer produced are removed.
  - Never overwrites a file it did not write (CONFLICT, exit 1) unless --force.
  - Owned files are tracked in <XDG_STATE_HOME or ~/.local/state>/agent-workflow/install-manifest.json.
  - The global instructions file is never replaced. The installer owns only the sections
    headed by the top-level headings of assets/global-instructions.md: an existing section
    with the same heading line is updated in place, a missing one is appended, and every
    other line of the file is left byte-for-byte as it was.
  - --uninstall removes the owned files and the owned sections.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path

ASSETS = Path(__file__).resolve().parent.parent / "assets"
STEPS_DIR = ASSETS / "steps"
TASK_FILES = ASSETS / "task-files.md"
GLOBAL_INSTRUCTIONS = ASSETS / "global-instructions.md"
HEADING_RE = re.compile(r"^(#{1,6})[ \t]+\S")
FENCE_RE = re.compile(r"^ {0,3}(`{3,}|~{3,})")
CODEX_PREFIX = "wf-"
HARNESSES = ("pi", "codex")


@dataclass
class Harness:
    name: str
    home: Path  # config directory used for detection
    root: Path  # directory holding the installed steps
    instructions: Path  # global instructions file that gets the owned sections
    input_text: str  # how a step refers to the user's input
    command: str  # how a step refers to another step, {} = step name


def harness_paths() -> dict[str, Harness]:
    home = Path.home()
    pi = Path(os.environ.get("PI_CODING_AGENT_DIR") or home / ".pi" / "agent").expanduser()
    codex = Path(os.environ.get("CODEX_HOME") or home / ".codex").expanduser()
    return {
        "pi": Harness("pi", pi, pi / "prompts", pi / "AGENTS.md", "$ARGUMENTS", "/{}"),
        "codex": Harness(
            "codex",
            codex,
            home / ".agents" / "skills",
            codex / "AGENTS.md",
            "the text I sent with this skill invocation",
            "$" + CODEX_PREFIX + "{}",
        ),
    }


def manifest_path() -> Path:
    state = Path(os.environ.get("XDG_STATE_HOME") or Path.home() / ".local" / "state").expanduser()
    return state / "agent-workflow" / "install-manifest.json"


def split_frontmatter(text: str, source: Path) -> tuple[str, dict[str, str], str]:
    """Return (raw frontmatter including fences, simple key/value map, body)."""
    match = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not match:
        raise ValueError(f"{source}: missing YAML frontmatter")
    meta = {}
    for line in match.group(1).splitlines():
        key, sep, value = line.partition(":")
        if sep:
            meta[key.strip()] = value.strip().strip('"')
    if not meta.get("description"):
        raise ValueError(f"{source}: frontmatter has no description")
    return match.group(0), meta, text[match.end() :]


def render(body: str, harness: Harness, steps: list[str], partial: str, source: Path) -> str:
    def command(match: re.Match[str]) -> str:
        if match.group(1) not in steps:
            raise ValueError(f"{source}: unknown step in {match.group(0)}")
        return harness.command.format(match.group(1))

    text = body.replace("{{TASK_FILES}}", partial.rstrip("\n")).replace("{{INPUT}}", harness.input_text)
    text = re.sub(r"\{\{CMD:([a-z-]+)\}\}", command, text)
    if leftover := re.search(r"\{\{[^}]*\}\}", text):
        raise ValueError(f"{source}: unknown placeholder {leftover.group(0)}")
    return text


def desired_files(harness: Harness) -> dict[Path, str]:
    """Every file the installer owns for one harness, with its content."""
    sources = sorted(STEPS_DIR.glob("*.md"))
    if not sources:
        raise ValueError(f"no step files in {STEPS_DIR}")
    steps = [path.stem for path in sources]
    partial = TASK_FILES.read_text(encoding="utf-8")
    files: dict[Path, str] = {}
    for source in sources:
        raw_meta, meta, body = split_frontmatter(source.read_text(encoding="utf-8"), source)
        rendered = render(body, harness, steps, partial, source)
        if harness.name == "pi":
            files[harness.root / f"{source.stem}.md"] = raw_meta + rendered
        else:
            name = CODEX_PREFIX + source.stem
            skill = harness.root / name
            description = f"{meta['description']}. Workflow step; use only when the user invokes ${name} explicitly."
            files[skill / "SKILL.md"] = (
                f"---\nname: {name}\ndescription: {json.dumps(description)}\n"
                f"disable-model-invocation: true\n---\n{rendered}"
            )
            files[skill / "agents" / "openai.yaml"] = "policy:\n  allow_implicit_invocation: false\n"
    return files


def headings(lines: list[str]) -> list[tuple[int, int]]:
    """(line index, level) of every Markdown ATX heading outside fenced code blocks."""
    found: list[tuple[int, int]] = []
    fence = ""
    for index, line in enumerate(lines):
        if match := FENCE_RE.match(line):
            marker = match.group(1)
            if not fence:
                fence = marker
            elif marker[0] == fence[0] and len(marker) >= len(fence) and not line.strip(" \t\n`~"):
                fence = ""
            continue
        if not fence and (match := HEADING_RE.match(line)):
            found.append((index, len(match.group(1))))
    return found


def section_span(lines: list[str], heading: str, level: int) -> tuple[int, int] | None:
    """Start and end line of the first section headed exactly by heading, or None."""
    marks = headings(lines)
    for position, (index, _) in enumerate(marks):
        if lines[index].rstrip() == heading:
            end = next((other for other, depth in marks[position + 1 :] if depth <= level), len(lines))
            return index, end
    return None


def owned_sections() -> list[tuple[str, int, str]]:
    """(heading line, level, section text) for each top-level section of the global instructions asset."""
    lines = GLOBAL_INSTRUCTIONS.read_text(encoding="utf-8").strip("\n").splitlines(keepends=True)
    marks = headings(lines)
    if not marks or marks[0][0] != 0:
        raise ValueError(f"{GLOBAL_INSTRUCTIONS}: must start with a Markdown heading")
    level = min(depth for _, depth in marks)
    starts = [index for index, depth in marks if depth == level]
    sections = []
    for start, end in zip(starts, starts[1:] + [len(lines)]):
        heading = lines[start].rstrip()
        if any(heading == other for other, _, _ in sections):
            raise ValueError(f"{GLOBAL_INSTRUCTIONS}: duplicate heading {heading!r}")
        sections.append((heading, level, "".join(lines[start:end]).rstrip() + "\n"))
    return sections


def with_sections(current: str, sections: list[tuple[str, int, str]], install: bool) -> str:
    """Update, append, or (install=False) remove the owned sections; leave every other line untouched."""
    lines = current.splitlines(keepends=True)
    for heading, level, text in sections:
        span = section_span(lines, heading, level)
        if install:
            new = text.splitlines(keepends=True)
            if span:
                start, end = span
                lines[start:end] = new + (["\n"] if end < len(lines) else [])
                continue
            if lines and not lines[-1].endswith("\n"):
                lines[-1] += "\n"
            if lines and lines[-1].strip():
                lines.append("\n")
            lines += new
        elif span:
            start, end = span
            at_end = end == len(lines)
            del lines[start:end]
            while at_end and lines and not lines[-1].strip():  # drop the blank lines it leaves behind
                lines.pop()
    return "".join(lines)


class Installer:
    def __init__(self, dry_run: bool, force: bool) -> None:
        self.dry_run, self.force = dry_run, force
        self.counts = {"written": 0, "unchanged": 0, "removed": 0, "conflicts": 0}

    def act(self, verb: str, path: Path) -> None:
        print(f"{verb:<9} {path}")

    def write(self, path: Path, content: str) -> None:
        if not self.dry_run:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        self.counts["written"] += 1

    def remove(self, path: Path, stop: Path) -> None:
        """Remove path, then empty parent directories up to (not including) stop."""
        self.act("remove", path)
        self.counts["removed"] += 1
        if self.dry_run:
            return
        path.unlink()
        parent = path.parent
        while parent != stop and stop in parent.parents and parent.is_dir() and not any(parent.iterdir()):
            parent.rmdir()
            parent = parent.parent

    def sync_files(self, desired: dict[Path, str], owned: set[Path]) -> set[Path]:
        kept: set[Path] = set()
        for path, content in desired.items():
            if path.is_file() and path.read_text(encoding="utf-8") == content:
                self.counts["unchanged"] += 1
                kept.add(path)
                continue
            if path.exists() and path not in owned and not self.force:
                print(f"CONFLICT  {path} exists and was not written by this installer (use --force)", file=sys.stderr)
                self.counts["conflicts"] += 1
                continue
            self.act("update" if path.exists() else "write", path)
            self.write(path, content)
            kept.add(path)
        return kept

    def prune(self, paths: set[Path], root: Path) -> None:
        for path in sorted(paths):
            if path.is_file():
                self.remove(path, root)

    def sync_sections(self, path: Path, install: bool) -> None:
        current = path.read_text(encoding="utf-8") if path.is_file() else ""
        updated = with_sections(current, owned_sections(), install)
        if updated == current:
            self.counts["unchanged"] += 1
            return
        if not install and not updated.strip():
            self.remove(path, path.parent)
            return
        self.act("sections" if install else "unsection", path)
        self.write(path, updated)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--harness", action="append", choices=HARNESSES, help="harness to process (repeatable; default: every detected one)")
    parser.add_argument("--uninstall", action="store_true", help="remove the installed steps and owned sections")
    parser.add_argument("--dry-run", action="store_true", help="print actions without changing anything")
    parser.add_argument("--force", action="store_true", help="overwrite step files this installer did not write")
    args = parser.parse_args()

    harnesses = harness_paths()
    selected = args.harness or [name for name in HARNESSES if harnesses[name].home.is_dir()]
    for name in HARNESSES:
        if name not in selected:
            print(f"skip      {name} ({harnesses[name].home} not found; pass --harness {name} to force)" if not args.harness else f"skip      {name}")
    if not selected:
        print("error: no harness detected; pass --harness", file=sys.stderr)
        return 2

    manifest_file = manifest_path()
    manifest: dict[str, list[str]] = json.loads(manifest_file.read_text(encoding="utf-8")) if manifest_file.is_file() else {}
    installer = Installer(args.dry_run, args.force)
    try:
        for name in selected:
            harness = harnesses[name]
            owned = {Path(path) for path in manifest.get(name, [])}
            if args.uninstall:
                installer.prune(owned, harness.root)
                manifest.pop(name, None)
            else:
                desired = desired_files(harness)
                kept = installer.sync_files(desired, owned)
                installer.prune(owned - set(desired), harness.root)
                manifest[name] = sorted(str(path) for path in kept)
            installer.sync_sections(harness.instructions, install=not args.uninstall)
    except (OSError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    if not args.dry_run:
        manifest_file.parent.mkdir(parents=True, exist_ok=True)
        manifest_file.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    counts = installer.counts
    print("summary   " + ", ".join(f"{value} {key}" for key, value in counts.items()) + (" (dry run)" if args.dry_run else ""))
    return 1 if counts["conflicts"] else 0


if __name__ == "__main__":
    sys.exit(main())
