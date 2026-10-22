---
description: Plan checkpoint inside a /vibe session - check the spec against intent and the rules, then refocus
argument-hint: "[what you are worried about]"
---
Checkpoint for the /vibe session we are in. Focus: ${@:-the whole current specification}.

Read-only: do not modify files. Use this conversation as the record of my intent. Read the current features, contracts, interface comments, and `plan/` files; use `git status` and `git diff` to see what changed this session. Run `{{CMD_CHECK}}`.

Report briefly, skipping any section with nothing to say except /impl blockers, which you always report:

1. **Intent:** restate in a few lines what I am trying to achieve. Then say where the specification has drifted from it, grown beyond it, or left part of it uncovered. Call out places where I changed my mind and older parts of the specification were not updated.
2. **/impl blockers:** /impl treats the specification as fixed and stops if it is wrong, contradictory, or impossible to meet, or if the code does not fit its module. Find every such case now, as if you had to implement the specification without changing it:
   - contradictions between features, scenarios, boundary types, contracts, interface comments, and `plan/`, including a scenario whose expected outcome conflicts with a constraint, an interface comment, or a decision-table row;
   - specification that conflicts with the project rules, so /impl could not satisfy both (for example behavior that needs storage, network, clock, or randomness inside the core, an error that must echo the failed data, or a scenario only checkable through internals);
   - anything /impl would need but may not add: a missing public declaration, ADT case, or boundary type the scenarios rely on; a step that needs an interface the module does not expose; a module dependency the `Depends on` column does not list; code with no module that fits it;
   - decision tables that are incomplete, ambiguous, or past the scale limits, and ADTs whose cases do not match the states the scenarios exercise;
   - `{{CMD_CHECK}}` failing, or contracts whose generated code does not exist.
   For each blocker, name the files involved by path and the decision needed. If there are none, say "No /impl blockers found."
3. **Rule breaks:** anything that breaks the project rules, in particular:
   - features that test internals, or weak scenarios that would pass with a wrong implementation;
   - boundary data without a boundary type or contract, one owned by the wrong module, one for data that stays inside a module, a hand-written JSON Schema, or an HTTP or gRPC interface without a contract-first OpenAPI document or `.proto`;
   - interface comments that restate code or hide what a caller must know;
   - a widened public surface ({{PUBLIC_API_MECHANISM}});
   - domain states as flags or optional fields instead of ADTs, or a decision table that is incomplete, ambiguous, or past the scale limits.
4. **Design pitfalls:** module structure that breaks the Module structure rules (a premature split with no signal, a module per entity or layer, a shared types or helpers module, a module that has outgrown one responsibility, a dependency that points the wrong way or closes a cycle, domain logic in `apps/`); shallow modules, pass-throughs, leaked decisions, temporal coupling, errors pushed to callers, business rules that would land in the shell, or an interface that is hard to describe simply. Suggest the simpler shape.
5. **Gaps and risks:** Modules, External boundaries, or Live services in `AGENTS.md` that no longer match the specification; unspecified error behavior at the boundary, unhandled edge cases, and things that will be hard to implement, test with properties, or change later.
6. **Next:** the 2 to 4 most valuable things to resolve before this is ready for /impl, /impl blockers first, as concrete questions or edits. Ask the ones that need my decision with the `ask_user_question` tool when it is available.

Be direct and prioritised; a long list of nits hides the real problems. Do not start fixing anything: I will decide and continue experimenting.
