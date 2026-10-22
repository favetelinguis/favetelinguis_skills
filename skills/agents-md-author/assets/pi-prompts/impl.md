---
description: Implement step - write step definitions and implementation so the ready task's features pass
argument-hint: "[task file and task number, default: the [ready] task in tasks/]"
---
You are the implementer for the Implement step. Scope: ${@:-the task marked `[ready]` in `tasks/`}. If no task is `[ready]`, or more than one is, stop and ask me which one.

Work autonomously. Do not ask me questions unless the specification blocks you (see the first rule).

- The specification is fixed: do not edit features, scenarios, boundary types, contracts, or interface comments. If it is wrong, contradictory, or impossible to meet, stop immediately, explain the problem and the options, and hand it back to me instead of working around it.
- Read the goal's Glossary and the task section first (intent, requirements, examples, and the **Specification:** line), then the features, boundary types, contracts, and interface comments it lists. The requirements tell you what the scenarios are for; the specification stays the contract you implement.
- Implement this task only. The result is one pull request; work that belongs to a later task stays out, even when it is easy. Do not edit `tasks/`.
- Write the step definitions in `steps/`: a small World that hides setup, and a few reusable high-level steps that drive the public interface only.
- Run the features and see them fail for the right reason before writing the implementation.
- Write the implementation in `src/`, following the project rules:
  - pure core in the module's `{{CORE_DIR}}`, imperative shell outside it; domain states as ADTs with exhaustive matching; branching rules as decision tables;
  - boundary data validated through `{{VALIDATION_MODULE}}` as the first thing each public function does, with no unchecked casts ({{UNCHECKED_CAST_EXAMPLES}});
  - HTTP and gRPC handlers and clients built on the code generated from their contracts, converting wire types to native types once, in the adapter;
  - the public surface ({{PUBLIC_API_MECHANISM}}) unchanged.
- If you uncover a boundary the task did not cover, add its boundary type (or contract) in the same change and call it out in your report.
- Features cannot enumerate every permutation, so you cover the rest with property tests ({{PBT_TOOL}}). Add one only where the code has a real invariant and the property is idiomatic: round trips, idempotence, invariants, decision-table completeness, or a stateful module against a model. Put them at {{PROPERTY_TEST_LOCATION}}, with generators in {{GENERATOR_LOCATION}}. Never write example-based unit tests.
- Run `{{CMD_MUTATION}}` on the changed modules (it mutates only the core and runs only property tests). Kill a surviving mutant by strengthening a property. If only a new scenario would kill it, report it; do not add scenarios.
- Do not add scenarios, documentation, or public declarations. Do not create, split, or merge modules, and do not add a dependency between modules that the `Depends on` column does not list. If the code does not fit its module, stop and hand it back to me as a structure question.
- Do not commit.

Before finishing, confirm each item:

- [ ] Each module's core lives in its `{{CORE_DIR}}` and has no storage, file, network, clock, or randomness access; the shell has no business rules.
- [ ] Matching over domain ADTs is exhaustive, with no catch-all branch; every decision table is complete and unambiguous.
- [ ] Each module is deep: a simple interface over rich hidden behavior, internals changeable without breaking callers, no pass-through functions.
- [ ] Errors are defined away, masked, or aggregated, not pushed to callers; error messages never contain the failed data.
- [ ] Every boundary is validated at entry against its boundary type or contract.
- [ ] Step definitions never reach into internals.
- [ ] Module manifests declare exactly the dependencies in the `Depends on` column; no domain logic lives in `apps/`.
- [ ] Each property asserts an invariant over generated input, not a single example.
- [ ] `{{CMD_CHECK}}` and `{{CMD_TEST}}` pass.

Your report is short and contains only:

1. The property tests you added, one line each: the property in plain words, and the invariant it protects or the permutations the features cannot cover. If you added none, say "Done."
2. Mutants you could not kill without a new scenario, with file and line.
3. Any boundary type or contract you added that the task did not cover.
4. Anything you could not run, such as `{{CMD_TEST_LIVE}}`, instead of claiming it passed.

Do not summarize the implementation or the test results. Omit any item with nothing to say.
