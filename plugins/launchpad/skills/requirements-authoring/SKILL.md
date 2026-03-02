---
name: requirements-authoring
description: This skill should be used when "writing requirements", "structuring an implementation plan", "adding traceability", "writing verification checks", "authoring requirements with R/S/V IDs", or producing a requirements document for any implementation task. Provides EARS (Easy Approach to Requirements Syntax) patterns — ubiquitous, event-driven, state-driven, and unwanted behavior — with RFC 2119 priority language (SHALL/SHOULD/MAY), sub-requirement hierarchies, R/S/V traceability, phased implementation steps, and verification anti-patterns. Use this skill whenever someone needs to write structured, verifiable requirements — even if they don't explicitly ask for "EARS" or "requirements authoring."
---

# Requirements Authoring — EARS Patterns & Traceability

Structured methodology for authoring implementation requirements. Defines the requirement pattern language, priority levels, sub-requirement hierarchy, phased implementation steps, and traceability scheme that produce clear, verifiable plans.

## Quick Reference

| Pattern | Template | Keyword |
|---------|----------|---------|
| Event-Driven | `When [trigger], the [system] SHALL [action].` | "When" |
| State-Driven | `While [state], the [system] SHALL [action].` | "While" |
| Unwanted | `If [condition], then the [system] SHALL [mitigation].` | "If...then" |
| Ubiquitous | `The [system] SHALL [action].` | always true |

| Priority | Meaning (RFC 2119) |
|----------|-------------------|
| SHALL | Absolute requirement — must be implemented |
| SHOULD | Recommended — strong reason to implement, but valid exceptions may exist |
| MAY | Optional — implement if beneficial, omit without justification |

### Choosing the Pattern

- Specific trigger event? → **Event-Driven** (When)
- Depends on ongoing state? → **State-Driven** (While)
- Error or failure case? → **Unwanted Behavior** (If...then)
- None of the above — always true? → **Ubiquitous**

Most requirements in practice are event-driven or unwanted-behavior — they describe what happens when something occurs or goes wrong. Ubiquitous requirements are the minority, typically reserved for architectural invariants and naming conventions. If you find yourself writing mostly ubiquitous requirements, reconsider whether each one really has no trigger, condition, or failure mode.

### Before You Start: Is This a Small Task?

Count the distinct behavioral changes the task requires. If **1-3 changes** (file renames, config tweaks, single-function additions, adding a flag), skip everything below and jump to [Small Task Format](#small-task-format). The full REQ/S/V structure adds overhead that hurts more than it helps on small tasks.

| Expected Changes | Action |
|-----------------|--------|
| 1-3 | Use **Small Task Format** — Changes table + Verification list |
| 3-7 | Continue with full EARS requirements below |
| 7+ | Split into separate deliverables first |

## EARS Requirement Patterns

EARS (Easy Approach to Requirements Syntax) provides four patterns for writing unambiguous requirements. Each requirement uses exactly one pattern.

### Event-Driven

Requirements triggered by a specific event.

```
REQ-<N>: When [trigger], the [system] SHALL [action].
```

Use for reactive behavior: "When a new worktree is created, the session-start hook SHALL detect the fresh environment and run background init."

### State-Driven

Requirements that apply while a condition holds.

```
REQ-<N>: While [state], the [system] SHALL [action].
```

Use for conditional behavior: "While the CI run is in progress, the landing workflow SHALL poll for completion."

### Unwanted Behavior

Requirements that handle failure modes and edge cases.

```
REQ-<N>: If [condition], then the [system] SHALL [mitigation].
```

Use for error handling: "If the git push fails, then the landing workflow SHALL offer retry or abort."

### Ubiquitous

Requirements that always hold, with no triggering event or state.

```
REQ-<N>: The [system] SHALL [action].
```

Use for invariant properties: "The CLI SHALL validate all inputs before execution."

## Requirement Structure

Every top-level requirement must include three parts: the EARS statement, a **Rationale** explaining *why* it exists, and **Acceptance Criteria** defining specific, observable conditions for verification.

### Format

```markdown
### REQ-<N>: <Short title>

<EARS pattern statement using SHALL/SHOULD/MAY>

**Rationale:** <Why this requirement exists — the problem it solves or constraint it enforces>

**Acceptance Criteria:**
- <Observable condition 1>
- <Observable condition 2>
```

Requirements must cover functional behavior — not just structural skeleton — so that an implementer never has to guess what the system actually does.

### Sub-Requirements

Top-level requirements decompose into 1-5 sub-requirements that flesh out the details:

```markdown
### REQ-1: Worktree Environment Detection

When a new worktree is created, the session-start hook SHALL detect the missing CLI binary and run `go build` in the background.

**Rationale:** Worktrees share the Git repo but not the built binary. Without auto-detection, users must manually build the CLI before running any commands in a fresh worktree.

**Acceptance Criteria:**
- Hook checks for CLI binary at repo root; if missing, triggers background build
- Build output is suppressed unless it fails
- User can run commands immediately; build completes within 10 seconds

| ID | Sub-Requirement | Priority |
|----|----------------|----------|
| REQ-1.1 | When the worktree has no CLI binary, the hook SHALL invoke `go build` targeting the repo root. | SHALL |
| REQ-1.2 | While the build is running, the hook SHALL suppress stdout and only surface stderr on failure. | SHALL |
| REQ-1.3 | If the build fails, then the hook SHALL print the error and exit with a non-zero code. | SHOULD |
```

### Sizing

Aim for **3-7 top-level requirements**, each with **1-5 sub-requirements**. This keeps the plan scannable while providing enough detail that an implementer doesn't have to guess.

- **Fewer than 3 top-level requirements** suggests the task may be too small for structured requirements. Consider a simple checklist instead.
- **More than 7 top-level requirements** suggests the task should be split into phases (see Phased Steps section below).

### Completeness

Cover these dimensions — missing any is a plan defect:

1. **Core functionality** — what the system must do (ubiquitous or event-driven)
2. **Error handling** — what happens when things go wrong (unwanted behavior). Every plan needs at least one unwanted-behavior requirement.
3. **Integration** — how it connects to existing components (event-driven or state-driven)
4. **Prerequisites** — external dependencies and preconditions (see Prerequisites section below)

### Granularity

Each top-level requirement should be independently verifiable. If you can't write a distinct V-check for it, it's either too vague or a subset of another requirement — merge or sharpen it. Sub-requirements decompose a top-level requirement into implementable pieces.

## Prerequisites

Every requirements document must list external dependencies and preconditions before the implementation plan. These are things that must be true or available before work begins.

### Format

```markdown
## Prerequisites

| Dependency | Type | Status |
|-----------|------|--------|
| CSI volume `prometheus-data` created | Infrastructure | Verify with `nomad volume status` |
| Docker registry accessible from cluster | Network | Verify with `docker pull` from any node |
| Python 3.13+ available via `uv` | Toolchain | Verify with `uv run python --version` |
```

Types: Infrastructure, Toolchain, Network, Configuration, Data, Permissions.

## ID Convention

Requirements documents use three ID prefixes for end-to-end traceability:

| Prefix | Section | Meaning |
|--------|---------|---------|
| REQ | Requirements | What the implementation must achieve |
| S | Plan of Attack | How each requirement gets implemented |
| V | Verification | How each requirement gets verified |

Top-level IDs are sequential: REQ-1, REQ-2...; S1, S2...; V1, V2...
Sub-requirement IDs use dot notation: REQ-1.1, REQ-1.2, REQ-2.1...

## Traceability

Every requirement must be both implemented and verified:

- **Forward trace:** Every REQ must appear in at least one S (implemented) and at least one V (verified).
- **Backward trace:** Every S must reference at least one REQ. Every V must reference at least one REQ.
- **Tag syntax:** `S3 (REQ-2, REQ-4): Step description` — parenthesized REQ-IDs after the S/V-ID.

If a requirement has no step, it won't be implemented. If it has no verification check, it can't be confirmed done. Both are plan defects.

### Traceability Matrix

When reviewing a draft, construct this matrix:

```
          S1  S2  S3  S4  V1  V2  V3
  REQ-1    x           x   x
  REQ-2        x   x           x
  REQ-3    x       x               x
```

Every REQ row must have at least one mark in an S column and at least one in a V column.

## Phased Steps

Group implementation steps into phases that each produce a shippable, testable increment. This reduces risk of large unshippable branches and enables incremental delivery.

### Format

```markdown
## Plan of Attack

### Phase 1: <Name> — Foundation
S1 (REQ-1, REQ-2): <step description>
S2 (REQ-1): <step description>
**Checkpoint:** <what's verifiable after this phase>
If checkpoint fails: <where to investigate before proceeding>

### Phase 2: <Name> — Core Logic
S3 (REQ-3, REQ-4): <step description>
S4 (REQ-4, REQ-5): <step description>
**Checkpoint:** <what's verifiable after this phase>
If checkpoint fails: <where to investigate before proceeding>
```

### Scope-Size Check

Before finalizing the plan, assess the total scope:

- **Small** (1-3 REQs, single phase): Use the **Small Task Format** below instead of the full requirements structure.
- **Medium** (3-7 REQs, 1-2 phases): Standard treatment. Each phase should be committable independently.
- **Large** (7+ REQs, 3+ phases): Split into separate deliverables. Each deliverable gets its own requirements document. A single branch should not accumulate more than 2-3 phases of uncommitted work.

If a plan exceeds 7 top-level requirements, explicitly recommend splitting the work: "This task spans N requirements across M phases. Consider splitting into separate branches: Phase 1-2 as one PR, Phase 3-4 as a follow-up."

### Small Task Format

For tasks with 1-3 requirements — file renames, config tweaks, single-function additions — skip the full REQ/S/V structure and use this lightweight format instead:

```markdown
## Task: <One-sentence summary of what changes and why>

### Changes
| File | Change |
|------|--------|
| `path/to/file.ext` | <What changes in this file> |
| `path/to/other.ext` | <What changes in this file> |

### Verification
1. `<command to run>` — expected: <result>
2. `<command to run>` — expected: <result>
3. `<manual check>` — expected: <result>
```

No sub-requirements, no traceability matrix, no phased steps. The verification list replaces both V-checks and acceptance criteria — each item must be a concrete, copy-pasteable command or an observable check.

### Step Guidelines

- Steps are ordered — dependencies flow downward
- Each step should be completable independently (no half-states)
- Group related changes into a single step when they must be atomic
- Note explicit dependencies: "S3 (REQ-2, REQ-4): ... (after S1)"

## Writing Verification Checks

Verification checks assert observable behavior. They must cover both happy paths and failure/negative cases.

### Format

```
V<N> (REQ-<ids>): When [trigger/command], the [system] SHALL [observable output].
```

### Observable Outputs

V-checks describe **what to verify**, not how. The implementer chooses the verification method (run a command, read a file, inspect output). Your job is to make the expected outcome specific enough that there's no ambiguity about pass/fail.

Good verification checks reference things you can directly observe:

- Exit codes: "SHALL exit with code 0"
- Command output: "SHALL print 'All validations passed'"
- File contents: "SHALL write a YAML frontmatter block containing `branch:`"
- HTTP responses: "SHALL return 200 with JSON body containing `status: healthy`"
- Log entries: "SHALL log 'deployment complete' to stdout"
- UI state: "SHALL display the dashboard with no error panels"

**Rules for specificity:**

1. **State the expected value** — not a comparison. Write "SHALL print `v1.2.3`" not "SHALL print the correct version." Write "SHALL contain exactly 3 entries" not "SHALL contain the expected number of entries."
2. **Avoid relative terms** — "identical to baseline", "similar output", "matches existing behavior", and "consistent with" are ambiguous. The implementer doesn't have the baseline in front of them. State what the output actually is.
3. **One observable per V-check** — if a check verifies two unrelated things, split it. "SHALL exit 0 AND write a log file" is two checks.
4. **Each V-check is self-contained** — an implementer should be able to verify it without reading other V-checks or external documents for context.

### Negative and Failure Cases

Every verification plan must include checks for failure modes — not just happy paths. For each unwanted-behavior requirement (If...then), write a corresponding V-check that deliberately triggers the failure and verifies the mitigation works.

Negative checks must verify behavior that **your implementation specifically defines** — not platform behavior that exists regardless of what you built. The litmus test: "If I introduced a bug in my code, would this check catch it?" If the platform would enforce the same outcome with or without your code, the check isn't testing your work.

**Good negative checks** — verify something specific to your implementation:
```
V5 (REQ-4): When the Prometheus container is killed, `consul health checks
            prometheus` SHALL report the check as `critical` within 60 seconds.
            (Tests the health check interval YOU configured at 30s.)
V6 (REQ-1): When a PR is opened targeting `feat/experiment` instead of `main`,
            the CI pipeline SHALL NOT trigger.
            (Tests the trigger scoping YOU defined in the workflow.)
V7 (REQ-3): When a deliberately failing Go test is included, the `go-validate`
            job SHALL fail with non-zero exit code and the log SHALL contain
            the test function name and failure message.
            (Tests the error reporting behavior YOU designed into the pipeline.)
```

**Bad negative checks** — test the platform, not your work:
```
AVOID: "When deployed without the CSI volume, Nomad SHALL fail placement."
       (Nomad always rejects missing volumes — your code didn't create that behavior.)
AVOID: "When the kernel constraint is removed, macOS scheduling fails."
       (The cluster's driver config enforces this — nothing to do with your job spec.)
AVOID: "When an invalid job spec is submitted, validation fails."
       (Nomad validates all job specs — this would pass even with an empty file.)
```

Aim for at least **one negative V-check for every unwanted-behavior requirement** and one for every critical happy-path requirement. Focus on edge cases where your specific choices (configuration values, trigger filters, error messages, timeout intervals) determine the outcome.

### Anti-Patterns

| AVOID | USE INSTEAD |
|-------|-------------|
| "Be fast" | `V1: When processing <100 files, SHALL complete within 5s` |
| "Handle errors gracefully" | `V2: When git push fails, SHALL display error and offer retry` |
| "The function shall call validate()" | `V3: When input exceeds 100 items, SHALL print "batch limit exceeded" and exit 1` |
| "Code should be clean" | `V4: When ./cluster validate --cli is run, SHALL exit with 0 (tests pass)` |
| "Work correctly" | `V5: When deployed to canary node, SHALL respond on port 8080 with 200` |
| Only happy-path checks | Include negative cases: what happens when input is invalid, service is down, precondition unmet |
| Passive voice without trigger | Active voice with explicit "When [trigger]" |
| Implementation details (calls X, stores Y) | Observable outcomes (outputs X, displays Y) |

## Reference

For detailed EARS pattern examples with domain-specific illustrations, see [references/ears-patterns.md](references/ears-patterns.md).
