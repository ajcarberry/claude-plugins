---
name: write-tests
description: Use when writing tests, adding test coverage, choosing test types, testing a specific function, or when asked "should I mock this", "how should I test this", "write tests for", "add tests", "test this function", "write integration tests", or "rewrite test suite". Provides three-layer testing strategy, specification-grade testing workflow, boundary mocking, and Go-specific patterns including Cobra command, Bubble Tea model, and runner testing.
---

# Writing Specification-Grade Tests

Tests are the long-term moat of this codebase. They define the contract first, give
confidence second, and serve as documentation third.

> "Tests are the new moat — an investment that compounds."

**Three purposes, in priority order:**

1. **Specification** — tests define what the code *must* do
2. **Confidence** — tests prove the code *does* do it
3. **Documentation** — tests show *how* to use the code

Any agent should be able to run the test suite and know within seconds whether the
system is healthy. Write tests as runnable acceptance criteria — they are the primary
feedback mechanism in the development loop.

## Before Writing Tests

1. Read existing tests in the package — match style and conventions
2. Check `internal/testutil/` (or `test/`) for reusable helpers before writing new ones
3. Consult [references/go.md](references/go.md) for Go-specific patterns and examples
4. Default to **table-driven** structure for multiple scenarios

## Black-Box Testing

Default to testing the public API only. Test what the code does, not how it does it.

**Use white-box testing only when** testing unexported helpers with complex branching.
Match the existing package convention, but prefer black-box for new test files.

## Test Organization

```
tools/cluster/
├── internal/
│   ├── services/
│   │   ├── runner.go
│   │   └── runner_test.go        # Co-located, package-level tests
│   ├── infrastructure/
│   │   ├── runner.go
│   │   └── runner_test.go
│   └── testutil/                 # Shared helpers (extract when used 3+ times)
│       └── helpers.go
└── test/                         # E2E tests (binary execution)
    ├── integration_test.go
    ├── helpers_test.go
    └── testdata/                 # Static fixtures
```

- **Co-located tests** — default. Test file lives next to the code it tests
- **`internal/testutil/`** — shared helpers used across multiple packages
- **`test/`** — E2E tests that execute the built binary
- **`testdata/`** — static fixtures (ignored by Go tooling)

## Three-Layer Testing Strategy

> "The more your tests resemble the way your software is used, the more
> confidence they can give you." — Kent C. Dodds

**Every testable behavior gets a Layer 3 (E2E) test.** Layers 1 and 2 supplement
Layer 3 — they keep CI green when real tools aren't available, but they never
replace E2E coverage.

| Layer | Technique              | Purpose                                       |
|-------|------------------------|-----------------------------------------------|
| 3     | Real execution (E2E)   | **Required.** Proves the real thing works      |
| 1     | Filesystem isolation   | CI fallback — logic with real files via `t.TempDir()` |
| 2     | Interface-based fakes  | CI fallback — verifies command wiring only     |

**Layer 3 is the standard.** Build the binary, run real commands, assert on real
output. Guard E2E tests with `t.Skip()` when the environment isn't available
(missing binary, no cluster) — but the tests must exist.

**Layers 1 and 2 are CI safety nets.** They catch regressions fast when E2E can't
run. Layer 2 fakes can only verify your code builds the *intended* command — they
cannot prove the command actually works. Treat them as regression guards, not proof
of correctness.

**Choosing the primary layer by function type:**
- Reads/writes files → **Layer 1** (integration with `t.TempDir()`)
- Shells out to external tools → **Layer 2** (boundary fake) + **Layer 3** (E2E with `t.Skip()`)
- Pure computation → **Unit test**
- State machine (TUI) → State transition tests (send messages, assert model)

**Mock at the boundary, not inside:**
- External commands (nomad, terraform, ansible) — define a narrow interface, inject a fake
- Filesystem operations — use `t.TempDir()` with real reads and writes, not mocks
- Internal modules and your own code — always use the real thing

See [references/go.md](references/go.md) for the CommandRunner pattern.

## Table-Driven Tests

Default structure when you have multiple scenarios for the same function. Each case
gets a `name`, `setup`, `input`, `want`, and `wantErr` field. Run subtests with
`t.Run` and `t.Parallel()`.

See [references/go.md](references/go.md) for the full pattern with examples.

**When NOT to use tables:** single-scenario tests, tests needing complex per-case
setup, or tests where the table struct would be larger than the test body.

## Test Naming

Pattern: `Test<Function>_<Scenario>_<Expected>`

Names should read as specifications:

```
TestListServices_EmptyDir_ReturnsEmpty
TestFindModule_NotADirectory_ReturnsError
TestListModules_IgnoresHiddenDirs
TestClusterInfo_ShowsAllSections
TestValidate_InvalidJSON_ReturnsParseError
```

## Assertion Strategy

Two assertion modes, each with a specific role:

- **`require`** (stop-on-failure) — for preconditions. If setup fails, the rest of
  the test is meaningless.
- **`assert`** (continue-on-failure) — for the checks themselves. Seeing all failures
  at once is more diagnostic than stopping at the first.

See [references/go.md](references/go.md) for the full assertion reference.

| Context | Assert On                 | Avoid                       |
|---------|---------------------------|-----------------------------|
| CLI     | Exit code, stdout/stderr  | Internal function calls     |
| Files   | File exists, content      | Internal write calls        |
| API     | Response body, status     | Internal DB state           |
| Library | Return values, errors     | Private methods             |
| Errors  | Error message, error type | Whether error was logged    |

## Anti-Patterns

| Bad Pattern                      | Good Pattern                               |
|----------------------------------|--------------------------------------------|
| Testing mock behavior            | Test actual outcome with real dependencies |
| One assertion per function       | Group related assertions in one test       |
| Copy-pasting setup across tests  | Extract to `t.Helper()` function           |
| Percentage-based coverage goals  | Cover behavior and edge cases              |
| `sleep(500)` for timing          | Use condition-based waiting                |
| Asserting on internal state      | Assert on observable output                |
| Test-only methods in production  | Move to test utilities                     |
| Testing implementation details   | Test behavior and contract                 |
| Non-deterministic tests (random data, timing) | Deterministic tests with fixed inputs and isolated state |

## Quality Checklist

- [ ] Happy path covered
- [ ] Error conditions and edge cases handled
- [ ] Error messages asserted (not just `wantErr: true`)
- [ ] Real dependencies used (fakes only at external boundaries)
- [ ] Tests survive refactoring
- [ ] Test names read as specifications
- [ ] Table-driven where multiple scenarios exist
- [ ] Shared helpers extracted to `testutil` (if used 3+ times)
- [ ] `t.Parallel()` in table-driven subtests
- [ ] `t.Helper()` on all helper functions

---

**Remember:** Specification over verification. Real over mocked. Behavior over implementation.
