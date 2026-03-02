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

### Step 2.5: Scope-Size Assessment

Before drafting, assess the task size from the research results:

| Expected REQs | Size | Drafting Mode |
|---------------|------|---------------|
| 1-3 | Small | Use the **Small Task Format** from the requirements-authoring skill. Skip full REQ/S/V structure, phased steps, and traceability matrix. |
| 3-7 | Standard | Full EARS requirements with phases and V-checks. |
| 7+ | Large | Ask the user to split into separate deliverables before drafting. |

To assess: count the distinct behavioral changes, new components, or integration points identified during research. Each maps roughly to one top-level requirement. Err toward "small" — if in doubt between small and standard, choose small.

If **small**: Step 4 uses the lightweight format (Changes table + Verification list). Steps 5 (Review) and 6 (Write) still apply but review scope is reduced.

If **large**: Present the scope breakdown to the user via AskUserQuestion (header "Scope Too Large") with options: "Split now" (recommend how to divide, then re-run for the first deliverable), "Proceed anyway" (continue with standard treatment), "Cancel" (stop). Do **not** proceed to Step 3 until the user decides.

### Step 3: Clarify

If genuine ambiguities remain, ask **one round** of questions (max 4 questions) via AskUserQuestion — confirm objective, fill gaps, clarify scope boundaries. **Skip** if already unambiguous.

### Step 4: Draft

Load the `launchpad:requirements-authoring` skill using the Skill tool for EARS patterns, requirement structure, and traceability guidance.

Assemble (fresh mode) or update (iterating mode) the flight plan. Do **not** write to disk yet. When mode is iterating, update only affected sections.

**If scope-size is "small":** Use the Small Task Format from the requirements-authoring skill instead of the full template below. Skip the Requirements, Traceability, and Phased Steps sections — use the Changes table and Verification list directly.

**If scope-size is "standard"** (or "large" if user chose "Proceed anyway")**:** Follow the requirements-authoring skill for all requirement, step, and verification formatting. The template below defines the document structure; the skill defines content quality standards.

**Template:**

    ---
    mission: <task from mission brief, verbatim>
    branch: <branch>
    date: <today>
    ---

    # Flight Plan

    > **For the implementer:** This flight plan is designed for autonomous execution.
    > Requirements define what must be true — not how to build it. V-checks are
    > guardrails, not scripts. Work loop: implement a phase → verify against its
    > checkpoint and V-checks → fix failures → proceed to next phase. If a V-check
    > fails, investigate root cause before moving on.

    ## Objective

    <detailed technical restatement — what's broken/missing, what "done" looks like>

    ## Prerequisites

    List external dependencies and preconditions per the requirements-authoring skill's Prerequisites format (dependency, type, status/verification).

    ## Requirements

    Expand the mission brief's Desired Outcome into 3-7 top-level requirements, each with 1-5 sub-requirements, using EARS patterns and RFC 2119 priority language (SHALL/SHOULD/MAY) from the loaded requirements-authoring skill. Every requirement must include a Rationale and Acceptance Criteria. At least one requirement must use the unwanted-behavior pattern (If...then) for error handling.

    ## Starting Points

    <3-7 verified file paths in `path:line` format with one-line notes — every path must exist>

    ## Scope & Decisions

    <what's in, what's out, key architectural choices>

    ## Guardrails

    <patterns to follow, anti-patterns to avoid, constraints from CLAUDE.md and .claude/rules/>

    ## Plan of Attack

    Group steps into phases per the requirements-authoring skill's Phased Steps format. Each phase produces a shippable, testable increment with a Checkpoint. Steps use S-prefix IDs with REQ traceability tags.

    Each checkpoint must include a failure recovery hint:
    ```
    **Checkpoint:** <what's verifiable after this phase>
    If checkpoint fails: <what to investigate or fix before proceeding>
    ```
    The recovery hint tells the implementer where to look — not what to do. Example: "If checkpoint fails: check Consul service registration logs and verify the health check endpoint returns 200."

    Apply the scope-size check: if the plan exceeds 7 top-level requirements, recommend splitting into separate deliverables.

    **Traceability:** Every REQ must appear in at least one S. Every S must reference at least one REQ.

    ## Verification

    Follow the requirements-authoring skill's verification format. Each check uses event-driven EARS phrasing and asserts observable behavior. Include both happy-path and negative/failure test cases. At least one negative V-check for every unwanted-behavior requirement.

    **Traceability:** Every REQ must appear in at least one V. Every V must reference at least one REQ.

### Step 5: Review

Define the peer-review pipeline parameters, then execute.

**Agent count and focus areas:** 4 parallel Sonnet agents (reduce to 2 — #1 and #3 — for small-scope plans).

| Agent | Focus | Fresh Mode | Iterating Mode |
|-------|-------|:-----:|:---------:|
| #1 — Completeness | **Standard/large:** All affected files identified? Starting points verified? Guardrails sufficient? Are all requirements (REQ) traced to at least one step (S) and one verification check (V)? Do requirements include rationale and acceptance criteria? **Small:** All affected files listed in the Changes table? Every verification item concrete and copy-pasteable? | yes | yes |
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
- **Blocking concerns** → present each to user with agent source + score → ask to revise or accept as-is. Always offer "Accept as-is."
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
      Requirements:    <N> top-level (REQ-1 to REQ-N) with sub-requirements
      Starting points: <N> verified files
      Plan phases:     <N> phases, <M> steps (S1-SM)
      Verification:    <N> checks (V1-VN) including <M> negative cases
      The flight plan is at .claude/flight-plan.md
      Start implementing — or review the plan first.

**Small:**

    Flight plan ready!
      Task:            <1-line summary>
      Files affected:  <N> files
      Verification:    <N> checks
      The flight plan is at .claude/flight-plan.md
      Start implementing — or review the plan first.

**STOP.** Do not begin implementation.

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
