# Launchpad Plugin

Session lifecycle and flight rules — from idea to verified landing, with discipline
skills enforcing verification, failing-check-first, and root-cause debugging along
the way.

## Lifecycle

```
IDEA → /mission → /stage → /flight-plan → [implement] → /land → …
            │                             (/commit at checkpoints)
            └─ small task? → /hop                 /status = re-entry, any time
```

1. **`/mission`** — Shape an idea into an approved spec (hard gate before implementation). Skippable for small/obvious work.
2. **`/stage`** — Fast workspace setup (~15 seconds): worktree + branch + mission brief (linking the spec if one exists) + background baseline check.
3. **`/flight-plan`** — Research and planning: verified flight plan with phases, checkpoints, and V-checks.
4. **Implement** — using the mission brief and flight plan as context; `/commit` reviews and commits at checkpoints.
5. **`/land`** — Close out: commits, docs check, push, CI status, PR.
6. **`/hop`** — Express lane: mini-brief → failing check → implement → light review → commit → optional PR, in one command.
7. **`/status`** — Read-only mission re-entry: where things stand, what's next, what's blocked.

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

### `/land` — Close Out a Session

Commits outstanding work, checks documentation for drift, pushes the branch, checks CI status, and creates a pull request.

```bash
/land                                # Derives PR title from context
/land feat: add alerting rules       # Uses argument as PR title
```

**CI Status Check:** After pushing, `/land` checks CI status via `gh run list`. If CI is running, offers to wait. If CI failed, offers to proceed or abort. If `gh` is unavailable, skips with a note.

**Verification Traceability:** If a flight plan exists with a Verification section, the PR test plan cross-references each V-check with pass/fail status.

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
