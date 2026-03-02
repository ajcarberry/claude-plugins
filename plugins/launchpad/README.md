# Launchpad Plugin

Session lifecycle management — `/stage` creates workspaces, `/flight-plan` researches and plans, `/land` closes out with PR.

## Lifecycle

```
/stage  →  /flight-plan (optional)  →  [work]  →  /land
```

1. **`/stage`** — Fast workspace setup (~15 seconds). Creates a worktree + branch and writes a minimal mission brief with YAML frontmatter.
2. **`/flight-plan`** — Research and planning. Reads the mission brief, explores the codebase, clarifies scope, and produces a verified flight plan using EARS methodology with R/S/V traceability.
3. **Work** — Implement using the mission brief and flight plan as context.
4. **`/land`** — Close out. Commits, checks docs, pushes, checks CI status, and creates a PR with verification traceability.

## Commands

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
5. Multi-agent architecture review with confidence scoring (includes traceability check)
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

## Knowledge Skills

Commands delegate domain knowledge to background skills that provide templates, rubrics, and guidance.

| Skill | Purpose | Used by |
|-------|---------|---------|
| `peer-review` | Scoring rubric and review pipeline for multi-agent review | `/flight-plan` |
| `requirements-authoring` | EARS patterns, RFC 2119 priorities, sub-requirement hierarchies, R/S/V traceability, phased steps, and verification guidelines | `/flight-plan` |
| `write-tests` | Testing Trophy model, behavior-first test patterns, and mocking guidelines | User-invocable (`/write-tests`) |

`peer-review` and `requirements-authoring` are command-internal — loaded automatically by `/flight-plan`. `write-tests` is user-invocable.

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

When Claude starts in a worktree that contains `.claude/mission-brief.md`, the SessionStart hook:

1. **Loads context** — reads the mission brief and flight plan (if present) into session context
2. **Detects mismatches** — branch drift (via YAML frontmatter `branch:` field), stale brief, dirty working tree
3. **Background env init** — if the worktree is fresh (missing CLI binary or .venv), runs `go build` and `uv sync` in the background

## Prerequisites

- **git** — worktree and branch operations
- **Go 1.23+** — CLI build in fresh worktrees (background)
- **uv** — Python dependency sync (background)
- **VS Code** — opened automatically by `/stage` (falls back to `code` CLI, then manual)
- **gh** (GitHub CLI) — PR creation and CI status checking in `/land`

## Extending

See the plugin source code for how to add commands, skills, hooks, and reference files.
