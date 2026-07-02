---
description: Shape an idea into an approved spec — clarify, compare approaches, gate implementation until sign-off
argument-hint: "[idea description]"
allowed-tools: Bash, Read, Grep, Glob, Write, Task, Skill, AskUserQuestion, WebSearch, WebFetch
---

# Mission — Idea to Approved Spec

Turn a fuzzy idea into an approved design spec. This is the front door for work that
needs shaping. For small or obvious tasks, skip this — use `/hop` or go straight to
`/stage`.

## The Hard Gate

**Do NOT write code, scaffold files, create branches, or invoke any implementation
workflow until the user has approved the spec.** Clarifying and designing is the only
work permitted inside `/mission`.

## Workflow

### Step 1: Understand the Idea

Take the idea from `$ARGUMENTS`, or ask: "What are we exploring?"

Explore just enough context to ask intelligent questions: relevant files, existing
patterns, prior art in the codebase (use Explore agents only if the area is genuinely
unfamiliar). Do not deep-dive — that's `/flight-plan`'s job.

### Step 2: Clarify

Determine the stakes tier (load `launchpad:stakes-rubric` if unsure).

Ask clarifying questions via AskUserQuestion — batched into 1 round of up to 4
questions for standard work, up to 2 rounds for high-stakes or genuinely open-ended
ideas. Prefer multiple-choice over open-ended. Cover: purpose (what problem, for
whom), constraints (must-haves, must-nots), and success (how we'll know it worked).

Skip questions whose answers are already clear from the idea or the codebase.

### Step 3: Propose Approaches

Present **2-3 genuinely different approaches** with trade-offs and a clear
recommendation. Format each as: name, one-paragraph description, pros/cons, rough
effort. Ask the user to pick via AskUserQuestion (recommended option first).

If only one sensible approach exists, say so and why — don't invent strawmen.

### Step 4: Draft the Spec

Write the spec draft. Scale depth to stakes: standard work gets a 1-2 page spec;
high-stakes or large designs get fuller treatment and section-by-section confirmation.

**Template:**

    ---
    topic: <short-kebab-slug>
    date: <today>
    status: draft
    ---

    # Spec: <Title>

    ## Problem
    <What's broken/missing, for whom, why now — 2-5 sentences>

    ## Approach
    <The chosen approach and why it won over the alternatives>

    **Alternatives considered:** <one line each, with the reason rejected>

    ## Design
    <The shape of the solution — components, flows, key decisions.
     Scale to complexity; bullet points over prose where possible.>

    ## Out of Scope
    <Explicit non-goals — the anti-scope-creep list>

    ## Success Criteria
    <Observable conditions that define "worked" — these seed /flight-plan's V-checks>

### Step 5: Approval Gate

Show the full spec, then ask via AskUserQuestion (header "Spec"):
- "Approve" — lock the spec
- "Revise" — user describes changes; update and re-present (no cycle limit — this is
  the cheap phase to iterate in)
- "Abandon" — stop; write nothing

Only on **Approve**: set `status: approved` and write to
`.claude/specs/<date>-<topic>.md` (create the directory if needed).

### Step 6: Handoff

    Mission defined!
      Spec:    .claude/specs/<date>-<topic>.md
      Next:    /stage to create the workspace (the mission brief will link this spec)
               Small task after all? /hop works too.

**STOP.** The gate holds until the user moves forward themselves.

## Error Handling

| Scenario | Action |
|----------|--------|
| Idea already fully specified | Say so; offer to skip straight to /stage |
| User abandons | Stop gracefully, write nothing |
| Not a git repo | Fine — specs can be written anywhere; warn that /stage will need a repo |
| Spec dir missing | `mkdir -p .claude/specs` |
