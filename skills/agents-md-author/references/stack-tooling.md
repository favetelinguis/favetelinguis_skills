# Stack tooling map

Default values for the stack placeholders in `assets/AGENTS.md.template` and the prompt
templates in `assets/pi-prompts/`, per language. The supported stacks are TypeScript and Java.
Prefer a tool the project already uses when it can satisfy the rule.
Tool names, flags, and APIs drift over time: confirm each command with the tool's
`--help` or docs before writing it into AGENTS.md.

Contents

- [Shared conventions (all languages)](#shared-conventions-all-languages)
- [TypeScript / Node](#typescript--node)
- [Java 21+ / Kotlin (Maven)](#java-21--kotlin-maven)
- [Any other language](#any-other-language)

## Shared conventions (all languages)

- Layout is `apps/<app>/` (deployable entry points: wiring and the outermost shell) plus
  `libs/<module>/`, each with `features/`, `steps/`, `src/`, and `plan/` at the root, and
  `contracts/` only in a module that serves or calls an HTTP or gRPC interface.
  Adapt only what the toolchain forces (e.g. Maven `src/main/java/...`), and say so in the layout tree.
- Every module is a build module of the workspace root: a pnpm workspace package listed by
  `pnpm-workspace.yaml` (`libs/*`, `apps/*`), or a Maven module listed in the root aggregator
  `pom.xml`. No module is just a directory inside another build module.
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
  `contracts/` are written during `/vibe`. `{{CMD_GEN}}` generates code from every contract into
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
- Typical commands: `pnpm check`, `pnpm test`, `pnpm test:live`, `pnpm gen`, `pnpm mutation`
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
- Typical commands, all through the Maven wrapper (`mvn wrapper:wrapper`):
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
