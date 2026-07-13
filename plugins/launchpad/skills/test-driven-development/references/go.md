# Go Testing Patterns

Comprehensive Go-specific patterns for specification-grade testing.

## Dependencies

Standard import block for all test files:

```go
import (
    "testing"

    "github.com/stretchr/testify/assert"
    "github.com/stretchr/testify/require"
)
```

`testify` is the only testing dependency. No gomock, no testcontainers, no ginkgo.

If `testify` is not yet in `go.mod`, add it:

```bash
cd tools/cluster && go get github.com/stretchr/testify
```

## Table-Driven Tests

The default pattern for multiple scenarios:

```go
func TestFindService(t *testing.T) {
    tests := []struct {
        name    string
        setup   func(t *testing.T, dir string)
        input   string
        want    string
        wantErr string
    }{
        {
            name:  "exact match returns full path",
            setup: func(t *testing.T, dir string) { createJobFile(t, dir, "caddy") },
            input: "caddy",
            want:  "caddy.nomad.hcl",
        },
        {
            name:  "match with extension strips correctly",
            setup: func(t *testing.T, dir string) { createJobFile(t, dir, "caddy") },
            input: "caddy.nomad.hcl",
            want:  "caddy.nomad.hcl",
        },
        {
            name:    "missing service returns descriptive error",
            setup:   func(t *testing.T, dir string) {},
            input:   "nonexistent",
            wantErr: "not found",
        },
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            t.Parallel()
            cfg := setupTestConfig(t)
            tt.setup(t, cfg.NomadJobsDir)

            runner := NewRunner(cfg)
            got, err := runner.FindService(tt.input)

            if tt.wantErr != "" {
                require.Error(t, err)
                assert.Contains(t, err.Error(), tt.wantErr)
                return
            }
            require.NoError(t, err)
            assert.Contains(t, got, tt.want)
        })
    }
}
```

**When NOT to use tables:**
- Single-scenario tests — just write the test directly
- Tests needing complex per-case setup that doesn't fit a `func` field
- Tests where the struct definition is larger than the test body

## Test Naming

Pattern: `Test<Function>_<Scenario>_<Expected>`

Names read as specifications:

```go
// Services
func TestListServices_EmptyDir_ReturnsEmpty(t *testing.T)
func TestListServices_MultipleFiles_ReturnsSorted(t *testing.T)
func TestFindService_ExactMatch_ReturnsPath(t *testing.T)
func TestFindService_NotFound_ReturnsError(t *testing.T)

// Infrastructure
func TestListModules_IgnoresHiddenDirs(t *testing.T)
func TestListModules_IgnoresDirsWithoutTfFiles(t *testing.T)
func TestFindModule_NotADirectory_ReturnsError(t *testing.T)

// Validation
func TestValidate_InvalidJSON_ReturnsParseError(t *testing.T)
func TestValidate_MissingRequiredField_ListsFields(t *testing.T)

// E2E
func TestClusterInfo_ShowsAllSections(t *testing.T)
func TestClusterHelp_ShowsUsage(t *testing.T)
```

## Assertions

### `require` vs `assert`

- **`require`** — stops the test immediately. Use for preconditions
- **`assert`** — records failure, continues. Use for the checks themselves

```go
// Setup — use require (no point continuing if setup fails)
cfg, err := loadConfig(path)
require.NoError(t, err)
require.NotNil(t, cfg)

// Checks — use assert (see all failures at once)
assert.Equal(t, "caddy", cfg.Name)
assert.Equal(t, 8080, cfg.Port)
```

### Assertion Reference

```go
// Equality
assert.Equal(t, expected, actual)
assert.NotEqual(t, unexpected, actual)

// Errors
assert.NoError(t, err)
assert.Error(t, err)
assert.ErrorContains(t, err, "not found")
assert.ErrorIs(t, err, os.ErrNotExist)

// Collections
assert.Len(t, items, 3)
assert.Contains(t, items, "caddy")
assert.Empty(t, items)
assert.ElementsMatch(t, expected, actual)  // order-independent

// Strings
assert.Contains(t, output, "Validating")
assert.NotContains(t, output, "error")

// Nil / Boolean / Files
assert.Nil(t, result)
assert.NotNil(t, result)
assert.True(t, ok)
assert.FileExists(t, path)
assert.DirExists(t, dir)
```

## Helper Functions

Mark every helper with `t.Helper()` for accurate error reporting:

```go
func createJobFile(t *testing.T, dir, name string) {
    t.Helper()
    content := `job "` + name + `" { datacenters = ["dc1"] }`
    path := filepath.Join(dir, name+".nomad.hcl")
    require.NoError(t, os.WriteFile(path, []byte(content), 0644))
}
```

**When to extract helpers:**
- Same setup appears in 3+ tests → extract to file-local helper
- Same helper appears in 3+ packages → extract to `internal/testutil/`

### testutil Package

Shared helpers live in `internal/testutil/`. Pattern: fixture builders that
accept variadic args for flexibility.

```go
// SetupServiceDir creates a temp dir pre-populated with job files.
func SetupServiceDir(t *testing.T, services ...string) (string, *config.Config) {
    t.Helper()
    dir := t.TempDir()
    jobsDir := filepath.Join(dir, "nomad/jobs")
    require.NoError(t, os.MkdirAll(jobsDir, 0755))
    for _, svc := range services {
        WriteFile(t, jobsDir, svc+".nomad.hcl",
            `job "`+svc+`" { datacenters = ["dc1"] }`)
    }
    return dir, &config.Config{RepoRoot: dir, NomadJobsDir: jobsDir}
}
```

## Temporary Directories and Environment

```go
dir := t.TempDir()                              // auto-cleaned after test
t.Setenv("NOMAD_ADDR", "http://localhost:4646") // auto-restored after test
```

## CLI Binary Testing (E2E)

Layer 3 — execute the real binary. E2E tests live in `test/` and assert on
exit codes, stdout, and stderr:

```go
func TestClusterInfo_ShowsAllSections(t *testing.T) {
    binary := clusterBinaryPath(t)  // helper that t.Skip()s if not built

    cmd := exec.Command(binary, "info")
    output, err := cmd.CombinedOutput()
    require.NoError(t, err, "cluster info failed: %s", output)

    for _, section := range []string{"Nodes", "Groups", "Services"} {
        assert.Contains(t, string(output), section)
    }
}
```

## Testing Cobra Commands

For testing command logic without building the full binary (Layer 1/2), set up
the command directly and capture output:

```go
func TestInfoCommand_ShowsAllSections(t *testing.T) {
    cmd := newInfoCmd()
    buf := new(bytes.Buffer)
    cmd.SetOut(buf)
    cmd.SetArgs([]string{})

    require.NoError(t, cmd.Execute())

    output := buf.String()
    for _, section := range []string{"Nodes", "Groups", "Services"} {
        assert.Contains(t, output, section)
    }
}
```

For commands that need config, inject via the command's context or a setup helper.
Use E2E binary tests (Layer 3) for full CLI integration — Cobra command tests
complement those by covering command-level logic without the binary build step.

## Testing Bubble Tea Models

Test `Update()` by sending `tea.Msg` values and asserting on the returned model.
Test `View()` by asserting on the rendered string.

```go
func TestMenuUpdate_SpaceTogglesSelection(t *testing.T) {
    m := newTestModel([]string{"caddy-dns", "grafana-dashboards"})

    result, _ := m.Update(tea.KeyMsg{Type: tea.KeyRunes, Runes: []rune{' '}})
    updated := result.(model)

    assert.True(t, updated.selectedModules[0], "space should toggle first module on")
}

func TestMenuView_ShowsAllOptions(t *testing.T) {
    m := newTestModel([]string{"caddy-dns", "grafana-dashboards"})

    view := m.View()

    assert.Contains(t, view, "caddy-dns")
    assert.Contains(t, view, "grafana-dashboards")
}
```

Keep TUI tests focused on state transitions (Update) and visible output (View).
Don't test rendering details like exact spacing or ANSI codes — those are
implementation details that break on terminal width changes.

## Testing Runners

The project follows a consistent pattern: `NewRunner(cfg)` → `runner.Action()`.
Most runner methods interact with the filesystem (listing files, reading configs).

**Default approach (Layer 1):** Create a temp dir with `t.TempDir()`, populate it
with test fixtures, pass a config pointing at the temp dir.

**When the runner shells out** (Layer 2): Use the CommandRunner interface pattern
below.

## CommandRunner Pattern (Boundary Fakes)

Layer 2 — for logic that shells out to external tools. Define a narrow
interface, inject a fake in tests:

```go
type CommandRunner interface {
    Run(name string, args ...string) ([]byte, error)
}

// Fake records calls and returns canned responses
type FakeRunner struct {
    Output []byte
    Err    error
    Calls  [][]string
}

func (f *FakeRunner) Run(name string, args ...string) ([]byte, error) {
    f.Calls = append(f.Calls, append([]string{name}, args...))
    return f.Output, f.Err
}

// Test uses the fake
func TestValidateService_PassesCorrectArgs(t *testing.T) {
    fake := &FakeRunner{Output: []byte("ok")}
    runner := NewRunner(cfg, WithCommandRunner(fake))

    require.NoError(t, runner.Validate("caddy"))
    require.Len(t, fake.Calls, 1)
    assert.Equal(t, "nomad", fake.Calls[0][0])
}
```

Use sparingly — most tests should use filesystem isolation (Layer 1).

## Skipping Tests

Guard tests that need external tools or environment:

```go
if _, err := exec.LookPath("nomad"); err != nil {
    t.Skip("nomad not found in PATH")
}
if os.Getenv("NOMAD_ADDR") == "" {
    t.Skip("NOMAD_ADDR not set")
}
```

## Parallel Tests

Use `t.Parallel()` in table-driven subtests — each subtest gets its own `t.TempDir()`
so there's no shared state to conflict:

```go
for _, tt := range tests {
    t.Run(tt.name, func(t *testing.T) {
        t.Parallel()
        // each subtest is isolated via t.TempDir()
    })
}
```

**Don't parallelize** when tests share mutable state (package-level variables,
environment variables). `t.Setenv` is not parallel-safe with the parent test — only
use it in non-parallel tests or in subtests where the parent doesn't also call
`t.Parallel()`.

## Test Fixtures

Keep fixtures minimal — the smallest structure that exercises the contract, nothing
more. A Nomad job fixture doesn't need real task config if you're testing file
discovery.

- **`t.TempDir()`** — default. Dynamic files that tests create, modify, and assert on.
  Each test gets a fresh directory; cleanup is automatic.
- **`testdata/`** — static, read-only fixtures checked into the repo. Use for complex
  structures that would be tedious to build programmatically (full config files, golden
  output files). Go tooling ignores `testdata/` directories.

Prefer `t.TempDir()` unless the fixture is complex enough that building it in code
would obscure the test's intent.

```go
data, err := os.ReadFile("testdata/valid-job.nomad.hcl")  // static fixture
dir := t.TempDir()                                         // dynamic workspace
```

## Setup and Teardown

Prefer per-test `t.Helper()` functions — they're simpler, parallel-safe, and
auto-cleanup:

```go
func setupTestConfig(t *testing.T) *config.Config {
    t.Helper()
    dir := t.TempDir()
    require.NoError(t, os.MkdirAll(filepath.Join(dir, "nomad/jobs"), 0755))
    return &config.Config{RepoRoot: dir, NomadJobsDir: filepath.Join(dir, "nomad/jobs")}
}
```

Use `TestMain` only for expensive one-time setup (building a binary for E2E tests).

## Golden Files

For complex output comparison. Update with `go test -run TestOutput -update`:

```go
var update = flag.Bool("update", false, "update golden files")

func TestOutput_MatchesGolden(t *testing.T) {
    got := generateOutput()
    golden := filepath.Join("testdata", t.Name()+".golden")
    if *update {
        require.NoError(t, os.WriteFile(golden, []byte(got), 0644))
    }
    want, err := os.ReadFile(golden)
    require.NoError(t, err)
    assert.Equal(t, string(want), got)
}
```
