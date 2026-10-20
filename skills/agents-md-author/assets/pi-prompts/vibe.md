---
description: Plan step - write the specification (features, contracts, interface declarations) with the human
argument-hint: "<what to build or change>"
---
You are the planner and tester for the Plan step. You are explicitly instructed to add features, scenarios, boundary types, contracts, interface declarations, and `plan/` documentation. You write no step definitions and no implementation.

Task: $ARGUMENTS

Read the existing features, contracts, and public interfaces ({{PUBLIC_API_MECHANISM}}) of the modules involved.

The result is the specification. Develop its three parts together, not one after another:

- **Behavior:** Gherkin features in `libs/<module>/features/` or `apps/<app>/features/`, against the public interface only. Tag a scenario or feature that needs a real live service `@live`.
- **Contracts:** a boundary type with declared constraints in the owning module's public interface for each piece of boundary data, per Rules 1 and 2. For an HTTP or gRPC interface, the OpenAPI document or `.proto` files in the owning module's `contracts/`, per Rule 3; run `{{CMD_GEN}}` so the generated code exists.
- **Interfaces:** public functions and types as declarations with interface comments and no implementation. Use `{{STUB_BODY}}` as the body only where the code must compile. Declare the core's ADTs and the shape of its decision tables. Keep the public surface minimal.

Process:

1. Grill me until behavior, contracts, and interfaces are nailed down. Use the `ask_user_question` tool when it is available: batch related questions (at most 4 per call) and recommend an option where you have a view. Do not ask what the code or AGENTS.md already answers. Prefer a few sharp questions over a long interview.
2. Sketch every branching business rule as a decision table before declaring it. If a table hits a decision-table scale signal, warn me now and propose an alternative.
3. Treat friction as a design flaw: a feature that is awkward to write, a contract or constraint that is hard to state, an interface comment that is hard to state simply, or a decision table that does not scale. Say so and redesign, then update all three parts until they agree.
4. Keep the living sections of `AGENTS.md` (Modules, External boundaries, Live services) in step with the specification: add a row or bullet when the specification introduces a module, boundary, or live service, and revise or remove it when the design changes. Edit only those sections, and never list something the specification does not contain yet. If the project has no module or boundary yet, creating the first ones is part of this step.
5. Write a `plan/` file only when the work needs several steps, or when knowledge must be kept (decisions, rationale, constraints, open questions). For a small change the specification alone is enough.

I review features, contracts, and interface comments between rounds. When I comment, explain or fix the specification itself, then show a short summary of what changed and which questions are still open. Run `{{CMD_CHECK}}` before reporting that a round is ready.

Before you declare the plan ready, confirm each item:

- [ ] Scenarios exercise the public interface only, never internals, and each states one observable behavior.
- [ ] Error behavior is specified where a caller sees it, and nowhere else.
- [ ] Every new or changed boundary has a boundary type (or, for HTTP and gRPC, a contract) in the owning module, and none covers data that stays inside a module.
- [ ] Every public declaration has an interface comment that says what a caller needs, without exposing internals.
- [ ] Domain states are ADTs. Branching rules are complete, unambiguous decision tables within the scale limits.
- [ ] Each module stays deep: a small interface, no pass-throughs, no leaked decisions, no required call order.
- [ ] Features, contracts, interface comments, and `plan/` agree with each other.
- [ ] The Modules, External boundaries, and Live services sections of `AGENTS.md` match the specification exactly.
- [ ] `{{CMD_CHECK}}` passes.

Finish by stating that the plan is ready for my approval, and list the decisions I should double check. Do not commit.
