# Engineering practices

The project decides language, architecture, design and code standards, tooling, and commands: its AGENTS.md or CLAUDE.md, its docs, and its existing code. Where the project speaks, it wins over this section. Where it is silent, follow the surrounding code, then these practices.

- Solve the problem with the simplest change that fits. No speculative options, layers, or abstractions. Less code beats more.
- Put code where the project keeps that kind of code. Reuse and extend what exists before adding files, modules, helpers, or dependencies. Match local naming and style.
- Prefer deep modules: a small interface hiding real work. No pass-through functions or wrappers that add nothing.
- Every behavior change ships with tests at the level the project already tests, through public interfaces. A bug fix starts with a failing test. Never weaken or skip a test to make code pass.
- Comments say why, or what a caller must know; never restate the code. Update docs sparingly, only where the change made them wrong or a reader will look for it. Do not add doc files nobody asked for.
- Validate untrusted input where it enters; handle errors where they can be handled; keep secrets and private data out of logs and errors.
- Stay in scope: one task is one reviewable pull request. Report unrelated problems instead of fixing them.
- Run the project's check and test commands before saying something works. Name what you could not run.
- Never commit, push, or rewrite git history unless asked.
