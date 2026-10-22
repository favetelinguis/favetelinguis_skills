---
description: Design checkpoint inside a /design session - check the task's specification against its requirements, traceability, and the rules, then refocus
argument-hint: "[what you are worried about]"
---
Checkpoint for the /design session we are in. Focus: ${@:-the whole specification of the task being designed}.

Read-only: do not modify files. Use the goal's Intent and Glossary, the task's requirements in `tasks/`, and this conversation as the record of my intent. Read the current features, contracts, and interface comments; use `git status` and `git diff` to see what changed this session. Run `{{CMD_CHECK}}`.

Report briefly, skipping any section with nothing to say except /impl blockers, which you always report:

1. **Intent:** restate in a few lines what this task is for. Then say where the specification has drifted from the requirements or this conversation, or grown beyond them. Call out places where I changed my mind and older parts of the specification or the task section were not updated.
2. **Traceability and scope:** requirements or Examples rows that no tagged scenario verifies; scenarios this task adds or changes with no requirement tag, or tagged with a requirement that does not exist; behavior the specification adds that no requirement states (a missing requirement to take back to me); names that stray from the Glossary; and a task that has grown past one pull request the team can understand and review in one sitting (name the self-contained part to move into a new `[todo]` task, or say it needs `/specify`).
3. **/impl blockers:** /impl treats the specification as fixed and stops if it is wrong, contradictory, or impossible to meet, or if the code does not fit its module. Find every such case now, as if you had to implement the specification without changing it:
   - contradictions between features, scenarios, boundary types, contracts, interface comments, and the task section, including a scenario whose expected outcome conflicts with a constraint, an interface comment, or a decision-table row;
   - specification that conflicts with the project rules, so /impl could not satisfy both (for example behavior that needs storage, network, clock, or randomness inside the core, an error that must echo the failed data, or a scenario only checkable through internals);
   - anything /impl would need but may not add: a missing public declaration, ADT case, or boundary type the scenarios rely on; a step that needs an interface the module does not expose; a module dependency the `Depends on` column does not list; code with no module that fits it;
   - decision tables that are incomplete, ambiguous, or past the scale limits, and ADTs whose cases do not match the states the scenarios exercise;
   - `{{CMD_CHECK}}` failing, or contracts whose generated code does not exist.
   For each blocker, name the files involved by path and the decision needed. If there are none, say "No /impl blockers found."
4. **Rule breaks:** anything that breaks the project rules, in particular:
   - features that test internals, or weak scenarios that would pass with a wrong implementation;
   - boundary data without a boundary type or contract, one owned by the wrong module, one for data that stays inside a module, a hand-written JSON Schema, or an HTTP or gRPC interface without a contract-first OpenAPI document or `.proto`;
   - interface comments that restate code or hide what a caller must know;
   - a widened public surface ({{PUBLIC_API_MECHANISM}});
   - domain states as flags or optional fields instead of ADTs, or a decision table that is incomplete, ambiguous, or past the scale limits.
5. **Design pitfalls:** module structure that breaks the Module structure rules (a premature split with no signal, a module per entity or layer, a shared types or helpers module, a module that has outgrown one responsibility, a dependency that points the wrong way or closes a cycle, domain logic in `apps/`); shallow modules, pass-throughs, leaked decisions, temporal coupling, errors pushed to callers, business rules that would land in the shell, or an interface that is hard to describe simply. Suggest the simpler shape.
6. **Gaps and risks:** Modules, External boundaries, or Live services in `AGENTS.md` that no longer match the specification; unspecified error behavior at the boundary, unhandled edge cases, and things that will be hard to implement, test with properties, or change later.
7. **Next:** the 2 to 4 most valuable things to resolve before this task is ready for /impl, /impl blockers first, as concrete questions or edits. Ask the ones that need my decision with the `ask_user_question` tool when it is available.

Be direct and prioritised; a long list of nits hides the real problems. Do not start fixing anything: I will decide and continue experimenting.
