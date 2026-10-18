# Purpose

Personal, harness-agnostic skill repository. Every skill follows the open
[Agent Skills](https://agentskills.io/specification) format so it works in any
harness that supports it (Pi, Codex, Claude Code, Cursor, Gemini CLI, Copilot, ...).
Nothing in a skill may depend on one harness.

# Repository layout

```
skills/<skill-name>/      one directory per skill; this is the only thing installed
  SKILL.md                required: frontmatter + instructions
  scripts/                optional: executable code the agent runs
  references/             optional: docs the agent reads on demand
  assets/                 optional: templates/files used in output
scripts/install.py        symlinks skills/* into the harness skill directories
templates/SKILL.md.template   starting point for a new skill (outside skills/ so it is never discovered)
AGENTS.md                 this file
```

- Skills are flat under `skills/`. Do not nest skills inside skills or group them in
  subdirectories: discovery scanners look for `<dir>/SKILL.md` at a fixed depth and
  nested layouts are not portable.
- Only `skills/` is installed. Never put a `SKILL.md` anywhere else in the repo
  (templates, docs, examples), or scanners such as `npx skills add` may pick it up.
- Do not add `README.md`, `CHANGELOG.md`, or install guides inside a skill. A skill
  contains only what the agent needs to do the job.

# Discovery and installation

Skill format is standardized; install location is not. The convention used here:

| Location                       | Read by                                                   |
| ------------------------------ | --------------------------------------------------------- |
| `~/.agents/skills/`            | Pi, Codex, Cline, Zed, Warp, and most others (user scope) |
| `.agents/skills/` in a project | Nearly all harnesses (project scope)                      |
| `~/.claude/skills/`            | Claude Code only (it does not read `.agents/skills`)      |

- Install with `uv run scripts/install.py` (use `--dry-run` first). It symlinks each
  `skills/<name>` into `~/.agents/skills` and `~/.claude/skills`, so edits are live,
  and prunes links to skills that no longer exist. It never overwrites real directories.
- Do not copy skills into harness directories. Copies drift; symlinks keep this repo the
  single source of truth.
- Do not install into harness-specific directories other than the two above unless a
  harness cannot read `~/.agents/skills`; add that target to `install.py` instead of
  doing it by hand.
- Precedence: project-level skills override user-level skills of the same `name`.
  Keep names distinctive so a personal skill never silently shadows, or is shadowed by,
  a project skill.
- Alternative installers (`npx skills add ./ -g`) work with this layout, but check where
  they write; some use `~/.config/agents/skills` as the "universal" global path.

# Skill architecture

## Frontmatter

Only two fields are used. They are the portable subset; other fields (`allowed-tools`,
`compatibility`, `metadata`, harness-specific keys like `disable-model-invocation`) are
not portable and must not be relied on.

```yaml
---
name: pdf-processing # must equal the directory name
description: >-
  Extracts text and tables from PDF files, fills forms, merges documents.
  Use when working with PDF files or when the user mentions PDFs, forms, or extraction.
---
```

- `name`: lowercase letters, digits, hyphens; 1-64 chars; no leading/trailing/double
  hyphen; identical to the directory name.
- `description`: at most 1024 chars, no angle brackets. It is the only text the agent
  sees before deciding to load the skill, so it is the trigger.
  - Say what the skill does AND when to use it. Put the "use when" triggers in it; a
    "when to use" section in the body is never seen before activation.
  - Write in third person ("Extracts...", not "I can..." or "You can...").
  - Name concrete triggers: file types, tools, task verbs, phrases a user would say.
  - Be specific enough not to fire on unrelated tasks, broad enough to fire on related
    ones. Avoid vague descriptions like "helps with documents".

## Progressive disclosure

Skills are loaded in three tiers; design for them. Context is shared and expensive.

1. Metadata (`name` + `description`): always in context, about 50-100 tokens per skill.
2. `SKILL.md` body: loaded when the skill triggers. Keep under 500 lines / ~5000 tokens.
3. `scripts/`, `references/`, `assets/`: loaded or run only when the body tells the agent to.

Rules:

- Include only what the agent does not already know. Challenge every paragraph: does the
  agent need this, and does it justify its tokens?
- Split by topic into `references/` when the body nears 500 lines or content is only
  needed for some tasks. Name each file by topic (`references/api-errors.md`), not by
  position.
- Tell the agent when to read each reference: "Read `references/api-errors.md` if the API
  returns a non-200 status", not "see references/".
- Keep references one level deep: link them from `SKILL.md`, never from another
  reference. Long references (>100 lines) start with a short table of contents.
- Use relative paths from the skill root (`scripts/extract.py`, `references/x.md`).
  Never use absolute paths or harness-specific paths (`~/.claude/...`, `~/.pi/...`):
  the skill is reached through different symlinked locations in different harnesses.

## Writing the body

- Imperative, direct instructions. Prefer procedures and checklists over prose.
- Match specificity to fragility: high freedom (guidance) where many approaches work,
  exact commands and fixed order where operations are fragile or order matters.
- Give one default approach, not a menu of equal options; mention an alternative only
  as an explicit escape hatch.
- Put gotchas (non-obvious facts the agent would get wrong) and validation steps
  (a check to run, then fix and re-check) in the body. These carry the most value.
- Use templates in `assets/` for output formats the agent must reproduce exactly.
- Be consistent: one term per concept throughout.
- No time-sensitive information ("before 2026 use X"); keep a clearly labelled "old
  approach" section if history matters.
- Do not reference tools by one harness's name. Describe the capability ("read the
  file", "run the command") unless a tool is genuinely required.

## Scripts

- Bundled scripts are Python with PEP 723 inline metadata, run with `uv run`:
  shebang `#!/usr/bin/env -S uv run`, a `# /// script` block declaring
  `requires-python` and `dependencies`, executable bit set. Not bash, not bare `python3`.
- Invoke from `SKILL.md` with a relative path: `uv run scripts/<name>.py --arg value`.
- Non-interactive only: no prompts, no TTY assumptions. Take input via arguments, flags,
  or stdin.
- Provide `--help`. Print structured, concise output (JSON or short lines) to stdout and
  diagnostics to stderr. Exit non-zero on failure with an actionable message.
- Make them safe to re-run (idempotent) and support `--dry-run` for destructive ones.
- Say in `SKILL.md` whether the agent should run the script or read it as reference.
- Scripts the skill cannot work without live in the skill; one-off repo tooling lives in
  top-level `scripts/`, not in a skill.

## Scope

- One skill = one coherent job. Split when a skill covers unrelated triggers; merge when
  two skills are always loaded together.
- Skills hold reusable procedure and knowledge. Project-specific facts belong in that
  project's `AGENTS.md` or its own `.agents/skills/`, not here.
- Never store secrets, tokens, or machine-specific absolute paths in a skill.

# Workflow

1. Create: use the `py-skill-creator` skill, or copy `templates/SKILL.md.template` to
   `skills/<name>/SKILL.md`.
2. Write the `description` first, then the body, then add scripts/references only where
   the body needs them.
3. Validate every changed skill before committing:
   `uv run skills/py-skill-creator/scripts/validate_skill.py skills/<name>`
4. Install or refresh links: `uv run scripts/install.py`.
5. Test in at least two harnesses: confirm the skill appears in the catalog and triggers
   on a realistic prompt, and that it does not trigger on an unrelated one. Iterate on the
   `description` based on misfires.
6. Commit. Renaming or deleting a skill: rerun `install.py` to prune dangling links.

# Guardrails

- Do not add harness-specific files or directories (`.claude-plugin/`, `.cursor/`, ...) unless
  explicitly asked; they are a second packaging path to maintain.
- Do not change a skill's `name` casually; it is its identity across harnesses and in
  users' muscle memory. Rename = change the directory and `name` together, then reinstall.
- Do not weaken a validation rule to make a skill pass; fix the skill.
