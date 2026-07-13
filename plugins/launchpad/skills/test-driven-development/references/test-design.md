# Test Design — Specification-Grade Tests

Tests define the contract first, give confidence second, and serve as documentation
third.

**Three purposes, in priority order:**

1. **Specification** — tests define what the code *must* do
2. **Confidence** — tests prove the code *does* do it
3. **Documentation** — tests show *how* to use the code

Any agent should be able to run the test suite and know within seconds whether the
system is healthy. Write tests as runnable acceptance criteria.

## Before Writing Tests

1. Read existing tests in the package — match style and conventions
2. Check for reusable helpers (`internal/testutil/`, `test/`) before writing new ones
3. Default to **table-driven** structure for multiple scenarios

## Black-Box Testing

Default to testing the public API only. Test what the code does, not how it does it.
Use white-box testing only for unexported helpers with complex branching; prefer
black-box for new test files.

## Three-Layer Strategy

> "The more your tests resemble the way your software is used, the more confidence
> they can give you." — Kent C. Dodds

**Every testable behavior gets a Layer 3 (E2E) test.** Layers 1 and 2 supplement
Layer 3 — they keep CI green when real tools aren't available, but never replace E2E
coverage.

| Layer | Technique | Purpose |
|-------|-----------|---------|
| 3 | Real execution (E2E) | **Required.** Proves the real thing works |
| 1 | Filesystem isolation | CI fallback — logic with real files via temp dirs |
| 2 | Interface-based fakes | CI fallback — verifies command wiring only |

Guard E2E tests with skip conditions when the environment isn't available — but the
tests must exist. Layer 2 fakes can only verify your code builds the *intended*
command; they cannot prove the command works. Regression guards, not proof.

**Choosing the primary layer by function type:**
- Reads/writes files → Layer 1 (temp-dir integration)
- Shells out to external tools → Layer 2 (boundary fake) + Layer 3 (E2E, skippable)
- Pure computation → unit test
- State machine (TUI) → state transition tests (send messages, assert model)

**Mock at the boundary, not inside:**
- External commands (nomad, terraform, ansible) — narrow interface, inject a fake
- Filesystem — real reads/writes in temp dirs, not mocks
- Internal modules and your own code — always the real thing

## Table-Driven Tests

Default structure for multiple scenarios of the same function: each case gets `name`,
`setup`, `input`, `want`, `wantErr`; run as parallel subtests. **When NOT to use
tables:** single-scenario tests, complex per-case setup, or when the table struct
would be larger than the test body.

## Naming

Pattern: `Test<Function>_<Scenario>_<Expected>` — names read as specifications:

```
TestListServices_EmptyDir_ReturnsEmpty
TestFindModule_NotADirectory_ReturnsError
TestValidate_InvalidJSON_ReturnsParseError
```

## Assertion Strategy

- **require** (stop-on-failure) — preconditions; if setup fails, the rest is meaningless
- **assert** (continue-on-failure) — the checks; seeing all failures at once is diagnostic

| Context | Assert on | Avoid |
|---------|-----------|-------|
| CLI | Exit code, stdout/stderr | Internal function calls |
| Files | Existence, content | Internal write calls |
| API | Response body, status | Internal DB state |
| Library | Return values, errors | Private methods |
| Errors | Message, type | Whether error was logged |

## Anti-Patterns

| Bad | Good |
|-----|------|
| Testing mock behavior | Test actual outcome with real dependencies |
| One assertion per function | Group related assertions in one test |
| Copy-pasted setup | Extract to helper functions |
| Percentage coverage goals | Cover behavior and edge cases |
| `sleep(500)` for timing | Condition-based waiting (see systematic-debugging references) |
| Asserting internal state | Assert observable output |
| Test-only methods in production | Move to test utilities |
| Non-deterministic tests | Fixed inputs, isolated state |

## Quality Checklist

- [ ] Happy path and error/edge cases covered
- [ ] Error messages asserted (not just "an error occurred")
- [ ] Real dependencies; fakes only at external boundaries
- [ ] Tests survive refactoring; names read as specifications
- [ ] Table-driven where multiple scenarios exist
- [ ] Shared helpers extracted when used 3+ times

**Remember:** specification over verification. Real over mocked. Behavior over
implementation.
