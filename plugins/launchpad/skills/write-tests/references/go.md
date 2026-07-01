# Go Testing Patterns

Comprehensive Go-specific patterns for specification-grade testing. The guiding
rule: **test the observable contract, and mock only at the process/network
boundary — never inside your own code.**

## Dependencies

Standard library `testing` only — no assertion framework. Tests read as
`if got != want { t.Errorf(...) }`, which keeps failures explicit and adds no
dependency to the module.

```go
import (
    "reflect"
    "strings"
    "testing"
)
```

For value comparison use `==` (scalars) or `reflect.DeepEqual` (slices/maps/
structs). For substrings use `strings.Contains`. For error identity/shape use
`errors.Is` / `errors.As`. If a project already standardises on `testify`, match
it — but do not introduce it into a stdlib codebase.

## Assertions (stdlib)

Two roles, mirroring `require` vs `assert`:

- **Precondition failure → `t.Fatalf`** (stop; the rest of the test is moot).
- **Behavior check → `t.Errorf`** (record and continue; see all failures at once).

```go
// Precondition — stop if setup fails
cfg, err := config.Load()
if err != nil {
    t.Fatalf("Load() error = %v", err)
}

// Checks — continue so every failure surfaces
if got := cfg.Name; got != "caddy" {
    t.Errorf("Name = %q, want %q", got, "caddy")
}
if got := cfg.Port; got != 8080 {
    t.Errorf("Port = %d, want %d", got, 8080)
}
```

Common shapes:

```go
if !reflect.DeepEqual(got, want) { t.Errorf("argv = %v, want %v", got, want) }
if !strings.Contains(out, "Validating") { t.Errorf("output missing marker: %q", out) }
if err == nil { t.Fatal("expected an error, got nil") }
if !strings.Contains(err.Error(), "not found") { t.Errorf("error = %q, want 'not found'", err) }
if !errors.Is(err, os.ErrNotExist) { t.Errorf("want ErrNotExist, got %v", err) }
if errors.Unwrap(err) == nil { t.Errorf("error %q should wrap a cause", err) }
```

Assert on the **observable behavior** — return values, error message/shape,
stdout/stderr, the command a runner built, the request a client sent. Never
assert on internal calls or private state.

## Table-Driven Tests

The default pattern for multiple scenarios of one function:

```go
func TestPercentCheck_Boundaries(t *testing.T) {
    const warn, fail = 80.0, 90.0
    cases := []struct {
        name string
        val  float64
        want Status
    }{
        {"exactly at fail is Fail", 90.0, StatusFail},
        {"just below fail is Warn", 89.9, StatusWarn},
        {"exactly at warn is Warn", 80.0, StatusWarn},
        {"just below warn is OK", 79.9, StatusOK},
    }
    for _, c := range cases {
        t.Run(c.name, func(t *testing.T) {
            got := percentCheck("Disk", oneSample("node-00", c.val), nil, warn, fail, instanceLabel)
            if got.Status != c.want {
                t.Errorf("value %.1f: got %v, want %v", c.val, got.Status, c.want)
            }
        })
    }
}
```

Enumerate the edges explicitly: empty, single, uneven, boundary (`>=` vs `>`),
off-by-one, nil. Boundary and empty cases are where real bugs hide.

**When NOT to use tables:** single-scenario tests, cases needing complex per-case
setup, or where the struct is larger than the test body.

## Test Naming

Pattern: `Test<Function>_<Scenario>_<Expected>` — names read as specifications:

```go
func TestResolveLimit_UnknownNode_ListsAvailable(t *testing.T)
func TestRunPreview_IsDryRunAtWire(t *testing.T)
func TestDeleteVolume_WireArgv(t *testing.T)
func TestControlPlane_EmptyNodes_Fails(t *testing.T)
```

## Mocking at the Wire — Fake Executables on PATH

For code that shells out (`exec.Command("nomad", ...)`), install a fake
executable of that name on `PATH` that records its argv and working directory,
then assert the exact command the code built. This tests the real contract — the
command line — and survives refactors, unlike an injected interface.

Extract the recorder into a shared `internal/testutil` package once more than one
package needs it (it imports `testing`, so it is only ever imported from
`_test.go` files and never enters the production binary):

```go
// internal/testutil/exec.go
package testutil

type Options struct {
    ExitCode int
    Stdout   string // exact bytes echoed to stdout on each call
}

type Recorder struct{ /* ... */ }

func (r *Recorder) Args() []string    { /* argv of the last call */ }
func (r *Recorder) Cwd() string       { /* working dir of the last call */ }
func (r *Recorder) Count() int        { /* number of invocations */ }
func (r *Recorder) Calls() []Invocation

// FakeExec writes a fake `name` into a temp dir, prepends it to PATH (restored
// by t.Setenv), and records argv + cwd. Deliver Stdout via a sidecar file the
// script `cat`s — not string-interpolated — so multi-line JSON survives intact.
func FakeExec(t *testing.T, name string, opts Options) *Recorder { /* ... */ }
```

Using it — assert the exact argv and the directory the command ran in:

```go
func TestDeployService_WireArgv(t *testing.T) {
    cfg := setupTestConfig(t)
    rec := testutil.FakeExec(t, "nomad", testutil.Options{})

    if err := NewRunner(cfg).DeployService("caddy.nomad.hcl"); err != nil {
        t.Fatalf("DeployService() error = %v", err)
    }

    want := []string{"job", "run", "caddy.nomad.hcl"}
    if got := rec.Args(); !reflect.DeepEqual(got, want) {
        t.Errorf("argv = %v, want %v", got, want)
    }
}
```

The fake's `Stdout` feeds multi-call flows (e.g. `nomad job allocs -json` →
parse → `nomad alloc logs <id>`): return the JSON as `Options.Stdout`, then
assert the second call's argv via `rec.Calls()`. A non-zero `ExitCode` lets you
prove error propagation.

**Do not** instead define `type CommandRunner interface { Run(...) }` and assert
`fake.Calls[0][0] == "nomad"` — that only proves the code called your fake, not
that it built the right command, and it couples the test to an interface that
exists solely for testing.

## Mocking at the Wire — httptest

For an HTTP client, point it at an `httptest.Server` and assert both the request
sent and that a real response parses. Key the handler on **method and path** and
decode the body — a path-only mock lets a write silently downgrade to `GET`:

```go
func TestCreateChannel_PostsWrappedBody(t *testing.T) {
    var got struct {
        method, path string
        body         []byte
    }
    srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        got.method, got.path = r.Method, r.URL.Path
        got.body, _ = io.ReadAll(r.Body)
        _, _ = w.Write([]byte(`{"id":"srv-assigned"}`))
    }))
    defer srv.Close()

    c := New(srv.URL, 5*time.Second)
    out, err := c.CreateChannel(context.Background(), Channel{Name: "Kids"})
    if err != nil {
        t.Fatalf("CreateChannel: %v", err)
    }
    if got.method != http.MethodPost || got.path != "/api/channels" {
        t.Errorf("request = %s %s, want POST /api/channels", got.method, got.path)
    }
    var sent struct{ Channel Channel `json:"channel"` }
    if err := json.Unmarshal(got.body, &sent); err != nil {
        t.Fatalf("decode body: %v", err)
    }
    if sent.Channel.Name != "Kids" {
        t.Errorf("sent channel = %+v, want Kids", sent.Channel)
    }
    if out.ID != "srv-assigned" { t.Errorf("id = %q, want srv-assigned", out.ID) }
}
```

## Proving the Negative for Destructive Ops

For a dry-run, a declined confirmation, or an empty-input guard, wire the fake
boundary to **fail the test** if a mutating call arrives. "Did not mutate"
becomes structural, not an afterthought:

```go
srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
    if r.Method == http.MethodPost && strings.HasSuffix(r.URL.Path, "/programming") {
        t.Errorf("MUTATION LEAK: unexpected POST %s (channel would be overwritten)", r.URL.Path)
    }
    // ... serve the reads the code needs ...
}))
```

The same shape works for exec: after driving the "should not act" path, assert
`rec.Count() == 0` — the fake `nomad`/`terraform` must never have run.

## Helper Functions

Mark every helper with `t.Helper()` for accurate failure line numbers:

```go
func createJobFile(t *testing.T, dir, name string) {
    t.Helper()
    path := filepath.Join(dir, name+".nomad.hcl")
    if err := os.WriteFile(path, []byte(`job "`+name+`" {}`), 0644); err != nil {
        t.Fatalf("write job file: %v", err)
    }
}
```

Extract to a file-local helper at 3+ uses in a package; extract to
`internal/testutil` at 3+ packages.

## Temporary Directories and Environment

```go
dir := t.TempDir()                              // auto-cleaned
t.Setenv("PATH", dir+":"+os.Getenv("PATH"))     // auto-restored (not parallel-safe)
```

When a test changes the process working directory or `os.Stdin`/`os.Stdout`, it
cannot be `t.Parallel()`.

## Testing Cobra Commands In-Process

Command-layer coverage must be **in-process** — a subprocess test (below) does
not count toward the command package's coverage. Execute the command's `RunE`
directly. If the command prints via `fmt.Printf` to the real `os.Stdout` (common)
rather than `cmd.OutOrStdout()`, capture the OS-level stream:

```go
// captureOutput redirects the real os.Stdout/os.Stderr around fn.
func captureOutput(t *testing.T, fn func()) (stdout, stderr string) {
    t.Helper()
    origOut, origErr := os.Stdout, os.Stderr
    outR, outW, _ := os.Pipe()
    errR, errW, _ := os.Pipe()
    os.Stdout, os.Stderr = outW, errW
    outC, errC := make(chan string, 1), make(chan string, 1)
    go func() { var b bytes.Buffer; io.Copy(&b, outR); outC <- b.String() }()
    go func() { var b bytes.Buffer; io.Copy(&b, errR); errC <- b.String() }()
    func() {
        defer func() { os.Stdout, os.Stderr = origOut, origErr; outW.Close(); errW.Close() }()
        fn()
    }()
    return <-outC, <-errC
}
```

Combine with a `PATH` fake (fake `uv`/`nomad`) and, for confirmation prompts that
read `os.Stdin` directly, a stdin swap. Reset any package-level flag globals you
set via `t.Cleanup`.

For `os.Exit` code contracts (e.g. a health command that exits 0/1/2), either
extract a pure function that returns the code and test that directly, or drive
the **built binary** as a subprocess and assert on its exit code — a wrapped
`os.Exit` in-process cannot be observed.

## CLI Binary Testing (E2E)

End-to-end tests that run the real binary live in `test/`. Build the binary once
in `TestMain` — **never `t.Skip()` when it is absent** (that skip is a
false-green: the coverage gate runs `go test` without building first, so the test
silently passes):

```go
var builtBinary string

func TestMain(m *testing.M) {
    tmp, err := os.MkdirTemp("", "cli-bin")
    if err != nil { log.Fatalf("mkdir temp: %v", err) }
    bin := filepath.Join(tmp, "cluster")
    build := exec.Command("go", "build", "-o", bin, "./cmd/cluster")
    build.Dir = ".." // module root
    if out, err := build.CombinedOutput(); err != nil {
        os.RemoveAll(tmp)
        log.Fatalf("build failed: %v\n%s", err, out) // hard fail, not skip
    }
    builtBinary = bin
    code := m.Run()
    os.RemoveAll(tmp) // os.Exit skips defers — clean up explicitly
    os.Exit(code)
}

func TestClusterInfo_ShowsAllSections(t *testing.T) {
    out, err := exec.Command(builtBinary, "info").CombinedOutput()
    if err != nil { t.Fatalf("cluster info failed: %v\n%s", err, out) }
    for _, section := range []string{"NODES", "GROUPS", "SERVICES"} {
        if !strings.Contains(string(out), section) {
            t.Errorf("output missing section %q", section)
        }
    }
}
```

Assert on the **real** headers/content the binary prints — verify against source,
not against assumptions (a stale assertion that never matches will pass only
because the test was skipping).

## Testing Bubble Tea Models

Test `Update()` by sending `tea.Msg` values and asserting the returned model;
test `View()` on the rendered string. Keep to state transitions and visible
output — not exact spacing or ANSI codes:

```go
func TestMenuUpdate_SpaceTogglesSelection(t *testing.T) {
    m := newTestModel([]string{"caddy-dns", "grafana-dashboards"})
    result, _ := m.Update(tea.KeyMsg{Type: tea.KeyRunes, Runes: []rune{' '}})
    if !result.(model).selectedModules[0] {
        t.Error("space should toggle the first module on")
    }
}
```

## Skipping Tests

Skip **only** for a test that genuinely needs a *running* external service (a
live Nomad/Consul cluster) — never for a missing binary or a tool you can fake:

```go
func TestServicesValidate_NoArgs(t *testing.T) {
    if os.Getenv("NOMAD_ADDR") == "" {
        t.Skip("NOMAD_ADDR not set") // needs a live cluster
    }
    // ...
}
```

Anything testable without the live service should use a wire fake instead — a
skip that hides testable behavior is a false-green.

## Parallel Tests

Use `t.Parallel()` in table-driven subtests where each is isolated by its own
`t.TempDir()`:

```go
for _, tt := range tests {
    t.Run(tt.name, func(t *testing.T) {
        t.Parallel()
        // isolated via t.TempDir()
    })
}
```

**Don't parallelize** tests that mutate shared state — package-level variables,
`os.Stdin`/`os.Stdout`, the working directory, or `t.Setenv` (not parallel-safe
with the parent test).

## Determinism

Non-deterministic tests are worse than none — they train the team to ignore red.
Two frequent sources, both real bugs when they reach production code:

- **Map iteration order.** Ranging a `map` for anything order-sensitive (picking
  a winner, applying overlapping string replacements) is nondeterministic. Sort
  keys first, or use an ordered slice.
- **Unseeded randomness / time.** Seed RNGs from a fixed value and inject clocks;
  assert reproducibility (same seed → same output) explicitly.

## Test Fixtures

Keep fixtures minimal — the smallest structure that exercises the contract.

- **`t.TempDir()`** — default. Dynamic files tests create and assert on.
- **`testdata/`** — static, read-only fixtures checked in (Go tooling ignores it).
  Use for complex payloads (full config or golden output files).

```go
data, err := os.ReadFile("testdata/valid-job.nomad.hcl") // static fixture
dir := t.TempDir()                                        // dynamic workspace
```

## Golden Files

For complex output comparison, update with `go test -run TestOutput -update`:

```go
var update = flag.Bool("update", false, "update golden files")

func TestOutput_MatchesGolden(t *testing.T) {
    got := generateOutput()
    golden := filepath.Join("testdata", t.Name()+".golden")
    if *update {
        if err := os.WriteFile(golden, []byte(got), 0644); err != nil {
            t.Fatal(err)
        }
    }
    want, err := os.ReadFile(golden)
    if err != nil { t.Fatal(err) }
    if got != string(want) { t.Errorf("output != golden; run -update if intended") }
}
```
