---
name: py-skill-creator
description: >-
  Create, edit, validate, and package skills for Claude Code, Pi, or any agent.
  Use when creating a new skill, editing an existing skill, adding scripts to a skill,
  or packaging a skill for distribution. All scripts bundled in skills must be Python
  with PEP 723 inline metadata executed via uv run (not bash, not plain python3).
---

# Py Skill Creator

## Skill Anatomy

```text
skill-name/
├── SKILL.md          (required — frontmatter + instructions)
├── scripts/          (optional — Python scripts with uv run + PEP 723)
├── references/       (optional — docs loaded into context as needed)
└── assets/           (optional — templates/images used in output, not loaded into context)
```

Validation enforces these rules:
- The directory name must match frontmatter `name`
- Frontmatter allows only `name` and `description`
- `name` must be hyphen-case and ≤64 chars
- `description` must be ≤1024 chars and contain no `<>`
- `SKILL.md` body must be non-empty and stay under 500 lines
- Files under `scripts/` must be executable `.py` files with the exact `uv run` shebang and a PEP 723 metadata block
- Relative files referenced from `SKILL.md` must exist
- Packaging excludes caches, hidden files, `.pyc`, `.DS_Store`, and existing `.skill` archives

## Creation Workflow

**Step 1 — Understand:** Get concrete examples of how the skill will be used before building anything.

**Step 2 — Plan contents:** For each example, identify what scripts/references/assets would be reused. Don't build what isn't needed.

**Step 3 — Initialize:**
```bash
uv run ~/.claude/skills/py-skill-creator/scripts/init_skill.py <skill-name> --path <dir>
```
Optional scaffold flags:
- `--no-example-script`
- `--with-references`
- `--with-assets`

Creates a lean `SKILL.md`, `scripts/`, and optional directories.

**Step 4 — Edit:** Implement scripts, references, assets, then write the `SKILL.md` body. See [patterns.md](references/patterns.md) for workflow and output patterns.

**Step 5 — Validate:**
```bash
uv run ~/.claude/skills/py-skill-creator/scripts/validate_skill.py <skill-dir>
```

**Step 6 — Package:**
```bash
uv run ~/.claude/skills/py-skill-creator/scripts/package_skill.py <skill-dir> [output-dir]
```
Creates a `.skill` zip file after validation. Fix validation errors before packaging.

## Script Standard

All scripts bundled in skills must be Python with PEP 723 inline metadata, executed via `uv run`.

**Rules:**
- Python, not bash or shell scripts
- Use this exact shebang: `#!/usr/bin/env -S uv run`
- Declare `requires-python` and `dependencies` in a `# /// script` block
- Make scripts executable: `chmod +x scripts/*.py`
- Reference scripts from `SKILL.md` using relative paths: `uv run scripts/<script>.py`
- `uv run` caches environments in `~/.cache/uv/` — no reinstall on repeated runs

**Script template:**
```python
#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.11"
# dependencies = ["httpx", "rich"]
# ///

import argparse
import httpx
from rich.console import Console

console = Console()

def main():
    parser = argparse.ArgumentParser(description="What this script does")
    parser.add_argument("--arg", required=True, help="Some argument")
    args = parser.parse_args()

    console.print(f"[green]Done:[/green] {args.arg}")

if __name__ == "__main__":
    main()
```

**SKILL.md invocation pattern:**
```bash
uv run scripts/<script>.py --arg value
```

## SKILL.md Authoring

**Concise is key** — the context window is shared. Only include what Claude doesn't already know. Challenge every paragraph.

**Progressive disclosure:**
1. Metadata (`name` + `description`) — always loaded, ~100 words
2. `SKILL.md` body — loaded on trigger, keep under 500 lines
3. Bundled resources — loaded as needed; reference them explicitly from the body

**Structure patterns** (pick what fits, mix as needed):
- **Workflow-based** — numbered steps with decision branches; good for sequential processes
- **Task-based** — sections per operation; good for tool collections with multiple capabilities
- **Reference/guidelines** — specifications or standards; good for coding conventions, brand rules

**When to use `references/` files:** Move detailed content there when the body approaches 500 lines, or when content is only needed for specific sub-tasks. Always link from `SKILL.md` with context on when to read the file.

**Do not create:** `README.md`, `CHANGELOG.md`, `INSTALLATION_GUIDE.md`, or other auxiliary docs inside the distributed skill.
