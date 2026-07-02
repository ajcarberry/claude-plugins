# Launchpad Plugin

Session lifecycle and flight rules — from idea to verified landing, with discipline
skills enforcing verification, failing-check-first, and root-cause debugging along
the way.

## Lifecycle

```
IDEA → /mission → /stage → /flight-plan → /launch → /orbit → /land → debrief*
            │                            (/commit at  (push, PR,  (merge,
            │                             checkpoints) CI, review  deploy,
            │                                          iteration)  validate)
            └─ small task? → /hop            /status = re-entry, any time
```
\* `/debrief` is deferred — see SUPERPOWERS-DESIGN.md.

1. **`/mission`** — Shape an idea into an approved spec (hard gate before implementation). Skippable for small/obvious work.
2. **`/stage`** — Fast workspace setup (~15 seconds): worktree + branch + mission brief (linking the spec if one exists) + background baseline check.
3. **`/flight-plan`** — Research and planning: plain-language plan with phases, checkpoints, and `[orbit]`/`[landing]`-tagged V-checks. EARS requirements opt-in for high stakes.
4. **`/launch`** — Execute the plan phase by phase with a durable flight log; `/commit` at checkpoints; subagent orchestration (heavyweight mode) for big builds.
5. **`/orbit`** — Push, PR, CI watch, review iteration, orbit V-checks — until go-for-landing.
6. **`/land`** — Reentry and touchdown: go-for-landing gate, rollback path + backup, merge, deploy, observe, landing V-checks against the live system, abort-to-orbit on failure, cleanup.
7. **`/hop`** — Express lane for small tasks; **`/status`** — read-only re-entry, any time.

## Commands

### `/mission` — Idea to Approved Spec

Clarifying questions (batched, multiple-choice preferred), 2-3 approaches with
trade-offs, and a spec written to `.claude/specs/` — with a hard gate: no
implementation until the spec is approved. Ceremony scales with stakes.

```bash
/mission                                    # Interactive
/mission migrate auth to passkeys           # Direct
```

### `/hop` — Express Lane

Small tasks (1-3 changes) in one command: inline mini-brief, observable checks that
fail first, light review, commit, optional PR. Refuses high-stakes work; escalates to
the full sequence if scope grows.

```bash
/hop fix the footer link color
```

### `/status` — Mission Re-Entry

Read-only report from the mission brief, spec, flight plan, flight log, git, and
GitHub state: current phase, what's done, what's next, what's blocked. Ends with one
suggested next action.

### `/stage` — Fast Workspace Setup

Creates a new git worktree with a dedicated branch and writes a minimal mission brief. No research, no env init, no multi-round Q&A.

```bash
/stage                              # Interactive — prompts for description
/stage add prometheus alerting      # Direct — uses provided description
```

**Workflow:**
1. Gather work description (from argument or prompt)
2. Infer branch type, generate name, validate, and confirm
3. Create worktree (defaults to current branch as base)
4. Write minimal mission brief to `.claude/mission-brief.md` (with YAML frontmatter)
5. Open VS Code, print summary, and stop

### `/flight-plan` — Research, Scope & Plan

Reads the mission brief, researches the codebase, clarifies scope, and produces a verified flight plan with EARS-structured requirements and multi-agent architecture review.

```bash
/flight-plan                        # Reads mission brief and begins research
```

**Workflow:**
1. Read mission brief (requires `/stage` first)
2. Parallel codebase research via Explore agents
3. Clarify scope with user (max 4 questions, skipped if unambiguous)
4. Draft flight plan with EARS requirements (R), implementation steps (S), and verification checks (V)
5. Risk-scaled peer review — single reviewer by default, specialist panel for high-stakes plans (includes traceability check)
6. Write finalized plan to `.claude/flight-plan.md`

**EARS Methodology:** Flight plans use structured requirement patterns (ubiquitous, event-driven, state-driven, unwanted behavior) with end-to-end traceability — every requirement (R) must appear in at least one implementation step (S) and one verification check (V).

### `/launch` — Execute the Flight Plan

Implements phase by phase with a durable `.claude/flight-log.md` (resumable after
crashes or compaction), running `[orbit]` V-checks at checkpoints and `/commit` per
phase, ending with a whole-branch review. Heavyweight mode (per-step subagents with
two-stage review) for ~10+ step builds; solo mode for environments without subagents.

```bash
/launch            # Lean (default) — offers heavyweight when the plan is large
/launch --heavy    # Per-step subagent orchestration
```

### `/orbit` — PR, CI & Review Iteration

Runs orbit V-checks, checks docs drift, pushes, creates the PR (with `[landing]`
checks published as `/land`'s work queue), watches CI, and iterates on review
feedback until **go-for-landing**. Re-enterable anytime.

```bash
/orbit                               # Derives PR title from context
/orbit feat: add alerting rules      # Uses argument as PR title
```

### `/land` — Reentry & Touchdown

Runs only on GO from `/orbit`: verifies CI/reviews fresh, states the rollback path,
backs up before anything destructive (typed confirmation for irreversible steps),
merges, deploys (domain-pack mechanics → project deploy command → CI/CD watch),
observes until stable, and executes the `[landing]` V-checks against the live system
— including negative checks. Failure = **abort-to-orbit**: rollback, verify healthy,
preserve the branch for another iteration. Touchdown = verified in reality.

## Skills

Two kinds: **pipeline skills** that commands load at fixed workflow points, and
**Flight Rules** — discipline skills that auto-invoke on their descriptions during
implementation work.

| Skill | Purpose | Used by |
|-------|---------|---------|
| `peer-review` | Risk-scaled review pipeline — single reviewer by default, specialist panel for high stakes, independent-reviewer concern filter | `/flight-plan`, `/commit` |
| `requirements-authoring` | EARS patterns, RFC 2119 priorities, R/S/V traceability, phased steps, verification guidelines | `/flight-plan` |
| `stakes-rubric` | Shared risk tiers (low/standard/high) that size review depth, gates, and plan format | all commands |
| `verification-before-completion` | Flight Rule: no completion claim without fresh verification evidence | auto-invokes |
| `test-driven-development` | Flight Rule: failing check first — a test where a harness exists, an observable command where it doesn't. Includes test-design and Go references (absorbs the former `write-tests`) | auto-invokes |
| `systematic-debugging` | Flight Rule: root cause before remedy; 3-strikes rule. Includes root-cause-tracing, condition-based-waiting, defense-in-depth references | auto-invokes |
| `browser-verified-web-work` | Flight Rule: web changes verified by loading the page — console checked, screenshot captured | auto-invokes |
| `subagent-driven-development` | Heavyweight execution engine: fresh implementer per step, two-stage step review, file-based handoffs, model tiering | `/launch --heavy` |
| `receiving-code-review` | Verify feedback before implementing; reasoned pushback; no performative agreement | `/orbit`, auto-invokes |
| `data-safety` | Migrations up+down tested against a copy; backup gate before destructive operations | auto-invokes |

## Two Documents

### Mission Brief (`.claude/mission-brief.md`)

Written by `/stage`. High-level outcome description only — what are we doing and why? No implementation details.

Uses YAML frontmatter for structured fields:

```yaml
---
task: Add Prometheus alerting rules
branch: feat/add-prometheus-alerting
date: 2026-02-27
parent: main
---
```

Body contains: Desired Outcome.

### Flight Plan (`.claude/flight-plan.md`)

Written by `/flight-plan`. Detailed implementation context — everything needed to build with full context.

Uses YAML frontmatter for structured fields:

```yaml
---
mission: Add Prometheus alerting rules
branch: feat/add-prometheus-alerting
date: 2026-02-27
---
```

Body contains: Objective, Prerequisites, Requirements (REQ-1 to REQ-N with sub-requirements, rationale, and acceptance criteria), Starting Points (verified paths), Scope & Decisions, Guardrails, Plan of Attack (phased steps S1-SN with REQ-tags), Verification (V1-VN with REQ-tags, EARS phrasing, including negative test cases).

## Hook: SessionStart

Fires on session start, after `/clear`, and after context compaction — so the
methodology survives context loss. It:

1. **Injects the flight-rules bootstrap** (always, even with no mission in progress) — a short policy block directing Claude to check for an applicable skill before implementation work
2. **Loads mission context** — mission brief, latest approved spec (`.claude/specs/`), flight plan, and flight log (`.claude/flight-log.md`) when present; a flight log triggers resume-from-last-entry behavior
3. **Detects mismatches** — branch drift (via YAML frontmatter `branch:` field), stale brief, dirty working tree
4. **Background env init** — if the project provides an executable `.claude/session-init.sh` (worktree builds, dependency syncs — whatever the project needs), runs it in the background

## Prerequisites

- **git** — worktree and branch operations
- **VS Code** — opened automatically by `/stage` (falls back to `code` CLI, then manual)
- **gh** (GitHub CLI) — PR creation and CI status checking
- Optional: an executable `.claude/session-init.sh` in your project for background environment init in fresh worktrees

## Extending

See the plugin source code for how to add commands, skills, hooks, and reference files.
