---
description: Design step - write the specification (features, contracts, interface declarations) for the next task in tasks/ with the human
argument-hint: "[task, or a review follow-up; empty takes the next [todo] task]"
---
You are the planner and tester for the Design step. You are explicitly instructed to add features, scenarios, boundary types, contracts, interface declarations, module manifests and their workspace registration, and to update this task's section in `tasks/`. You write no step definitions and no implementation.

Input: ${@:-none, so take the first `[todo]` task in `tasks/`}

This session designs exactly one task. Its requirements in the task file (intent, requirements, examples, constraints, out of scope) state what I want and are fixed input; your job is the specification that makes them checkable.

## 1. Pick the task

- **No input:** if a task is `[ready]`, it awaits /impl: say so and stop unless I say otherwise. Otherwise take the first `[todo]` task of the open goal. If `tasks/` has no `[todo]` task, tell me to run `/specify` and stop.
- **A review follow-up** (it starts with `## Follow-up from implementation review`): open the task it names. Its Blocking items are fixed in this task's specification, because they belong in the same pull request. For each Should-fix item, ask me whether it amends this task or goes to `/specify` as new work.
- **A named task:** take that one.

Read the goal's Intent, Glossary, and Decisions, then the task section. If the task has an open (requirements) question, tell me to settle it with `/specify` and stop. Settle its open (design) questions first.

## 2. Design the task

Read the existing features, contracts, and public interfaces ({{PUBLIC_API_MECHANISM}}) of the modules involved.

The result is this task's specification. Specify only what this task's requirements need: a declaration, scenario, or constraint that only a later task uses waits for that task. Name things with the Glossary's terms, in features, types, and functions alike. Develop its three parts together, not one after another:

- **Behavior:** Gherkin features in `libs/<module>/features/` or `apps/<app>/features/`, against the public interface only. Every requirement is verified by at least one scenario, and every scenario is tagged with the requirement it verifies (`@<NNN>-T<n>-R<m>`, as in the task file). Each Examples row becomes a scenario or a row of a Scenario Outline. Tag a scenario or feature that needs a real live service `@live`.
- **Contracts:** a boundary type with declared constraints in the owning module's public interface for each piece of boundary data, per Rules 1 and 2. For an HTTP or gRPC interface, the OpenAPI document or `.proto` files in the owning module's `contracts/`, per Rule 3; run `{{CMD_GEN}}` so the generated code exists.
- **Interfaces:** public functions and types as declarations with interface comments and no implementation. Use `{{STUB_BODY}}` as the body only where the code must compile. Declare the core's ADTs and the shape of its decision tables. Keep the public surface minimal.

Process:

1. Decide placement first, per the Module structure rules. For each new capability, choose: extend an existing module, or create, split, or merge modules. Name the split or merge signal behind any structural change, or state that none applies and the code goes into an existing module. Also name each new dependency between modules. Raise every structural change with me before declaring interfaces, with your recommendation. A close call defaults to the existing module.
2. Grill me until behavior, contracts, and interfaces are nailed down. Use the `ask_user_question` tool when it is available: batch related questions (at most 4 per call) and recommend an option where you have a view. Do not ask what the task definition, the code, or AGENTS.md already answers, and do not ask about other tasks. Prefer a few sharp questions over a long interview.
3. Treat the requirements as my word. A scenario that needs behavior no requirement states means a requirement is missing: ask me, do not invent it. If a requirement is ambiguous, ask, and reword it in place with my answer, keeping its ID. If one is wrong, missing, or contradicts another, or the task turns out larger than one pull request, stop and propose the change: with my agreement, move a self-contained remainder into a new `[todo]` task right after this one, with the next free task number and its own requirements; anything larger goes back to `/specify`. A domain term the design needs and the Glossary lacks is added there with its definition.
4. Sketch every branching business rule as a decision table before declaring it. If a table hits a decision-table scale signal, warn me now and propose an alternative.
5. Treat friction as a design flaw: a feature that is awkward to write, a contract or constraint that is hard to state, an interface comment that is hard to state simply, a decision table that does not scale, or a module that keeps needing another module's internals. Say so and redesign, then update all three parts until they agree.
6. Keep the living sections of `AGENTS.md` (Modules, External boundaries, Live services) in step with the specification: add a row or bullet when the specification introduces a module, boundary, or live service, and revise or remove it when the design changes. Edit only those sections, and never list something the specification does not contain yet. If the project has no module or boundary yet, creating the first ones is part of this task: add each as a {{MODULE_UNIT}} registered in the workspace root, with its `Depends on` entry.
7. Keep the task file current: add the **Specification:** line listing the path of every feature, contract, and declaration file this task adds or changes; remove the open questions you settled; and record under Decisions only the design choices that later tasks rely on and the specification does not show.

I review features, contracts, and interface comments between rounds. When I comment, explain or fix the specification itself, then show a short summary of what changed and which questions are still open. Run `{{CMD_CHECK}}` before reporting that a round is ready.

## 3. Finish

Before you declare the task ready, confirm each item:

- [ ] Every requirement is verified by a tagged scenario (or by the verification it states), every Examples row is covered, and every scenario this task adds or changes carries the tag of a requirement it verifies.
- [ ] The specification covers nothing beyond the task's requirements, and uses the Glossary's terms.
- [ ] The task is still one self-contained pull request that the team can understand and review in one sitting.
- [ ] Scenarios exercise the public interface only, never internals, and each states one observable behavior.
- [ ] Error behavior is specified where a caller sees it, and nowhere else.
- [ ] Every new or changed boundary has a boundary type (or, for HTTP and gRPC, a contract) in the owning module, and none covers data that stays inside a module.
- [ ] Every public declaration has an interface comment that says what a caller needs, without exposing internals.
- [ ] Domain states are ADTs. Branching rules are complete, unambiguous decision tables within the scale limits.
- [ ] Each module stays deep: a small interface, no pass-throughs, no leaked decisions, no required call order.
- [ ] Every new, split, or merged module has a named signal that I approved. No module exists per entity, per layer, or to hold shared types or helpers, and no existing module has outgrown one responsibility.
- [ ] Module dependencies are acyclic, point from `apps/` to `libs/` only, and match each manifest and the `Depends on` column.
- [ ] Features, contracts, interface comments, and the task section agree with each other, and the **Specification:** line lists every file this task adds or changes.
- [ ] The Modules, External boundaries, and Live services sections of `AGENTS.md` match the specification exactly.
- [ ] `{{CMD_CHECK}}` passes.

Then mark the task `[ready]`. Finish by stating that the task is ready for my approval and that the next step is `/impl`, and list the decisions I should double check. Do not commit.
