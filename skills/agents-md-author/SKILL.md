---
name: agents-md-author
description: >-
  Writes or refreshes a project's AGENTS.md from a fixed engineering philosophy:
  modular monolith, Ousterhout deep modules, a pure core of algebraic data types
  and decision tables behind an imperative shell, BDD features first,
  property tests, mutation testing in CI, native-type validation at internal
  boundaries (typia, Jakarta Bean Validation), contract-first OpenAPI and
  protobuf for HTTP and gRPC, and a plan-implement-review workflow. Interviews
  the human about the project's purpose and its TypeScript or Java stack, maps
  every rule onto that tooling, wires the enforcing commands, and installs
  project-local pi prompt templates (/vibe, /vibe-review, /impl, /impl-review).
  Works from a rough idea; modules are discovered later through /vibe. Use when
  starting a new project or repo, or when creating, regenerating, updating, or
  auditing AGENTS.md or CLAUDE.md, agent instructions, coding guidelines,
  architecture rules, or the workflow prompt templates for a codebase.
  Not for skills, READMEs, or other documentation.
---

# AGENTS.md author

Produce two things for the project, both from `assets/`:

- `AGENTS.md` at the project root, from [assets/AGENTS.md.template](assets/AGENTS.md.template):
  the rules every agent session needs (architecture, design, testing, validation, commands).
- Four pi prompt templates in `<project>/.pi/prompts/`, from `assets/pi-prompts/`: the human's
  workflow, one per step, each with that step's procedure and checklist.

| Prompt template  | Step                                         | Session                 |
|------------------|----------------------------------------------|-------------------------|
| `vibe.md`        | Plan: write the specification with the human | fresh                   |
| `vibe-review.md` | Read-only checkpoint of the plan             | inside the `/vibe` one  |
| `impl.md`        | Implement against the fixed specification    | fresh                   |
| `impl-review.md` | Review, fix easy issues, hand off to `/vibe` | fresh                   |

The split keeps `AGENTS.md` thin: agents need the rules, not the workflow the human drives.
Rules live only in `AGENTS.md` (pi always loads it); procedures and checklists live only in the
prompt templates. The asset text is the human's canonical preference set: fill placeholders,
never reword, soften, reorder, or drop rules or checklist items. Every project-specific exception
goes under `## Project deviations` in `AGENTS.md`, with its reason.

## Workflow

1. **Inspect the project.**
    - Read any existing `AGENTS.md`, `CLAUDE.md`, and README.
    - Read the manifests and workspace configs (`package.json`, `pnpm-workspace.yaml`, Gradle,
      `module-info.java`), the CI config, and the top-level layout.
    - Note the language(s), package manager, and the test, lint, validation, and contract tools
      already in use, and any HTTP or gRPC interface the project serves or calls.
    - An empty repo is a greenfield project: the language is still to be decided.
2. **Interview the human, briefly.** This skill runs first, before the human has explored the
   problem. Ask only for what the human can know today, and accept rough answers. The modules,
   boundaries, and business rules are not an input: they are discovered later, in `/vibe` sessions.
    - What the project is for, and for whom (`PROJECT_PURPOSE`). Scope and non-goals only as far as
      they are known; a rough or partial statement is fine.
    - Language and runtime, if not decided: TypeScript or Java (Kotlin allowed). Any other
      language uses the fallback section of the stack map, with every gap recorded as a deviation.
      Existing conventions the human wants to keep.
    - The deployable unit, defaulting to one binary, service, or CLI. Confirm rather than ask.
    - Any existing `.pi/prompts/` files. Same-named ones are replaced; ask whether others stay.
    - Modules, boundaries, live services, or business rules, **only if the human volunteers them**
      or the repo already contains them. Record those as seeds. Do not ask for the full list, do not
      press for completeness, and do not design modules for them.
    - Push back only on what conflicts with the rules today (microservices, mocks in the core,
      hand-written JSON Schema for internal data, code-first OpenAPI). Either the human drops it,
      or it becomes a recorded deviation.
    - Never fill a gap with a guess or a `TODO`. An unknown that belongs to later discovery is
      written as "none yet" (see Placeholders), not invented.
3. **Map the stack.** Read the language's section in
   [references/stack-tooling.md](references/stack-tooling.md), plus its "Shared conventions"
   section. Prefer tools already in the project when they satisfy the rule. Confirm commands and
   flags with each tool's `--help` or docs.
4. **Draft.** Copy the template to `<project>/AGENTS.md`, or follow "Updating an existing
   AGENTS.md" below. Copy each `assets/pi-prompts/<name>.md` to `<project>/.pi/prompts/<name>.md`.
   Replace every `{{PLACEHOLDER}}` in all five files (see the table below). Leave the living
   sections empty when nothing is known yet.
5. **Wire enforcement.** Every command and check named in the file must exist and run.
    - List what is missing: dependencies, configs, task scripts, the validation module skeleton
      (`VALIDATION_MODULE`), the validator setup (the typia transform for TypeScript), a `CMD_GEN`
      that is a no-op until contracts exist, `CMD_COVERAGE`, the mutation testing job in the CI
      config, and the `.gitignore` entry for generated code.
    - Get the human's approval, then add only that tooling.
    - On a greenfield repo the commands must pass on the empty project, with no modules yet. Create
      only the shared validation module skeleton and tooling configs, never a placeholder feature module.
6. **Validate**, and repeat until there are no errors:

   ```bash
   uv run scripts/check_agents_md.py <project>/AGENTS.md
   ```

    - It checks `AGENTS.md` and `<project>/.pi/prompts/` together.
    - Errors (a missing heading, a missing prompt template, or an unfilled placeholder) must be fixed.
    - A "canonical line changed" warning is acceptable only if that change is listed under
      Project deviations. Otherwise restore the template text.
    - Then run `CMD_CHECK` and `CMD_TEST` once. Report any command you could not run.
7. **Hand off.** Summarise the stack choices, the deviations, any decision-table warnings, and the
   files added. State which living sections (Modules, External boundaries) are empty and that
   `/vibe` fills them in as the design emerges. Tell the human to run `/reload` (or restart pi) and trust the project so the
   prompt templates load. The human reviews and commits; never commit.

## Placeholders

| Placeholder                                                           | Source                                                                                                                                                                                                                  |
|-----------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `PROJECT_NAME`, `PROJECT_PURPOSE`, `SCOPE`, `NON_GOALS`, `DEPLOYABLE` | Interview. Keep the purpose to 2-4 sentences. Scope and non-goals may be `Not yet decided.`                                                                                                                                                                           |
| `MODULE_ROWS`                                                         | Only modules that already exist in the repo or that the human named: one row each, cells one line. Otherwise exactly one row: `\| _none yet_ \| _added by the Plan step_ \| _n/a_ \|`                                      |
| `EXTERNAL_BOUNDARIES`, `LIVE_SERVICES`                                | Only sources already in the repo or named by the human, as bullets. Otherwise `None yet.` for both                                                                                                                      |
| `PROJECT_DEVIATIONS`                                                  | Agreed exceptions as `- rule: reason` bullets, or `None.`                                                                                                                                                               |
| `STACK`, `LANGUAGE`, `LAYOUT_TREE`, `CMD_*`                           | Inspection plus the stack map. `LAYOUT_TREE` shows the real dirs with a one-line role each.                                                                                                                             |
| All other placeholders, including `STUB_BODY`                         | [references/stack-tooling.md](references/stack-tooling.md), section for the language                                                                                                                                    |

## Updating an existing AGENTS.md

- Regenerate from the current template; do not patch the old file.
- Carry the project facts from the old file into Project and Stack and commands, including every
  existing row of Modules and External boundaries. Never drop a living-section entry; the Plan
  step owns removals.
- Regenerate the four prompt templates the same way. Old workflow text in `AGENTS.md` (step
  procedures, checklists, report formats) is now covered by the prompt templates; drop it.
- For each old rule that contradicts the template, ask the human: is it a deviation (record it) or
  obsolete (drop it)?
- List the dropped content in the hand-off.

## Gotchas

- The generated files must stand alone. Never mention this skill, its assets, or its references:
  project agents run without the skill installed.
- Never copy rules into a prompt template. Pi puts `AGENTS.md` in every session's context, so a
  template names the rule it relies on ("Rules 1 and 2", "the scale signals") and never tells the
  agent to read `AGENTS.md`. Workflow-only text (step procedures, checklists, report and handoff
  formats) goes in the prompt templates, never in `AGENTS.md`.
- Prompt templates use pi argument syntax (`$ARGUMENTS`, `${@:-default}`). It is not a
  placeholder: leave it untouched. Pi loads only direct `.md` children of `.pi/prompts/`.
- The prompt templates are pi-specific. If the human drives another harness, ask where its
  project commands live (Claude Code: `.claude/commands/`), copy them there too, and rewrite only
  the argument syntax for that harness.
- Do not design the architecture here. An empty Modules table is correct on day one; a table
  invented from guesses is a defect, because later steps treat it as the specification's record.
- This skill acts as planner, not tester or implementer. Write tooling configs only. Write no
  features, steps, property tests, boundary types or contracts for real data, or implementation code.
- Internal boundaries are native types with declared constraints, never JSON Schema files. Where a
  library needs a JSON Schema (model tool definitions), it is derived from the native type.
- HTTP and gRPC are contract-first: the OpenAPI document or `.proto` is the source and code is
  generated from it. Never switch to generating the contract from code. A project with no HTTP or
  gRPC interface still gets Rule 3; it applies once `/vibe` adds one.
- Multi-language repo: use one root `AGENTS.md` whose Stack and commands section covers each stack.
  Add a nested `AGENTS.md` only for a subtree with its own toolchain, containing only that subtree's
  Stack and commands.
- If the human also uses Claude Code, add a `CLAUDE.md` containing the single line `@AGENTS.md`,
  so there is one source.
- The rules make `AGENTS.md` about 280 lines. Keep the project sections tight. The check script warns
  above 400 lines.
- A rule that tooling cannot enforce in this stack is still a rule. Record the gap under Project
  deviations, and fill its Enforcement cell with "review only".
