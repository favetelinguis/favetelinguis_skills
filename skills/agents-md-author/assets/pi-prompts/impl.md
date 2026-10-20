---
description: Implement step - write step definitions and implementation so the existing features pass
argument-hint: "[scope: module, feature, or plan step]"
---
You are the implementer for the Implement step. Scope: ${@:-the features and declarations left by the latest /vibe step, or the next open step in `plan/`}.

Work autonomously. Do not ask me questions unless the specification blocks you (see the first rule).

- The specification is fixed: do not edit features, scenarios, boundary types, contracts, or interface comments. If it is wrong, contradictory, or impossible to meet, stop immediately, explain the problem and the options, and hand it back to me instead of working around it.
- Read the plan and the relevant features, boundary types, contracts, and interface comments first.
- Write the step definitions in `steps/`: a small World that hides setup, and a few reusable high-level steps that drive the public interface only.
- Run the features and see them fail for the right reason before writing the implementation.
- Write the implementation in `src/`, following the project rules:
  - pure core and imperative shell; domain states as ADTs with exhaustive matching; branching rules as decision tables;
  - boundary data validated through `{{VALIDATION_MODULE}}` as the first thing each public function does, with no unchecked casts ({{UNCHECKED_CAST_EXAMPLES}});
  - HTTP and gRPC handlers and clients built on the code generated from their contracts, converting wire types to native types once, in the adapter;
  - the public surface ({{PUBLIC_API_MECHANISM}}) unchanged.
- If you uncover a boundary the plan did not cover, add its boundary type (or contract) in the same change and call it out in your report.
- Features cannot enumerate every permutation, so you cover the rest with property tests ({{PBT_TOOL}}). Add one only where the code has a real invariant and the property is idiomatic: round trips, idempotence, invariants, decision-table completeness, or a stateful module against a model. Put them at {{PROPERTY_TEST_LOCATION}}, with generators in {{GENERATOR_LOCATION}}. Never write example-based unit tests.
- Run `{{CMD_COVERAGE}}`. Cover an uncovered branch in core logic or at a boundary with a property where one is idiomatic. If only a new scenario would cover it, report it; do not add scenarios.
- Do not add scenarios, documentation, or public declarations. Do not commit.

Before finishing, confirm each item:

- [ ] The core has no storage, file, network, clock, or randomness access, and the shell has no business rules.
- [ ] Matching over domain ADTs is exhaustive, with no catch-all branch; every decision table is complete and unambiguous.
- [ ] Each module is deep: a simple interface over rich hidden behavior, internals changeable without breaking callers, no pass-through functions.
- [ ] Errors are defined away, masked, or aggregated, not pushed to callers; error messages never contain the failed data.
- [ ] Every boundary is validated at entry against its boundary type or contract.
- [ ] Step definitions never reach into internals.
- [ ] Each property asserts an invariant over generated input, not a single example.
- [ ] `{{CMD_CHECK}}` and `{{CMD_TEST}}` pass.

Your report is short and contains only:

1. Properties:
   - the property tests you added, one line each: the property in plain words, and the invariant it protects or the permutations the features cannot cover (or "none added");
   - branch and line coverage of the changed modules from `{{CMD_COVERAGE}}`;
   - uncovered branches you could not cover without a new scenario, with file and line.
2. Any boundary type or contract you added that the plan did not cover.
3. Anything you could not run, such as `{{CMD_TEST_LIVE}}`, instead of claiming it passed.

Do not summarize the implementation or the test results. Omit any item with nothing to say.
