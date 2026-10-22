# Stack tooling map

Default values for the stack placeholders in `assets/AGENTS.md.template` and the prompt
templates in `assets/pi-prompts/`, per language. The supported stacks are TypeScript, Java, and
Elixir.
Prefer a tool the project already uses when it can satisfy the rule.
Tool names, flags, and APIs drift over time: confirm each command with the tool's
`--help` or docs before writing it into AGENTS.md.

Contents

- [Shared conventions (all languages)](#shared-conventions-all-languages)
- [Self-contained toolchain (mise)](#self-contained-toolchain-mise)
- [TypeScript / Node](#typescript--node)
- [Java 21+ / Kotlin (Maven)](#java-21--kotlin-maven)
- [Elixir 1.20+ / Erlang/OTP (Mix)](#elixir-120--erlangotp-mix)
- [Any other language](#any-other-language)

## Shared conventions (all languages)

- Layout is `apps/<app>/` (deployable entry points: wiring and the outermost shell) plus
  `libs/<module>/`, each with `features/`, `steps/`, and `src/`, and
  `contracts/` only in a module that serves or calls an HTTP or gRPC interface. `tasks/` at the
  repo root holds one task file per goal; it is created by the first `/specify` session.
  Adapt only what the toolchain forces (e.g. Maven `src/main/java/...`), and say so in the layout tree.
- Every module is a build module of the workspace root: a pnpm workspace package listed by
  `pnpm-workspace.yaml` (`libs/*`, `apps/*`), or a Maven module listed in the root aggregator
  `pom.xml`. No module is just a directory inside another build module. Elixir is the one
  exception (a Boundary inside one Mix project); its section records it as a standing deviation.
- `{{MODULE_GRAPH_ENFORCEMENT}}` makes three things fail the build: an import of a module that is not
  declared in the manifest, a cycle between modules, and a `libs/` module depending on `apps/`.
  It runs in `{{CMD_CHECK}}`.
- Internal boundaries use native types only. Boundary types live in the owning module's public
  interface, with their constraints declared on the type. No JSON Schema files, no codegen.
- `{{VALIDATION_MODULE}}` is one shared module, conventionally `libs/boundary`. It is itself a deep
  module:
    - It exposes a single "validate or raise one aggregated boundary error" function.
    - It is strict: unknown properties are rejected.
    - Its errors carry the path and the violated constraint, never the failing value. The
      underlying validators do include the value, so it strips it.
- HTTP and gRPC are contract-first (Rule 3). The OpenAPI document (3.1) or `.proto` files in
  `contracts/` are written during `/design`. `{{CMD_GEN}}` generates code from every contract into
  `{{GENERATED_DIR}}`, and is a no-op while no contracts exist, so it can be wired on day one.
- Protobuf uses Buf for every language: `buf generate`, `buf lint`, `buf breaking`, with
  protovalidate (`buf.validate` field options) for constraints that proto3 cannot express.
- `{{CMD_TEST}}` runs the features (excluding `@live`), then the property tests.
- `CORE_DIR` is relative to the module root, so every `libs/` module has its own core. One mutation config
  matches all of them with a glob; `{{CMD_MUTATION}}` mutates only these directories (excluding
  property tests and generators), runs only the property tests, and accepts module paths to scope
  a run to the changed modules. It never runs features or mutates shell code: features are far too
  slow to run per mutant. Use the tool's incremental mode so unchanged mutants are not re-run.
- `{{CMD_CHECK}}` runs codegen first, then type check, lint, format check, contract lint, and the
  boundary checks.
- Decision-table completeness needs a check: use the compiler where it can check exhaustiveness,
  otherwise a property that enumerates the condition product.
- Every `{{CMD_*}}` is a mise task (`mise run check`, `mise run test`, `mise run test:live`,
  `mise run gen`, `mise run mutation`); a section's "Typical commands" are those task bodies.

## Self-contained toolchain (mise)

Shared `mise.toml` skeleton. Pin exact versions (check with `mise ls-remote <tool>`); the
language blocks below add their tools, env, and task bodies.

```toml
min_version = "<the installed mise version>"

[settings]
lockfile = true

[tools]
buf = "<x.y.z>"                  # aqua:bufbuild/buf: buf generate, lint, breaking
node = "<lts>"                    # needed by the npm: backend below
"npm:@redocly/cli" = "<x.y.z>"    # redocly lint for OpenAPI

[tasks.setup]
description = "Fetch dependencies and generate code"

[tasks.check]
description = "Codegen, type check, lint, format check, contract lint, boundary checks"

[tasks.test]
description = "Features (excluding @live), then property tests"

[tasks."test:live"]
description = "@live scenarios against real services"

[tasks.gen]
description = "Generate code from contracts (no-op without contracts)"

[tasks.mutation]
description = "Mutate the pure core, run only property tests; args scope to modules"
```

- Contract tools are pinned on day one even before a contract exists, so `{{CMD_GEN}}` and the
  contract lint run as no-ops instead of failing later on a missing tool.
- Commit `mise.toml`, `mise.lock`, and `.mise/locks/` if mise creates it. Git-ignore
  `mise.local.toml`, which stays the human's personal override file.
- Tasks that only make sense with arguments (`mutation` scoped to modules) take them through
  the `usage` field or pass `$@` through; confirm the syntax with `mise run --help`.
- TypeScript: `node` (core), `pnpm` (`aqua:pnpm/pnpm`) at the same version as `packageManager`
  in the root `package.json`; disable corepack for the project so it cannot shadow the pin.
- Java: `java` (core, e.g. `temurin-21.x`). Maven comes from the committed Maven wrapper
  (`./mvnw`), which is itself pinned, so `maven` is not a mise tool. Kotlin needs nothing extra.
- Elixir: see the Elixir section's mise block.
## TypeScript / Node

- MODULE_UNIT: pnpm workspace package
- PUBLIC_API_MECHANISM: `exports` in each `package.json`
- BOUNDARY_ENFORCEMENT: `exports` maps, pnpm's strict `node_modules`, and dependency-cruiser rules
  that forbid deep imports into another workspace's `src/`
- MODULE_GRAPH_ENFORCEMENT: `workspace:*` dependencies in each `package.json` with pnpm's strict
  `node_modules` (an undeclared module does not resolve), `disallow-workspace-cycles=true` in
  `.npmrc`, and dependency-cruiser rules `no-circular`, `no-non-package-json`, and a custom rule
  forbidding `libs/*` from importing `apps/*`
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
- CORE_DIR: `src/core/`
- MUTATION_TOOL: StrykerJS with `mutate: ["libs/*/src/core/**/*.ts", "!**/*.property.ts",
  "!**/*.arbitraries.ts"]`, `--incremental`, and the `command` test runner
  (node:test has no dedicated runner) running only the property tests (`node --test` on the
  compiled `*.property.js`), never cucumber-js. Scope a run with `--mutate "libs/<module>/src/core/**/*.ts"`.
- VALIDATOR: typia, applied by its compile-time transform
- CONSTRAINT_MECHANISM: typia type tags intersected into the type (`tags.MinLength<1>`,
  `tags.Format<"email">`, `tags.Pattern<"...">`, `tags.Minimum<0>`, `tags.Type<"uint32">`)
- CONSTRAINED_SCALAR_FORM: a named, exported type alias with tags, such as
  `type Email = string & tags.Format<"email">`
- CROSS_FIELD_FORM: a named refinement function passed to the same `@repo/boundary` call, reporting
  a path and a constraint name
- VALIDATOR_DECLARATION: `typia.createValidateEquals<T>()` (the `Equals` variant rejects unknown properties)
- VALIDATION_MODULE: `@repo/boundary`
- JSON_SCHEMA_EXPORT: `typia.json.schema<T>()`, or `typia.llm.parameters<T>()` for model tool definitions
- OPENAPI_TOOLING: `openapi-typescript` for types, and request and response validation against the
  document with the HTTP framework's OpenAPI validator (e.g. `express-openapi-validator`;
  `fastify-openapi-glue` for Fastify)
- PROTOBUF_TOOLING: `buf generate` with `protoc-gen-es` and Connect-ES (`@connectrpc/connect`),
  validated with `@bufbuild/protovalidate`
- CONTRACT_CHECKS: `redocly lint` for OpenAPI, `buf lint` and `buf breaking` for protobuf
- STUB_BODY: `throw new Error("not implemented")`
- GENERATED_DIR: `**/src/generated/`
- UNCHECKED_CAST_EXAMPLES: `as`, non-null `!`, `any`, hand-written guards such as `isRecord`,
  `JSON.parse` output used directly, `typia.assert` or `typia.is` called outside `@repo/boundary`
- Typical commands (the mise task bodies): `pnpm check`, `pnpm test`, `pnpm test:live`,
  `pnpm gen`, `pnpm mutation`
- Gotchas:
    - typia only works through its transform. Install it with `npx typia setup` (ts-patch), and run
      features, properties, and Stryker on transformed output (`tsc`, or a bundler with
      `@ryoppippi/unplugin-typia`). `tsx`, plain esbuild, and Node type stripping skip the transform,
      and typia calls then throw at runtime.
    - typia's validation errors include the failing value; `@repo/boundary` must drop it.
    - `openapi-typescript` emits types only, without constraints, so the runtime validator is
      required, not optional.

## Java 21+ / Kotlin (Maven)

- MODULE_UNIT: Maven module (a `<module>` of the root aggregator `pom.xml`, which also manages
  dependency and plugin versions)
- PUBLIC_API_MECHANISM: the module's `api` package. JPMS `module-info.java` `exports` only that package.
- BOUNDARY_ENFORCEMENT: JPMS exports plus ArchUnit rules run in `{{CMD_CHECK}}`. With Spring, use Spring
  Modulith `ApplicationModules.verify()`.
- MODULE_GRAPH_ENFORCEMENT: the Maven reactor (it rejects cyclic module dependencies),
  `maven-dependency-plugin:analyze-only` with `failOnWarning=true` (every used module is declared,
  no declared module is unused), `maven-enforcer-plugin` with `bannedDependencies` in each `libs/`
  module banning the `apps` artifacts, and an ArchUnit `slices().matching("<base>.(*)..")
  .should().beFreeOfCycles()` rule
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
- CORE_DIR: `src/main/java/<module package>/core/` (the module's `core` subpackage)
- MUTATION_TOOL: PIT via `org.pitest:pitest-maven` with the `pitest-junit5-plugin` dependency,
  `<targetClasses><param><base>.*.core.*</param></targetClasses>`,
  `<targetTests><param>*Properties</param></targetTests>` (so Cucumber runners are excluded), and
  `<withHistory>true</withHistory>` for incremental runs. Configure it once in the root
  `pluginManagement`, in a `mutation` profile, so `./mvnw -Pmutation -pl libs/<module> -am ...`
  scopes a run to one module and its upstream modules
- VALIDATOR: Jakarta Bean Validation (Hibernate Validator)
- CONSTRAINT_MECHANISM: Jakarta constraint annotations on record components (`@NotNull`, `@NotBlank`,
  `@Size`, `@Pattern`, `@Email`, `@Min`/`@Max`, `@Valid` to cascade into nested records), including
  type-use positions such as `List<@NotBlank String>`
- CONSTRAINED_SCALAR_FORM: a single-component record with constraints on the component, such as
  `record Email(@NotNull @jakarta.validation.constraints.Email String value)`, used with `@Valid`
- CROSS_FIELD_FORM: a class-level custom constraint (an `@Constraint` annotation with a
  `ConstraintValidator`) on the record
- VALIDATOR_DECLARATION: its constraint annotations; Bean Validation needs no validator object per
  type, only the one shared `Validator` inside `libs/boundary`
- VALIDATION_MODULE: the `libs/boundary` Maven module (`Boundary.check(value)`)
- JSON_SCHEMA_EXPORT: victools `jsonschema-generator` with `jsonschema-module-jakarta-validation`
- OPENAPI_TOOLING: `openapi-generator-maven-plugin`, bound to `generate-sources`, with `useBeanValidation=true` and
  `useJakartaEe=true` (server: `spring` with `interfaceOnly=true`, or `jaxrs-spec`; client: `java`),
  so generated models carry Jakarta constraints and are validated the same way
- PROTOBUF_TOOLING: `buf generate` with `protoc-gen-java` and `protoc-gen-grpc-java`, run from
  `exec-maven-plugin` in `generate-sources` and added as a source root with
  `build-helper-maven-plugin`, validated with `build.buf:protovalidate`
- CONTRACT_CHECKS: `redocly lint` for OpenAPI, `buf lint` and `buf breaking` for protobuf
- STUB_BODY: `throw new UnsupportedOperationException()` (Kotlin: `TODO()`)
- GENERATED_DIR: `target/generated-sources/` (ignored with `target/`)
- UNCHECKED_CAST_EXAMPLES: casts, `Map<String, Object>`, `@SuppressWarnings("unchecked")`,
  `ObjectMapper.readValue` without `Boundary.check`, `ConstraintViolation.getInvalidValue()` or
  `${validatedValue}` in a constraint message
- Typical commands (the mise task bodies), all through the Maven wrapper (`mvn wrapper:wrapper`):
    - check: `./mvnw -Pcheck verify`. Codegen, compile, Enforcer, dependency analysis, Checkstyle,
      and only the ArchUnit tests (Surefire `groups=architecture`).
    - test: `./mvnw verify`. One Surefire execution runs the Cucumber suite with
      `cucumber.filter.tags=not @live`, then a second runs `*Properties`.
    - live: `./mvnw -Plive verify` (`cucumber.filter.tags=@live`).
    - gen: `./mvnw generate-sources`.
    - mutation: `./mvnw -Pmutation test-compile org.pitest:pitest-maven:mutationCoverage`, scoped
      with `-pl libs/<module> -am`.
- Gotchas:
    - Cascading is opt-in: a nested record or collection element is validated only when the
      component carries `@Valid`. Add an ArchUnit rule that every component whose type is a
      boundary record is annotated `@Valid`.
    - Jackson leaves a missing field `null`, so every required component needs `@NotNull`. Enable
      `FAIL_ON_UNKNOWN_PROPERTIES` and `FAIL_ON_NULL_FOR_PRIMITIVES` on the shared `ObjectMapper`;
      Spring Boot disables the first by default.
    - Hibernate Validator needs an EL implementation (`org.glassfish.expressly:expressly`) or the
      `ParameterMessageInterpolator`.
    - Kotlin: target the field with `@field:NotBlank`, or the constraint is put on the constructor
      parameter and ignored. Build it with `kotlin-maven-plugin`.
    - Maven does not glob modules: every new module needs a `<module>` entry in the root `pom.xml`,
      and the root aggregator must not declare dependencies itself, or every module inherits them
      and the dependency analysis becomes meaningless. Use `dependencyManagement` only.
    - A dependency used only through another module's API still counts as used: declare it
      directly, or `dependency:analyze` reports it as used-undeclared.
    - Cucumber reads `features/` at the module root, outside Maven's resource dirs: set
      `cucumber.features` to it, or the suite runs zero scenarios and passes.

## Elixir 1.20+ / Erlang/OTP (Mix)

Idiom fit: idiomatic Elixir already satisfies much of the philosophy (immutable data, pattern
matching, tagged tuples as sum types, `{:ok, _} | {:error, _}` results, processes as the shell).
Fill the placeholders with those idioms. Do not add wrappers, macros, or DSLs on top of them.
The pure core is plain modules of structs and functions, never a process: GenServers,
`gen_statem`, Oban workers, and Phoenix controllers are shell that call the core and execute
what it returns (`{new_state, [effect]}`, or decide/evolve:
`decide(state, command) :: {:ok, [event]} | {:error, reason}`, `evolve(state, event) :: state`).

- Standing deviations, recorded in every Elixir project:
    - Module structure: a module is a top-level Boundary inside one Mix project, not its own
      build module. Boundary enforces the public interface, declared dependencies, and cycles
      that separate build modules would give.
    - Exhaustive handling of domain ADTs: the compiler does not report missing cases over
      user-defined sum types. Enforcement is the no-catch-all Credo check plus a property over
      every variant (partial; review covers the rest).
    - Protobuf constraints: no protovalidate implementation exists for Elixir. The gRPC adapter
      validates each decoded message against a Zoi schema through `{{VALIDATION_MODULE}}`.
    - Mutation testing: Muex is the only maintained tool and is young. If it cannot run a
      module, the reviewer hand-mutates that module's core instead.
- mise block (add to the shared skeleton):

  ```toml
  [tools]
  erlang = "<29.x.y>"
  elixir = "<x.y.z>-otp-29"   # the -otp-NN suffix must match the erlang major

  [settings.erlang]
  # Precompiled Erlang exists only for Ubuntu 20.04/22.04/24.04, macOS, and Windows; any other
  # glibc Linux (Arch, Fedora, Debian) builds from source with kerl. Ignored on macOS.
  precompiled_os = "ubuntu-24.04"

  [env]
  MIX_HOME = "{{config_root}}/.cache/mix"
  MIX_ARCHIVES = "{{config_root}}/.cache/mix/archives"
  HEX_HOME = "{{config_root}}/.cache/hex"
  _.path = ["{{config_root}}/.cache/mix/escripts"]

  [tasks.setup]
  run = ["mix local.hex --force --if-missing", "mix local.rebar --force --if-missing",
         "mix deps.get", "mix escript.install hex protobuf <same version as the dep> --force"]
  ```

  Git-ignore `.cache/`. `{{config_root}}` is mise template syntax, not a skill placeholder: copy
  it verbatim. Greenfield scaffold, after `mise install`: `mix new . --app <app>` (no
  `--sup` until an app exists), then reshape `mix.exs` as below. Phoenix: run `mix phx.new` in a
  scratch directory with the pinned toolchain and move its files into `apps/<app>/`.
- MODULE_UNIT: top-level Boundary (`use Boundary` in `<App>.<Module>`, whose code lives in
  `libs/<module>/lib/`) of the single Mix project
- Root `mix.exs`: `compilers: [:boundary] ++ Mix.compilers()`,
  `boundary: [default: [type: :strict]]`, `elixirc_paths: Path.wildcard("{libs,apps}/*/lib")`
  (plus `Path.wildcard("{libs,apps}/*/test/support")` in `:test`),
  `test_paths: ["test" | Path.wildcard("{libs,apps}/*/test")]`, and `test_ignore_filters`
  matching `*/test/support/` and the step files. The root `test/test_helper.exs` runs
  `ExUnit.start()` and, unless `SKIP_FEATURES=1`, `Cucumber.compile_features!()`. Mix requires a
  `test_helper.exs` in every test path, so each module's `test/` gets an empty one.
- PUBLIC_API_MECHANISM: Boundary `exports:` (the boundary's root module plus the listed
  modules); every other module in the boundary is `@moduledoc false`
- BOUNDARY_ENFORCEMENT: the Boundary compiler (`compilers: [:boundary | ...]`, default
  `type: :strict`), failing the build through `mix compile --warnings-as-errors`
- MODULE_GRAPH_ENFORCEMENT: Boundary `deps:` on every boundary (an undeclared dependency is a
  compile error, and Boundary reports cycles), no `libs/` boundary listing an `apps/` boundary
  in its `deps:`, and `mix xref graph --format cycles --label compile-connected --fail-above 0`
- ADT_ENFORCEMENT: tagged tuples and structs with `@type` unions, matched in multi-clause
  functions or `case` without a catch-all clause in the core (a project-local Credo check in
  `credo_checks/`, loaded through `requires:` in `.credo.exs`); Elixir 1.20's type checker
  under `--warnings-as-errors` for verified type violations and clauses that can never match;
  and a property over a generator of every variant for missing cases
- DECISION_TABLE_FORM: a dedicated multi-clause function, one clause per row, whose head
  matches a tuple of condition atoms (`def decide({:gold, :overdue}), do: ...`). Each condition's
  domain is declared once as an `@type` union plus a module attribute listing its values. A `_`
  in one column is allowed only as a deliberate "don't care" cell, with the table's first-match
  policy stated in its `@doc`; a clause that matches everything is never allowed.
  Completeness, determinism, and reachability are asserted by a test that enumerates the
  product of the domain attributes (no `FunctionClauseError`, every clause hit). When the rules
  must be data (the "rule set held as validated data" alternative), use a map from condition
  tuple to outcome in a module attribute, checked for completeness at compile time. Never
  `cond` or nested `if` chains, and never a macro DSL or decision-table library.
- INTERFACE_COMMENT_ENFORCEMENT: Credo `Credo.Check.Readability.ModuleDoc` plus `mix doctor`
  (`.doctor.exs` from `mix doctor.gen.config` with every `min_*_coverage` key at 100 and
  `raise: true`; confirm while wiring that `@moduledoc false` modules are skipped)
- BDD_TOOL: `cucumber` (huddlz-hq, on ExUnit) with
  `config :cucumber, features: ["{libs,apps}/*/features/**/*.feature"],
  steps: ["{libs,apps}/*/steps/**/*.exs"]` in `config/test.exs`. Gherkin tags become ExUnit
  tags: `mix test --exclude live --exclude property`; live: `mix test --only live`.
- PBT_TOOL: StreamData (`use ExUnitProperties`, `check all`); for stateful or model-based
  testing, PropCheck's `PropCheck.StateM`, added only when a module needs it
- PROPERTY_TEST_LOCATION: `libs/<module>/test/<thing>_property_test.exs`, tagged
  `@moduletag :property`
- GENERATOR_LOCATION: `libs/<module>/test/support/<module>_generators.ex`
- PBT_REGRESSION: a `test` that runs the property body on the shrunk counterexample as a fixed
  input, named after the property it guards
- PBT_REPLAY: `mix test --seed <seed>` (StreamData derives its seed from ExUnit's)
- CORE_DIR: `lib/core/`, a strict sub-boundary (`<App>.<Module>.Core`, `type: :strict`,
  `deps:` only pure libraries such as `Decimal`). Boundary cannot restrict the `:elixir`
  application or pure Erlang applications, so a project-local Credo check bans `File`, `IO`,
  `System`, `Port`, `Process`, `GenServer`, `Task`, `:ets`, `:rand`, `DateTime.utc_now`,
  `System.os_time`, and `make_ref` inside `lib/core/`.
- MUTATION_TOOL: Muex (`{:muex, only: [:dev, :test], runtime: false}`) run with
  `SKIP_FEATURES=1 mix muex --files "libs/*/lib/core" --test-paths "libs/*/test"
  --fail-at <score>`. Scope a run with `--files libs/<module>/lib/core
  --test-paths libs/<module>/test`; in CI add `--since <base ref>`. The mise task sets
  `SKIP_FEATURES=1` so features never run per mutant.
- VALIDATOR: Zoi
- CONSTRAINT_MECHANISM: Zoi refinements chained on the schema (`Zoi.min/2`, `Zoi.max/2`,
  `Zoi.regex/2`, `Zoi.email/0`, `Zoi.enum/1`, `Zoi.discriminated_union/2`)
- CONSTRAINED_SCALAR_FORM: a public schema function with its type in the owning module, such as
  `@type email :: String.t()` and `def email_schema, do: Zoi.email()`
- CROSS_FIELD_FORM: a named function passed to `Zoi.refine/2` on the map or struct schema,
  returning an error with a path and a constraint code
- VALIDATOR_DECLARATION: a module attribute schema beside the struct, its type derived from it:
  `@schema Validation.struct(__MODULE__, %{...})`,
  `@type t :: unquote(Zoi.type_spec(@schema))`, `def schema, do: @schema`
- VALIDATION_MODULE: `libs/validation` (`<App>.Validation`; not `boundary`, which collides with
  the Boundary library). It exposes `check(schema, input)` returning `{:ok, value}` or
  `{:error, %Validation.Error{issues: [%{path: path, code: code}]}}`, and the schema
  constructors `map/1` and `struct/2`, which set `unrecognized_keys: :error` (Zoi's default
  strips unknown keys).
- JSON_SCHEMA_EXPORT: `Zoi.to_json_schema/1` (JSON Schema 2020-12)
- OPENAPI_TOOLING: server: oaskit with an external spec, where the spec module reads
  `contracts/openapi.json` at compile time (`@external_resource`), controllers bind actions with
  `use_operation :action, "operationId"`, and `Oaskit.Plugs.ValidateRequest` validates every
  request; no server code is generated. Client: `oapi_generator` into `{{GENERATED_DIR}}`. Keep
  contracts as JSON, or add a YAML parser to the spec module.
- PROTOBUF_TOOLING: `buf generate` with the `protoc-gen-elixir` escript (installed by the
  `setup` task into the project's `MIX_HOME`; its version matches the `protobuf` dependency)
  and `plugins=grpc`, plus the `grpc` library. No protovalidate (standing deviation).
- CONTRACT_CHECKS: `redocly lint` for OpenAPI, `buf lint` and `buf breaking` for protobuf
- STUB_BODY: `raise "not implemented"`
- GENERATED_DIR: `{libs,apps}/*/lib/generated/`
- UNCHECKED_CAST_EXAMPLES: `String.to_atom/1` on input, `Map.get/2` or `params["x"]` on
  unvalidated maps, `JSON.decode!/1` output used directly, `struct!/2` or `Kernel.struct/2`
  built from raw maps, `Ecto.Changeset.cast/4` used as boundary validation, `Zoi.parse/2` or
  `Zoi.map/2` called outside `{{VALIDATION_MODULE}}`, a refinement message that interpolates
  the input
- Typical commands (the mise task bodies):
    - check: `mix format --check-formatted`, `mix compile --warnings-as-errors`,
      `mix xref graph --format cycles --label compile-connected --fail-above 0`,
      `mix credo --strict`, `mix doctor`, then `redocly lint` and `buf lint` / `buf breaking`
      over any contracts (skipped when none exist). Run `gen` first.
    - test: `mix test --exclude live --exclude property`, then
      `SKIP_FEATURES=1 mix test --only property`.
    - live: `mix test --only live`.
    - gen: `buf generate` when `.proto` files exist, plus `oapi_generator` for client contracts;
      a no-op otherwise.
    - mutation: the Muex command above.
- Gotchas:
    - Boundary reports violations as compiler warnings: `check` must compile with
      `--warnings-as-errors`, or a violation passes. Confirm that a deliberate violation fails
      `mise run check` once while wiring.
    - Zoi strips unknown keys by default; a boundary schema built with `Zoi.map/2` directly is
      not strict. Build every boundary schema with the `{{VALIDATION_MODULE}}` constructors.
    - Zoi errors carry a path, a code, and a message, not the input, but a custom
      `error:`/refinement message can interpolate the input. `{{VALIDATION_MODULE}}` returns only
      path and code.
    - Elixir builds from Hex are compiled per OTP major: `elixir@latest` with an older
      pinned `erlang` gives a mismatched pair. Pin both exactly.
    - Hex, Rebar, and escripts live in `MIX_HOME`, so they are per project here; `setup` must
      reinstall them after a change of Elixir version.
    - The mutation task and the property run set `SKIP_FEATURES=1`: Muex runs plain `mix test`,
      and the root test helper would otherwise compile and run every feature per mutant.

## Any other language

Fill each placeholder by finding, in order of preference:

1. A Cucumber-family Gherkin runner. If none exists, use Given/When/Then-structured tests in the
   native runner, keeping `features/` as the spec, and record it under Project deviations.
2. A property-based testing library with shrinking.
3. A mutation testing tool that can be limited to the core's files and the property tests. If none
   exists, say so under Project deviations, and have the reviewer hand-mutate core logic instead.
4. A runtime validator driven by the language's own type declarations, with constraints declared
   on the type and errors that can be stripped of the failing value. Plus an OpenAPI generator and
   a Buf plugin for that language.
5. The language's strongest mechanism for module privacy, plus a linter or architecture test that
   fails on cross-module internal imports.
6. Its closest form of sum types with exhaustiveness checking.
7. Its idiomatic "not implemented" body for a declared function (`STUB_BODY`).

Never give up a rule silently because tooling is missing. Record every gap under Project deviations.
