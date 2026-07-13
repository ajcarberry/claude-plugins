---
description: Create or update the roadmap — proactive horizon planning from themes and strategy, or reactively slot a new spec, finding, or request
argument-hint: "[what's new — spec path, dig finding, request] | blank for proactive planning"
allowed-tools: Bash, Read, Write, Glob, Grep, Task, Skill, AskUserQuestion
---

# Roadmap — Plan the Direction

Load `Skill: tpm:roadmap-planning` first — it owns both modes and the hygiene rules.

## Workflow

### Step 1: Gather

- Find the roadmap (default `docs/roadmap.md`; project-declared location
  supersedes). None → this is proactive mode creating one from the
  [template](../templates/roadmap.md).
- Load the latest `docs/feedback/*-themes.md` if present.
- Mode: `$ARGUMENTS` names something new (spec, dig finding, request) →
  **reactive**; blank → **proactive**.

### Step 2a: Proactive

Per the skill: brainstorm candidates wide (themes + strategy gaps + maintenance
debt), then prioritize with a stated frame. Where strategy or capacity is the
user's call — and it usually is — ask with AskUserQuestion, batched. Produce the
stakeholder question list alongside the roadmap.

### Step 2b: Reactive

Read the new input. Propose its slot (or a decline with reasoning). **Every
insertion shows its displacement** — what moves down, stated before the user
approves. New evidence that re-ranks old items: say which and why.

### Step 3: Confirm and Write

Show the proposed roadmap diff (or full draft) including displacement log entries.
AskUserQuestion: apply / revise / cancel. On apply, write the roadmap and remind:

```
Roadmap updated → docs/roadmap.md
  Now: <n> · Next: <n> · Later: <n> · Declined this round: <n>
  Displacements: <what moved, or none>

  Communicate it: /comms community | /comms exec
  Top item ready to spec: /spec <item>
```

The roadmap is a project artifact — commit it via the project's normal flow; this
command doesn't commit.

## Error Handling

| Scenario | Action |
|----------|--------|
| No themes doc | Proceed on strategy + user input; note the evidence gap |
| Reactive input not found | Ask for the path/reference, stop |
| User cancels | Leave the existing roadmap untouched |
