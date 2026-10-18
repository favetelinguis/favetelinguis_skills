---
name: agents-md-author
description: >-
  Writes or refreshes a project's AGENTS.md from a fixed engineering philosophy:
  modular monolith, Ousterhout deep modules, a pure core modelled with algebraic
  data types and decision tables behind an imperative shell, BDD features first,
  property-based and mutation testing, JSON Schema validation at every boundary,
  and a plan-implement-review workflow. Interviews the human about what the
  project builds, maps every rule onto the project's language and tooling, and
  wires the commands that enforce it. Use when starting a new project or repo,
  or when creating, regenerating, updating, or auditing AGENTS.md or CLAUDE.md,
  agent instructions, coding guidelines, or architecture rules for a codebase.
  Not for writing skills, READMEs, or other documentation.
---

# AGENTS.md author

Produce one self-contained `AGENTS.md` at the project root from
[assets/AGENTS.md.template](assets/AGENTS.md.template). The template's rule text is the human's
canonical preference set: fill placeholders, never reword, soften, reorder, or drop rules.
Every project-specific exception goes under `## Project deviations`, with its reason.

## Workflow

1. **Inspect the project.**
    - Read any existing `AGENTS.md`, `CLAUDE.md`, and README.
    - Read the manifests and workspace configs (`package.json`, `pyproject.toml`, `Cargo.toml`,
      `go.mod`, Gradle, `.csproj`), the CI config, and the top-level layout.
    - Note the language(s), package manager, and the test, lint, and schema tools already in use.
    - An empty repo is a greenfield project: the language is still to be decided.
2. **Interview the human.** Ask in batches and keep asking until each item below is concrete. Never
   fill a gap with a guess or a `TODO`.
    - What the project builds, for whom, and why (`PROJECT_PURPOSE`); scope and non-goals.
    - The deployable unit, such as one binary, service, or CLI.
    - The modules. For each: its responsibility, the design decisions it hides, and its public
      interface in one line. Challenge shallow or overlapping modules now.
    - Every external boundary: environment variables, files, databases, network APIs, model output,
      inbound messages. Note which real services need `@live` tests.
    - The core's branching business rules. Sketch them as decision tables. If any table hits a
      scale signal from the template's "Warn the human" list, warn now and agree an alternative.
    - Language and runtime, if not decided. Existing conventions the human wants to keep.
    - Whether the project has prompt templates for the Plan, Implement, and Review steps.
    - Push back on anything that conflicts with the rules, such as microservices, mocks in the
      core, or code-first schemas. Either the human drops it, or it becomes a recorded deviation.
3. **Map the stack.** Read the language's section in
   [references/stack-tooling.md](references/stack-tooling.md), plus its "Shared conventions"
   section. Prefer tools already in the project when they satisfy the rule. Confirm commands and
   flags with each tool's `--help` or docs.
4. **Draft.** Copy the template to `<project>/AGENTS.md`, or follow "Updating an existing
   AGENTS.md" below. Replace every `{{PLACEHOLDER}}` (see the table below).
5. **Wire enforcement.** Every command and check named in the file must exist and run.
    - List what is missing: dependencies, configs, task scripts, the schema module skeleton, and
      the `.gitignore` entry for generated types.
    - Get the human's approval, then add only that tooling.
    - On a greenfield repo the commands must pass on the empty project.
6. **Validate**, and repeat until there are no errors:

   ```bash
   uv run scripts/check_agents_md.py <project>/AGENTS.md
   ```

    - Errors (a missing heading or an unfilled placeholder) must be fixed.
    - A "canonical rule line changed" warning is acceptable only if that change is listed under
      Project deviations. Otherwise restore the template text.
    - Then run `CMD_CHECK` and `CMD_TEST` once. Report any command you could not run.
7. **Hand off.** Summarise the stack choices, the deviations, any decision-table warnings, and the
   files added. The human reviews and commits; never commit.

## Placeholders

| Placeholder                                                           | Source                                                                                                                                                                                                                  |
|-----------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `PROJECT_NAME`, `PROJECT_PURPOSE`, `SCOPE`, `NON_GOALS`, `DEPLOYABLE` | Interview. Keep the purpose to 2-4 sentences.                                                                                                                                                                           |
| `MODULE_ROWS`                                                         | Interview: one table row per module, each cell one line                                                                                                                                                                 |
| `EXTERNAL_BOUNDARIES`, `LIVE_SERVICES`                                | Interview: a bullet list naming each concrete source; `None.` if there are no live services                                                                                                                             |
| `PROJECT_DEVIATIONS`                                                  | Agreed exceptions as `- rule: reason` bullets, or `None.`                                                                                                                                                               |
| `WORKFLOW_TEMPLATES`                                                  | One line mapping the project's prompt templates to the steps, e.g. ``Prompt templates: `/vibe` (Plan), `/vibe-review` (plan review), `/impl` (Implement), `/impl-review` (Review).`` Delete the line if there are none. |
| `STACK`, `LANGUAGE`, `LAYOUT_TREE`, `CMD_*`                           | Inspection plus the stack map. `LAYOUT_TREE` shows the real dirs with a one-line role each.                                                                                                                             |
| All other placeholders                                                | [references/stack-tooling.md](references/stack-tooling.md), section for the language                                                                                                                                    |

## Updating an existing AGENTS.md

- Regenerate from the current template; do not patch the old file.
- Carry the project facts from the old file into Project and Stack and commands.
- For each old rule that contradicts the template, ask the human: is it a deviation (record it) or
  obsolete (drop it)?
- List the dropped content in the hand-off.

## Gotchas

- The generated `AGENTS.md` must stand alone. Never mention this skill, its template, or its
  references: project agents run without the skill installed.
- This skill acts as planner, not tester or implementer. Write tooling configs only. Write no
  features, steps, property tests, schemas for real data, or implementation code.
- JSON Schema draft 2020-12 is fixed even where the type generator supports less. Keep schemas inside
  the generator's subset and record that as a deviation. Never switch to generating schemas from code.
- Multi-language repo: use one root `AGENTS.md` whose Stack and commands section covers each stack.
  Add a nested `AGENTS.md` only for a subtree with its own toolchain, containing only that subtree's
  Stack and commands.
- If the human also uses Claude Code, add a `CLAUDE.md` containing the single line `@AGENTS.md`,
  so there is one source.
- The rules make the file about 300 lines. Keep the project sections tight. The check script warns
  above 400 lines.
- A rule that tooling cannot enforce in this stack is still a rule. Record the gap under Project
  deviations, and fill its Enforcement cell with "review only".
