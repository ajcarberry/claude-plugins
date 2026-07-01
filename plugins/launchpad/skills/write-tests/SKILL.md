---
name: write-tests
description: Use when writing tests, adding test coverage, choosing test types, testing a specific function, or when asked "should I mock this", "how should I test this", "write tests for", "add tests", "test this function", "write integration tests", or "rewrite test suite". Provides a boundary-first testing strategy (wire-level fakes, httptest, in-process commands), specification-grade workflow, and Go-specific patterns including Cobra command, Bubble Tea model, and runner testing.
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

## Testing Strategy: Test at the Boundary

> "The more your tests resemble the way your software is used, the more
> confidence they can give you." — Kent C. Dodds

Test the observable contract, and mock only at the process/network boundary —
never inside your own code.

| What the code does | How to test it |
|--------------------|----------------|
| Pure computation | Call it with constructed inputs; assert the return and its edge cases |
| Reads/writes files | Real files in `t.TempDir()` — no filesystem mocks |
| Shells out to a tool (nomad/terraform/uv) | Fake the executable on `PATH`, record its argv, assert the exact command built |
| Talks HTTP (an API, Prometheus, Loki) | `httptest.Server` — assert the request sent, parse a real response |
| Command (Cobra) | Execute it in-process; assert stdout/stderr and error/exit behavior |
| State machine (TUI) | Send messages to `Update`, assert the returned model; assert `View` output |

**Mock at the wire, never internals.** For a runner that does
`exec.Command("nomad", "job", "run", path)`, install a fake `nomad` on `PATH`
that records its argv, then assert the argv. Do **not** define a `CommandRunner`
interface and assert "Run was called" — that proves the code called your fake,
not that it built the right command, and it breaks on harmless refactors. Same
for HTTP: point the client at an `httptest.Server`; don't stub the client type.
Your own internal modules are always used for real.

**Build the binary; never skip on its absence.** End-to-end tests that run the
built CLI belong in `test/`, and `TestMain` builds the binary once before they
run — a missing binary is a hard failure, not a `t.Skip()`. (Skipping here is a
false-green: if the coverage gate runs `go test` without building first, every
skipped test silently "passes.") A subprocess test does not count toward the
tested package's coverage, so cover command logic **in-process** as well.

**Prove the negative for destructive ops.** For a dry-run, a declined
confirmation, or an empty-input guard, wire the fake boundary to **fail the
test** if a mutating call arrives — making "did not mutate" a structural
guarantee, not an assertion a later edit could quietly drop.

See [references/go.md](references/go.md) for the wire-fake, `httptest`, and
in-process command patterns.

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
| Interface fake asserting "method X was called" | Fake the executable on `PATH` / `httptest`; assert the real argv or request |
| Asserting a struct literal you just built | Assert the effect through the boundary (the flag the fake received) |
| `t.Skip()` on a missing-but-buildable binary/tool | Build it in `TestMain`; skip only a genuinely external live service |
| Regression test that passes without the fix | Ensure it fails against the pre-fix code |
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
- [ ] Boundaries mocked at the wire (fake exec on `PATH` / `httptest`), not via internal interfaces
- [ ] Destructive-op guards prove the negative (the fake fails the test on any mutating call)
- [ ] A bug fix ships a regression test that fails before the fix
- [ ] Tests survive refactoring
- [ ] Test names read as specifications
- [ ] Table-driven where multiple scenarios exist
- [ ] Shared helpers extracted to `testutil` (if used 3+ times)
- [ ] `t.Parallel()` in table-driven subtests
- [ ] `t.Helper()` on all helper functions

---

**Remember:** Specification over verification. Real over mocked. Behavior over implementation.
