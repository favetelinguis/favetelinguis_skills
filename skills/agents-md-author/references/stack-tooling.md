# Stack tooling map

Default values for the stack placeholders in `assets/AGENTS.md.template`, per language.
Prefer a tool the project already uses when it can satisfy the rule.
Tool names, flags, and draft support drift over time: confirm each command with the tool's
`--help` or docs before writing it into AGENTS.md.

Contents

- [Shared conventions (all languages)](#shared-conventions-all-languages)
- [TypeScript / Node](#typescript--node)
- [Python](#python)
- [Rust](#rust)
- [Go](#go)
- [JVM: Java 21+ / Kotlin](#jvm-java-21--kotlin)
- [.NET: C#](#net-c)
- [Any other language](#any-other-language)

## Shared conventions (all languages)

- Layout is `apps/<app>/` (deployable entry points: wiring and the outermost shell) plus
  `libs/<module>/`, each with `features/`, `steps/`, `schemas/`, `src/`, and `plan/` at the root.
  Adapt only what the toolchain forces (e.g. Gradle `src/main/...`), and say so in the layout tree.
- `{{SCHEMA_MODULE}}` is one shared module, conventionally `libs/schema`. It is itself a deep module:
    - It compiles each schema once, in strict mode, with `$schema` draft 2020-12.
    - It exposes a single "validate or raise one aggregated boundary error" function.
    - Its errors carry the schema path and keyword, never the failing value.
- `{{CMD_TEST}}` runs the features (excluding `@live`), then the property tests.
- `{{CMD_CHECK}}` runs codegen first, then type check, lint, format check, and the boundary checks.
- Decision-table completeness needs a check: use the compiler where it can check exhaustiveness,
  otherwise a property that enumerates the condition product.

## TypeScript / Node

- MODULE_UNIT: pnpm workspace package
- PUBLIC_API_MECHANISM: `exports` in each `package.json`
- BOUNDARY_ENFORCEMENT: `exports` maps, pnpm's strict `node_modules`, and dependency-cruiser rules
  that forbid deep imports into another workspace's `src/`
- ADT_ENFORCEMENT: discriminated unions with `switch` + `@typescript-eslint/switch-exhaustiveness-check`
  and an `assertNever(x: never)` default
- DECISION_TABLE_FORM: a nested `Record<CondA, Record<CondB, Outcome>>` constant declared with
  `as const satisfies ...`. The compiler then checks completeness over finite literal unions.
- INTERFACE_COMMENT_ENFORCEMENT: `eslint-plugin-jsdoc` `jsdoc/require-jsdoc` with `publicOnly: true`
- BDD_TOOL: `@cucumber/cucumber` (`cucumber-js --tags "not @live"`; live: `--tags @live`)
- PBT_TOOL: fast-check on the built-in `node:test` runner (stateful testing: `fc.commands`)
- PROPERTY_TEST_LOCATION: `src/<module>.property.ts`
- GENERATOR_LOCATION: `src/<workspace>.arbitraries.ts`
- PBT_REGRESSION: an `examples` entry in `fc.assert`
- PBT_REPLAY: `fc.assert(property, { seed, path })`
- MUTATION_TOOL: StrykerJS. Use the `command` test runner to run the same test command, because node:test
  has no dedicated runner. Cucumber steps can use `@stryker-mutator/cucumber-runner`.
- SCHEMA_VALIDATOR: Ajv (`ajv/dist/2020`) with `ajv-formats`
- SCHEMA_CODEGEN: `json-schema-to-typescript`. Import generated types only with `import type`.
- SCHEMA_MODULE: `@repo/schema`
- GENERATED_DIR: `**/src/generated/`
- UNCHECKED_CAST_EXAMPLES: `as`, non-null `!`, `any`, hand-written guards such as `isRecord`
- Typical commands: `pnpm check`, `pnpm test`, `pnpm test:live`, `pnpm gen`, `pnpm mutation`

## Python

- MODULE_UNIT: uv workspace member package
- PUBLIC_API_MECHANISM: names in the package `__init__.py` `__all__`. Everything else lives in
  `_private` submodules.
- BOUNDARY_ENFORCEMENT: import-linter contracts (`lint-imports`) that forbid importing another
  module's private submodules and keep modules independent
- ADT_ENFORCEMENT: frozen dataclasses joined in a union type alias. Handle them with `match` +
  `typing.assert_never`, under pyright strict with `reportMatchNotExhaustive`.
- DECISION_TABLE_FORM: a module-level `Mapping[tuple[CondA, CondB], Outcome]` keyed by `Enum` members.
  Completeness is asserted against `itertools.product` of the enums in a property.
- INTERFACE_COMMENT_ENFORCEMENT: ruff pydocstyle rules `D1` (public docstrings)
- BDD_TOOL: pytest-bdd. Tags become pytest markers, so use `-m "not live"` and register the `live` marker.
- PBT_TOOL: Hypothesis (stateful testing: `RuleBasedStateMachine`)
- PROPERTY_TEST_LOCATION: `libs/<module>/properties/test_<topic>.py`
- GENERATOR_LOCATION: `libs/<module>/properties/strategies.py`
- PBT_REGRESSION: an `@example(...)` decorator on the property
- PBT_REPLAY: the printed `@reproduce_failure(...)`, or `--hypothesis-seed`. Git-ignore `.hypothesis/`.
- MUTATION_TOOL: mutmut (`mutmut run`)
- SCHEMA_VALIDATOR: `jsonschema` `Draft202012Validator` with a `FormatChecker`. It has no strict mode,
  so the schema module runs `check_schema` and rejects schemas that lack
  `additionalProperties`/`unevaluatedProperties: false`.
- SCHEMA_CODEGEN: datamodel-code-generator with `--output-model-type typing.TypedDict`. Validated
  dicts are typed without a second validation layer.
- SCHEMA_MODULE: `repo_schema` (in `libs/schema`)
- GENERATED_DIR: `**/_generated/`
- UNCHECKED_CAST_EXAMPLES: `typing.cast`, `Any`, `# type: ignore`, `isinstance`-based hand guards,
  using `json.loads` output directly
- Typical commands: `uv run poe check` / `test` / `test-live` / `gen` / `mutation`. Any task runner
  works; `poethepoet` is shown as an example.

## Rust

- MODULE_UNIT: crate in a Cargo workspace (`libs/<module>`, binary crate in `apps/<app>`)
- PUBLIC_API_MECHANISM: `pub` items re-exported from `lib.rs`. Everything else is private or `pub(crate)`.
- BOUNDARY_ENFORCEMENT: the crate dependency graph in `Cargo.toml` plus crate privacy, with the
  `unreachable_pub` lint denied
- ADT_ENFORCEMENT: enums + `match` (the compiler checks exhaustiveness). clippy
  `wildcard_enum_match_arm` forbids `_` arms on domain enums. Do not mark domain enums `#[non_exhaustive]`.
- DECISION_TABLE_FORM: a `match (a, b, c)` over a tuple of enums. The compiler checks completeness,
  and overlapping rows show up as `unreachable_patterns` (denied).
- INTERFACE_COMMENT_ENFORCEMENT: `#![deny(missing_docs)]`, plus clippy `missing_errors_doc` and `missing_panics_doc`
- BDD_TOOL: the `cucumber` crate in a `harness = false` test target. It filters out `@live` unless an
  env var such as `LIVE=1` is set.
- PBT_TOOL: proptest (stateful testing: `proptest-state-machine`)
- PROPERTY_TEST_LOCATION: a `#[cfg(test)] mod properties` in `src/<module>/properties.rs`, which has
  private access
- GENERATOR_LOCATION: `#[cfg(test)]` strategies in `src/strategies.rs`
- PBT_REGRESSION: committed `proptest-regressions/` files, which proptest writes automatically
- PBT_REPLAY: the regressions file replays the case. To pin a seed, use the `PROPTEST_RNG_SEED` env var.
- MUTATION_TOOL: cargo-mutants (`cargo mutants`)
- SCHEMA_VALIDATOR: the `jsonschema` crate (draft 2020-12). Validate a `serde_json::Value` before
  deserializing it into the generated type.
- SCHEMA_CODEGEN: typify, from `build.rs` into `OUT_DIR`. It supports a subset of JSON Schema, so keep
  schemas inside that subset and note it under Project deviations.
- SCHEMA_MODULE: the `schema` crate in `libs/schema`
- GENERATED_DIR: `target/` (build.rs `OUT_DIR`)
- UNCHECKED_CAST_EXAMPLES: `serde_json::from_*::<T>` on boundary data without schema validation,
  `.unwrap()` on parsed input, `transmute`
- Typical commands: `cargo xtask check` (fmt --check, clippy -D warnings), `cargo test`,
  `LIVE=1 cargo test --test features`, `cargo build` (codegen runs in build.rs), `cargo mutants`

## Go

- MODULE_UNIT: package tree `libs/<module>/` in a single Go module (one `go.mod`)
- PUBLIC_API_MECHANISM: exported identifiers of the `libs/<module>` root package. Internals live in
  `libs/<module>/internal/...`.
- BOUNDARY_ENFORCEMENT: the compiler-enforced `internal/` rule, plus golangci-lint `depguard` rules
  for cross-module imports
- ADT_ENFORCEMENT: a sealed interface (unexported marker method) + type switch, checked by
  golangci-lint `gochecksumtype` (`//sumtype:decl`). Enum switches are checked by `exhaustive`.
- DECISION_TABLE_FORM: a map keyed by a struct of enum values. Completeness is asserted in a property
  over all enum combinations.
- INTERFACE_COMMENT_ENFORCEMENT: golangci-lint `revive` rule `exported`
- BDD_TOOL: godog through `TestMain`, with tags `~@live` by default and `@live` for live runs
- PBT_TOOL: `pgregory.net/rapid` (stateful testing: `t.Repeat` with action maps)
- PROPERTY_TEST_LOCATION: `<file>_property_test.go` in the same internal package
- GENERATOR_LOCATION: `generators_test.go` in the same package
- PBT_REGRESSION: the failfile committed under `testdata/rapid/`
- PBT_REPLAY: `-rapid.failfile=...` or `-rapid.seed=...`
- MUTATION_TOOL: gremlins (`gremlins unleash`). It is young; check that it is maintained, and fall
  back to go-mutesting.
- SCHEMA_VALIDATOR: `github.com/santhosh-tekuri/jsonschema/v6`
- SCHEMA_CODEGEN: `github.com/omissis/go-jsonschema` via `go generate`. Check its draft support
  against your schemas.
- SCHEMA_MODULE: `libs/schema`
- GENERATED_DIR: `**/generated/`. Go culture commits generated code; this rule does not, so
  `{{CMD_CHECK}}` and `{{CMD_TEST}}` must run `go generate ./...` first.
- UNCHECKED_CAST_EXAMPLES: type assertions on `any`, `map[string]any`, `json.Unmarshal` into a struct
  without schema validation
- Typical commands: `make check` (generate, vet, golangci-lint), `make test`, `make test-live`, `make gen`,
  `make mutation`

## JVM: Java 21+ / Kotlin

- MODULE_UNIT: Gradle subproject
- PUBLIC_API_MECHANISM: the module's `api` package. JPMS `module-info.java` `exports` only that package.
- BOUNDARY_ENFORCEMENT: JPMS exports plus ArchUnit rules run in `check`. With Spring, use Spring
  Modulith `ApplicationModules.verify()`.
- ADT_ENFORCEMENT: sealed interfaces + records with pattern-matching `switch` and no `default`
  (Kotlin: sealed interfaces + `when` expressions). The compiler checks exhaustiveness.
- DECISION_TABLE_FORM: an immutable `Map` keyed by a record of enums. Completeness is asserted in a
  property over all enum combinations.
- INTERFACE_COMMENT_ENFORCEMENT: Checkstyle `MissingJavadocMethod`/`MissingJavadocType` at public scope
  (Kotlin: detekt `UndocumentedPublic*`)
- BDD_TOOL: Cucumber-JVM on the JUnit Platform (`cucumber.filter.tags=not @live`)
- PBT_TOOL: jqwik (stateful testing: action chains). Kotlin may use Kotest property testing instead.
- PROPERTY_TEST_LOCATION: `src/test/java/<same package>/<Thing>Properties.java`
- GENERATOR_LOCATION: `<Module>Arbitraries.java` in the same test package
- PBT_REGRESSION: an `@Example` method reproducing the shrunk counterexample
- PBT_REPLAY: `@Property(seed = "...")`
- MUTATION_TOOL: PIT via the `info.solidsoft.pitest` Gradle plugin with `pitest-junit5-plugin`
- SCHEMA_VALIDATOR: `com.networknt:json-schema-validator` (draft 2020-12)
- SCHEMA_CODEGEN: jsonschema2pojo. It covers older drafts only, so keep schemas inside its supported
  subset and record that under Project deviations.
- SCHEMA_MODULE: the `:libs:schema` subproject
- GENERATED_DIR: `build/generated/`
- UNCHECKED_CAST_EXAMPLES: casts, `Map<String, Object>`, `@SuppressWarnings("unchecked")`,
  `ObjectMapper.readValue` without schema validation
- Typical commands: `./gradlew check`, `./gradlew test`, `./gradlew liveTest`, `./gradlew generateJsonSchema2Pojo`,
  `./gradlew pitest`

## .NET: C#

- MODULE_UNIT: project (`.csproj`) in the solution
- PUBLIC_API_MECHANISM: `public` types. Everything else is `internal`. `InternalsVisibleTo` is allowed
  only for the module's own test project.
- BOUNDARY_ENFORCEMENT: project references plus NetArchTest or ArchUnitNET rules in the test run
- ADT_ENFORCEMENT: C# has no closed unions. Use Dunet (or OneOf) for generated exhaustive `Match`,
  and never write `_ => throw` arms over domain types.
- DECISION_TABLE_FORM: a `FrozenDictionary` keyed by a tuple of enums. Completeness is asserted in a
  property, because enum switches are never compiler-exhaustive.
- INTERFACE_COMMENT_ENFORCEMENT: `GenerateDocumentationFile` with CS1591 as an error
- BDD_TOOL: Reqnroll. Tags become test categories, so use `dotnet test --filter "Category!=live"`.
- PBT_TOOL: FsCheck (or CsCheck)
- PROPERTY_TEST_LOCATION: the module's test project, `Properties/<Thing>Properties.cs`
- GENERATOR_LOCATION: `Properties/<Module>Arbitraries.cs`
- PBT_REGRESSION: an explicit test case reproducing the shrunk counterexample
- PBT_REPLAY: FsCheck `Replay = "<seed>"`
- MUTATION_TOOL: Stryker.NET (`dotnet stryker`)
- SCHEMA_VALIDATOR: JsonSchema.Net (json-everything)
- SCHEMA_CODEGEN: Corvus.JsonSchema
- SCHEMA_MODULE: the `Repo.Schema` project
- GENERATED_DIR: `**/Generated/`
- UNCHECKED_CAST_EXAMPLES: casts, `dynamic`, null-forgiving `!`, `JsonSerializer.Deserialize<T>`
  without schema validation
- Typical commands: `dotnet build -warnaserror` + `dotnet format --verify-no-changes`, `dotnet test`, `dotnet stryker`

## Any other language

Fill each placeholder by finding, in order of preference:

1. A Cucumber-family Gherkin runner. If none exists, use Given/When/Then-structured tests in the
   native runner, keeping `features/` as the spec, and record it under Project deviations.
2. A property-based testing library with shrinking.
3. A mutation testing tool. If none exists, say so under Project deviations, and have the
   reviewer hand-mutate core logic instead.
4. A JSON Schema validator that supports draft 2020-12, and a schema-to-type generator.
5. The language's strongest mechanism for module privacy, plus a linter or architecture test that
   fails on cross-module internal imports.
6. Its closest form of sum types with exhaustiveness checking.

Never give up a rule silently because tooling is missing. Record every gap under Project deviations.
