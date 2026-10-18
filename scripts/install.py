#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
Symlink every skill in ./skills into the user-level skill directories of the
agent harnesses, so edits in this repo are live everywhere.

Defaults:
    ~/.agents/skills   cross-harness convention (Pi, Codex, Cline, Zed, ...)
    ~/.claude/skills   Claude Code (does not read ~/.agents/skills)

Usage:
    install.py [--target DIR ...] [--dry-run] [--force]

Behaviour:
    - Idempotent. Re-running repairs links and removes dangling links that
      point into this repo (skills that were deleted or renamed).
    - Never touches a real directory or a link that points elsewhere unless
      --force is given for the latter; real directories are never replaced.
    - Targets that resolve to the same directory (e.g. ~/.claude/skills being
      a symlink to ~/.agents/skills) are processed once.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SKILLS = REPO / "skills"
DEFAULT_TARGETS = ["~/.agents/skills", "~/.claude/skills"]


def is_ours(link: Path) -> bool:
    """True if `link` is a symlink whose target lies inside this repo's skills/."""
    if not link.is_symlink():
        return False
    return SKILLS in (link.parent / link.readlink()).resolve(strict=False).parents


def sync_target(target: Path, names: list[str], dry_run: bool, force: bool) -> int:
    problems = 0
    if not dry_run:
        target.mkdir(parents=True, exist_ok=True)

    for name in names:
        link, source = target / name, SKILLS / name
        if link.is_symlink() and link.resolve() == source:
            continue
        if link.is_symlink() and (is_ours(link) or force):
            print(f"relink  {link}")
            if not dry_run:
                link.unlink()
        elif link.exists() or link.is_symlink():
            print(f"CONFLICT {link} exists and is not managed by this repo", file=sys.stderr)
            problems += 1
            continue
        else:
            print(f"link    {link} -> {source}")
        if not dry_run:
            link.symlink_to(source, target_is_directory=True)

    if target.is_dir():
        for link in sorted(target.iterdir()):
            if link.is_symlink() and is_ours(link) and link.name not in names:
                print(f"prune   {link}")
                if not dry_run:
                    link.unlink()
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--target", action="append", help="skill directory to install into (repeatable; replaces defaults)")
    parser.add_argument("--dry-run", action="store_true", help="print actions without changing anything")
    parser.add_argument("--force", action="store_true", help="replace symlinks that point outside this repo")
    args = parser.parse_args()

    names = sorted(p.parent.name for p in SKILLS.glob("*/SKILL.md"))
    if not names:
        print(f"no skills found in {SKILLS}", file=sys.stderr)
        return 1

    seen: set[Path] = set()
    problems = 0
    for raw in args.target or DEFAULT_TARGETS:
        target = Path(raw).expanduser()
        resolved = target.resolve()
        if resolved in seen:
            print(f"skip    {target} (same directory as an earlier target)")
            continue
        seen.add(resolved)
        problems += sync_target(target, names, args.dry_run, args.force)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
