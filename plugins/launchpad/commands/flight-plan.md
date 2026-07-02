---
description: Research the codebase and produce a detailed implementation plan from a mission brief
allowed-tools: Bash, Read, Write, Edit, Grep, Glob, Task, Skill, AskUserQuestion, WebSearch, WebFetch
---

# Flight Plan — Research, Scope & Plan

Read the mission brief, research the codebase, clarify scope, and produce a verified implementation plan. Works in two modes — **fresh** (no existing flight plan) or **iterating** (refining an existing one). The flow is identical; research depth and review breadth scale down when iterating.

## Preconditions

### 1. Mission Brief Must Exist

Glob for `.claude/mission-brief.md`. 

If missing:
> No mission brief found. Run `/stage` first to create a workspace and mission brief.
**STOP.**

### 2. Check for Existing Flight Plan

Glob for `.claude/flight-plan.md`. If found, ask via AskUserQuestion (header "Flight Plan"):
- "Iterate" — refine the existing plan
- "Overwrite" — start fresh
- "Cancel" — keep current plan, stop

If Cancel → **STOP**. If Overwrite → mode is **fresh**. If Iterate → mode is **iterating**.

If no existing flight plan → mode is **fresh**.

## Workflow

### Step 1: Load Context

Read `.claude/mission-brief.md`. Extract from YAML frontmatter: task, branch, date. Extract from body: Desired Outcome.

**If mode is iterating:** also read `.claude/flight-plan.md`, then ask the user (1 question, header "Target Refinement"):
- "Narrow scope" — reduce what's in scope
- "Expand scope" — add more to the plan
- "Revise approach" — change implementation strategy

### Step 2: Research

Launch Explore agents (via Task tool, `subagent_type: "Explore"`) to scan relevant codebase areas.

| Mode | Agents | Scope |
|------|--------|-------|
| Fresh | 2-4 | Broad scan across affected areas; read CLAUDE.md and relevant .claude/rules/ |
| Iterating | 1-2 | Focused on the area being changed |

From the results, draft:
- A candidate **Objective** (technical restatement of the task)
- Candidate **Starting Points** (verified `path:line` references)
- Open questions needing clarification

### Step 2.5: Size & Stakes Assessment

Before drafting, assess size and stakes (load `launchpad:stakes-rubric` if unsure):

| Distinct changes | Size | Drafting Mode |
|------------------|------|---------------|
| 1-3 | Small | **Small Task Format** — Changes table + Verification list. (This size usually means `/hop` was the better entry; say so, but proceed.) |
| 3-7 | Standard | **Plain plan** (default template below). |
| 7+ | Large | Ask the user to split into separate deliverables before drafting. |

**EARS opt-in:** if the stakes tier is **high** (auth, payments, migrations, prod
infra, destructive ops) or the user explicitly asks for formal requirements, add an
EARS Requirements section — load `launchpad:requirements-authoring` for patterns and
traceability. Otherwise skip formal requirements entirely; the plain plan's
objective + V-checks carry the contract.

To assess size: count the distinct behavioral changes, new components, or integration points identified during research. Err toward "small" — if in doubt between small and standard, choose small.

If **large**: Present the scope breakdown to the user via AskUserQuestion (header "Scope Too Large") with options: "Split now" (recommend how to divide, then re-run for the first deliverable), "Proceed anyway" (continue with standard treatment), "Cancel" (stop). Do **not** proceed to Step 3 until the user decides.

### Step 3: Clarify

If genuine ambiguities remain, ask **one round** of questions (max 4 questions) via AskUserQuestion — confirm objective, fill gaps, clarify scope boundaries. **Skip** if already unambiguous.

### Step 4: Draft

Assemble (fresh mode) or update (iterating mode) the flight plan. Do **not** write to disk yet. When mode is iterating, update only affected sections.

**If size is "small":** use the Small Task Format — a Changes table (file → what changes) and a numbered Verification list of copy-pasteable commands with expected results. Nothing else.

**If EARS opt-in triggered** (high stakes or explicit request): load `launchpad:requirements-authoring` and insert a `## Requirements` section (EARS patterns, rationale, acceptance criteria, R/S/V traceability tags) between Objective and Starting Points. Otherwise omit it.

**Default template (plain plan):**

    ---
    mission: <task from mission brief, verbatim>
    branch: <branch>
    date: <today>
    stakes: <low | standard | high>
    ---

    # Flight Plan

    > **For the implementer:** Designed for autonomous execution by someone with no
    > session context. Work loop: implement a phase → verify its checkpoint and
    > V-checks → fix failures at root cause → next phase.

    ## Objective

    <What's broken/missing, what "done" looks like — plain language, specific.
     Pull success criteria from the linked spec if one exists.>

    ## Prerequisites

    <External dependencies and preconditions, each with a verification command.
     Omit the section if there are none.>

    ## Starting Points

    <3-7 verified file paths in `path:line` format with one-line notes — every path must exist>

    ## Scope & Decisions

    <what's in, what's out, key choices — the out-list prevents scope creep>

    ## Guardrails

    <patterns to follow, anti-patterns to avoid, constraints from CLAUDE.md and .claude/rules/>

    ## Plan of Attack

    Phases, each producing a shippable, testable increment. Steps use S-prefix IDs.
    **Steps must be executable by a fresh-context implementer:** exact file paths,
    real function signatures, concrete commands — never "similar to S3" or "add
    appropriate validation".

    ### Phase 1: <name>
    S1: <step>
    S2: <step>
    **Checkpoint:** <what's verifiable after this phase>
    If checkpoint fails: <where to investigate — not what to do>

    ## Verification

    Numbered V-checks asserting observable behavior — concrete command or observation
    plus the expected result. Each check is tagged by when it can run:

    - `V1 [orbit]` — verifiable from the branch (tests, builds, local runs). Run by
      /launch at checkpoints and /orbit before the PR.
    - `V2 [landing]` — requires the live/deployed system (kill the container and
      watch the alert; verify prod telemetry). Queued in the PR body for /land.

    Include negative/failure cases, not just happy paths — at least one per
    error-handling behavior the plan introduces.

### Step 5: Review

Define the peer-review pipeline parameters, then execute.

**Review depth** (per the peer-review skill's stakes rubric):
- **Small-scope plans** — one lightweight reviewer covering dimensions #1 and #3 only.
- **Standard** (default) — **one strong reviewer** covering the applicable dimensions below as sections of a single prompt.
- **High stakes** (plan touches auth, payments, migrations, prod infra, or destructive ops) — parallel specialist agents, one per applicable dimension.

| Dimension | Focus | Fresh Mode | Iterating Mode |
|-------|-------|:-----:|:---------:|
| #1 — Completeness | **Standard/large:** All affected files identified? Starting points verified? Guardrails sufficient? Every phase has a checkpoint; every V-check is concrete, tagged `[orbit]`/`[landing]`, and covers the objective? (If an EARS Requirements section exists: every REQ traced to at least one S and one V.) **Small:** All affected files listed in the Changes table? Every verification item concrete and copy-pasteable? | yes | yes |
| #2 — Feasibility | Steps execute in order? Dependencies accounted for? Hidden complexities? Effort proportional? | yes | — |
| #3 — Scope Alignment | Plan stays within mission brief? Over-engineering? Scope boundaries clear? | yes | yes |
| #4 — Convention Compliance | Follows CLAUDE.md and .claude/rules/? Respects architectural constraints? Would pass `/commit-review`? | yes | — |

**Artifact format:** Each agent receives the draft flight plan, mission brief, and relevant CLAUDE.md rules.

**Domain-specific false positives** (score LOW):
- Suggestions to add scope the mission brief didn't ask for
- Concerns about implementation details the plan intentionally defers
- Style preferences for plan formatting
- Concerns already covered by another agent's dimension

**Resolution logic:**
- **Blocking concerns** → present each to user with the reviewing dimension → ask to revise or accept as-is. Always offer "Accept as-is."
- **Only nits** → mention briefly, proceed to Step 6
- **Clean** (no concerns survive filtering) → proceed to Step 6
- If user requests revisions, update the draft and re-run the pipeline. **Max 2 revision cycles** — then proceed as-is.

Load the `launchpad:peer-review` skill using the Skill tool and execute the pipeline with the parameters above.

### Step 6: Write

Write the finalized plan to `.claude/flight-plan.md` (Write tool for fresh, Edit tool for iterating).

Print summary (use the variant matching the scope-size):

**Standard/large:**

    Flight plan ready!
      Objective:       <1-line summary>
      Stakes:          <low | standard | high — with EARS requirements if high>
      Starting points: <N> verified files
      Plan phases:     <N> phases, <M> steps (S1-SM)
      Verification:    <N> checks (<X> [orbit], <Y> [landing]) incl. <M> negative cases
      The flight plan is at .claude/flight-plan.md
      Run /launch to execute — or review the plan first.

**Small:**

    Flight plan ready!
      Task:            <1-line summary>
      Files affected:  <N> files
      Verification:    <N> checks
      The flight plan is at .claude/flight-plan.md
      Run /launch to execute — or review the plan first.

**STOP.** Do not begin implementation — that's `/launch`.

## Error Handling

| Scenario | Action |
|----------|--------|
| No mission brief | Print message, suggest `/stage`, stop |
| Flight plan exists | Ask: iterate, overwrite, or cancel |
| Write fails | Report error with path, suggest checking permissions |
| Agent dispatch fails | Log which agent failed, continue with remaining results |
| Explore agents return nothing | Widen search scope, try alternative terms |
| User skips clarification | Proceed with best-guess scope, note assumptions |
| Blocking review issues | Present to user, revise or accept |
| All review agents timeout | Skip review, write plan with a note that review was skipped |
