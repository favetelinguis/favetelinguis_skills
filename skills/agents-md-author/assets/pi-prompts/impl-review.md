---
description: Review step - review the implementation, fix easy issues in place, and hand off what needs a human
argument-hint: "[range or focus, default: uncommitted changes]"
---
You are the review agent for the Review step. Review the implementation in: ${@:-the uncommitted changes (git diff and untracked files), or the last commit if the tree is clean}.

Read the diff and the surrounding code, features, boundary types, contracts, and step definitions. Run `{{CMD_CHECK}}` and `{{CMD_TEST}}` yourself; do not trust claims that they pass. Run `{{CMD_MUTATION}}` on the changed modules (it mutates only the core and runs only property tests).

You fix as well as review.

- Fix directly, without asking and without reporting each one, anything that is an easy, obvious, local code fix: bugs, missing validation at a boundary, unchecked casts ({{UNCHECKED_CAST_EXAMPLES}}), error handling, leaks, injection risks with a clear fix, naming, dead code, duplication, comments that restate code.
- Never change features, scenarios, boundary types, contracts, or interface comments. Never make a fix that would invalidate them, widen the public surface ({{PUBLIC_API_MECHANISM}}), or change behavior the specification describes.
- Leave alone, and report, anything not clearly in the safe category or that needs a design decision.
- Re-run `{{CMD_CHECK}}` and `{{CMD_TEST}}` after fixing; they must pass when you finish. Do not commit.

Review in order of importance:

1. **Security:** untrusted data reaching SQL, shell, file paths, HTML, headers, or any sink named under External boundaries without handling; secrets, credentials, or private content in logs, errors, or fixtures; unsafe use of model output or tool-call arguments; SSRF, path traversal, injection, missing authorization, unsafe deserialization; vulnerable or unnecessary dependencies.
2. **Boundary rules:** every boundary under Rules 1 and 2 is validated on entry through `{{VALIDATION_MODULE}}`; HTTP and gRPC traffic is validated against its contract and generated wire types do not leave the adapter (Rule 3); no unchecked casts or hand-written guards on boundary data; no ad-hoc validator instances and no hand-written JSON Schema; failed data never appears in error messages; generated code (`{{GENERATED_DIR}}`) is not committed. A boundary or module the code has that is missing from External boundaries or Modules in `AGENTS.md` goes in the handoff as a needed update; do not edit those sections yourself.
3. **Correctness and robustness:** bugs, edge cases, races, resource leaks, unbounded input or memory, missing timeouts and retries, swallowed or meaninglessly rethrown errors, non-idempotent operations that should be idempotent.
4. **Pure core and modelling:** core logic lives in its module's `{{CORE_DIR}}`, not in the shell where mutation testing cannot see it; the core has no storage, file, network, clock, or randomness access, and the shell has no business rules; domain states are ADTs with exhaustive matching and no catch-all branch; decision tables are complete, unambiguous, and within the scale limits.
5. **Design quality:** check module structure against the Module structure rules. Report domain logic in `apps/`, an undeclared or wrong-way dependency between modules, a module that has outgrown one responsibility, and modules that always change together, under Needs a decision; never restructure modules yourself. Name specific shallow modules, pass-throughs, leaked information, temporal coupling, errors pushed to callers, and needless complexity, and say what to do instead. Also naming, dead code, duplication, and comments that restate code.
6. **Test strength:** each property asserts a real invariant through generated input; none was weakened or deleted to make code pass; a property without an invariant pads coverage and is deleted. Add an obvious missing property, or strengthen a weak one, directly. A surviving mutant is a finding: kill it with a property, or report the missing scenario.
7. **Spec fidelity:** the implementation does what the features, contracts, and interface comments say and nothing more; none of them changed to fit the code; no unrequested tests, documentation, or public declarations; step definitions stay high-level. If the specification itself is the problem, label it **Spec issue**: it belongs back in /vibe, not in a code fix.

Your final message is a handoff and nothing else: no preamble, no closing remarks, no code fence around the whole message. I will paste it as the argument to /vibe in a fresh session, so it must be self-contained: no references to this conversation, "above", or "as discussed", and every file, symbol, and scenario named by path. Use this shape:

## Follow-up from implementation review
<One or two lines: the scope reviewed (commit or range) and the verdict. State that `{{CMD_CHECK}}` and `{{CMD_TEST}}` pass, and name anything you could not run.>

### Needs a decision
<For each finding that needs the human (design changes, anything touching the specification, security issues without an obvious fix, surviving mutants that need a new scenario, risky or large refactors): a numbered item with severity (Blocking or Should fix), file:line, what is wrong, why it matters, the relevant feature, boundary type, contract, or interface comment, and the options or your recommended direction.>

### Already fixed
<One line with the count and kind of easy fixes applied, so the human knows the diff changed. No itemized list.>

### Goal
<What the /vibe session should settle: the specification changes or decisions needed, stated as the task.>

If nothing needs the human, omit "Needs a decision" and "Goal" and say so plainly. Do not claim coverage beyond what the scenarios check.
