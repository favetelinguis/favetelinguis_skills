---
name: specify-design-impl-review
description: >-
  Installs, updates, or removes the user's global, language-agnostic
  specify-design-implement-review workflow for pi and Codex: five
  workflow commands (specify, design, design-review, impl, impl-review) and a short
  engineering-practices section in each harness's global AGENTS.md. Task
  files live outside the repository, keyed by repo and worktree. Use when the user
  asks to install, reinstall, update, sync, or uninstall the workflow, its slash
  commands or prompts, or the global agent instructions, or after the workflow's
  step files were edited. Not for writing a project's own AGENTS.md.
---

# Workflow installer

The workflow is the user's, the project standards are not. Each project's own
`AGENTS.md`/`CLAUDE.md` and code decide language, design, and code standards; this skill
installs only project-agnostic practice:

| Step            | pi                | Codex              | Does                                                                    |
|-----------------|-------------------|--------------------|-------------------------------------------------------------------------|
| `specify`       | `/specify`        | `$wf-specify`      | Interview, cut the goal into PR-sized tasks, write EARS requirements    |
| `design`        | `/design`         | `$wf-design`       | Sketch in the source tree: outlined tests, bodiless types and functions with `SKETCH:` requirement comments |
| `design-review` | `/design-review`  | `$wf-design-review`| Read-only checkpoint inside a design session                            |
| `impl`          | `/impl`           | `$wf-impl`         | Best-effort implementation from the sketch; strips `SKETCH:` comments   |
| `impl-review`   | `/impl-review`    | `$wf-impl-review`  | Simplify, align with the project, check placement, docs, tests; close   |

Sources, all in `assets/`:

- `steps/<step>.md`: one file per step: frontmatter (`description`, `argument-hint`) and body.
- `task-files.md`: the shared task-file location and status rules, spliced into every step.
- `global-instructions.md`: the sections merged into each global instructions file. The
  installer owns each top-level heading in it, and only those: a section with the same
  heading line is updated in place, a missing one is appended, and every other line of the
  file is left untouched. Content the user adds under an owned heading is overwritten.

Placeholders in step files, filled per harness by the installer: `{{INPUT}}` (the user's
argument), `{{TASK_FILES}}` (the shared partial), `{{CMD:<step>}}` (a reference to another
step). Any other `{{...}}` is an error.

## Install or update

1. Preview: `uv run scripts/install.py --dry-run`
2. Resolve every `CONFLICT` line with the user: an existing file the installer did not
   write. Keep theirs (rename it, or install with `--harness` for the other harnesses), or
   overwrite with `--force` once they agree.
3. Apply: `uv run scripts/install.py`. Exit 0 with no `CONFLICT` lines is success.
4. Re-run with `--dry-run`: the summary must show `0 written`.
5. Hand off: list the files written, and tell the user to reload (`/reload` in pi, restart
   Codex).

Without `--harness`, only harnesses whose config directory exists are processed. Remove
with `uv run scripts/install.py --uninstall`; it deletes only files the installer
wrote (tracked in its manifest) and removes the owned sections.

## Editing the workflow

- Edit the assets, never the installed copies; the next run overwrites them.
- Keep steps language-agnostic: name the capability ("the project's check command", "the
  test framework's pending marker"), never a language, tool, or file layout.
- Keep the global sections short. They are loaded in every session of every project;
  procedures belong in step files.
- Renaming an owned heading orphans the old section in already-installed files; remove it
  there by hand.
- A step refers to another step only through `{{CMD:<step>}}`, never `/design` literally:
  Codex invokes them as `$wf-<step>`.
- Pi substitutes `$1`, `$@`, and `$ARGUMENTS` anywhere in a prompt body. Never use them in
  step text or shell snippets, except through `{{INPUT}}`.
- Renaming or deleting a step file: re-run the installer; it prunes the old outputs.

## Gotchas

- Codex no longer reads custom prompts, so its steps are skills in `~/.agents/skills/wf-*`
  with `agents/openai.yaml` disabling implicit invocation. Pi also scans that directory: it
  sees them as `/skill:wf-*`, hidden from the model by `disable-model-invocation`. That
  duplicate is expected.
- Project-level prompts shadow the global ones: an old `.pi/prompts/design.md` in a
  project wins. Offer to delete those when the user
  reports old step behavior.
- Task files live in `${XDG_STATE_HOME:-~/.local/state}/agent-workflow/<repo>/`. Two repos
  whose main worktree directories share a name share that directory.
