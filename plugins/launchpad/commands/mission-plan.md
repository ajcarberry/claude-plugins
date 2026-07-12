---
description: Turn the staged idea into a spec and work packets — the optional planning phase for complex work
allowed-tools: Bash, Read, Write, Glob, Grep, Skill, Task, AskUserQuestion
argument-hint: "[extra context]"
---

# Mission Plan — Spec First, Then Packets

Optional phase between `/stage` and `/launch`, for work too complex to implement
straight from the brief. Output: `.claude/mission/spec.md` — one artifact, no
separate plan document.

## Workflow

### Step 1: Preflight

Read `.claude/mission/brief.md`. If it doesn't exist:
> No mission staged. Run `/stage` first — it creates the worktree and brief this
> plan builds on.
**STOP.**

If `.claude/mission/spec.md` already exists, ask: revise it or start over.

### Step 2: Author the Spec

**Load the spec skill:** invoke `Skill: tpm:spec-authoring`. It owns the template
(including the project-override lookup) and the authoring discipline.

**Fallback** (tpm plugin not installed): use this minimal structure —
`## Problem`, `## Desired Outcome` (from the brief), `## Requirements` (numbered,
testable), `## Out of Scope`, `## Open Questions`, `## Done When` (observable
checks).

**Ground it:** explore the relevant code before writing — the spec must name real
files, real constraints, real integration points, not guesses. Where the skill
calls for user input (goals, tradeoffs, open questions), ask with AskUserQuestion —
batched, not one-at-a-time. `$ARGUMENTS` is extra context from the user; fold it in.

### Step 3: Re-check Stakes

The spec usually reveals more than the one-line idea did. Re-classify per the
[stakes reference](../references/stakes.md); if the tier changed, update `stakes:`
in the brief and say so.

### Step 4: Decompose into Work Packets

If the work merits orchestration (~5+ separable pieces — see
[orchestration.md](../references/orchestration.md), "When NOT to orchestrate"),
append a `## Work Packets` section to the spec: one packet per piece in the
reference's format (goal, files in scope, contracts, spec slice, done-check, tier),
ordered so contracts exist before their consumers.

Smaller work: skip packets entirely and note "express launch" in the spec.

### Step 5: Confirm + STOP

Write `.claude/mission/spec.md`. Present a compact summary — the requirements, the
done-checks, the packet count (or "express"), the stakes tier — and ask:
- "Approved" — spec is final
- "Revise" — take the feedback, loop to Step 2
- "Cancel" — keep the draft on disk, note it's unapproved

On approval:

```
Spec approved: .claude/mission/spec.md
  Requirements: <N>   Packets: <N | express>   Stakes: <tier>

  Run /launch to implement.
```

**STOP.** Implementation is `/launch`'s job.

## Error Handling

| Scenario | Action |
|----------|--------|
| No mission brief | Point to `/stage`, stop |
| tpm plugin missing | Use the inline fallback structure, note it once |
| User cancels | Leave draft spec on disk, marked unapproved |
