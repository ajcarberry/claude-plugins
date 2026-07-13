---
description: Turn an idea, feedback theme, or roadmap item into a spec — problem, proposal, implementation, gated in order
argument-hint: "[the idea, or a path to a theme/roadmap item]"
allowed-tools: Bash, Read, Write, Glob, Grep, Task, Skill, AskUserQuestion
---

# Spec — Idea to Approved Spec

Load `Skill: tpm:spec-authoring` first — it owns the template lookup, the section
gates, and the rules of substance. This command is the workflow around it.

## Workflow

### Step 1: Intake

The subject comes from `$ARGUMENTS` (an idea, or a path to a feedback theme /
roadmap item / dig finding — read it if it's a path). Nothing given → ask what
we're speccing.

Check `specs/` for an existing spec on this subject — if one exists, ask: revise
it (picking up at its current `status` gate) or start fresh.

### Step 2: Ground

Explore the relevant code, docs, and artifacts (themes doc, roadmap) so the
Problem section names real constraints and cites real evidence. Then interview
the user — batched via AskUserQuestion: audience, the forces at work, scope
boundaries, known assumptions, anything already decided.

### Step 3: Problem → Gate

Draft the Problem section (≤ 1 page, per the skill). Present it and ask:
- "Approve problem" — set `status: problem-approved`, continue
- "Revise" — take the feedback, redraft
- "Park it" — save as `status: draft`, stop

### Step 4: Proposal → Gate

Draft the Proposal — functional, user-oriented, one proposal per objective. Self-
check against the skill before presenting: any tech stack, file names, or
architecture in this section is a defect. Same gate: approve
(`status: proposal-approved`) / revise / park.

### Step 5: Implementation

Ask what shape the work takes:
- **Handed to launchpad** — write `## Work Packets` (orchestration format) and
  **Done When** checks per objective; note the handoff (`/stage` then `/launch`
  will pick it up, or `/mission-plan` copies it into the mission).
- **Product/program work** — prioritized backlog table with per-item
  specifications.
- **Not yet** — leave Implementation as Done When + TBD plan; the spec is still
  approved and usable.

### Step 6: Write and Report

Write to `specs/<slug>.md` (project-declared location supersedes). Report:

```
Spec: specs/<slug>.md   (status: <status>)
  Objectives: <n>  Proposals: <n>  Done-when checks: <n>
  <Next: /stage to run it | /roadmap to slot it | open questions to resolve: <n>>
```

The spec is a project artifact — commit it via the project's normal flow.

## Error Handling

| Scenario | Action |
|----------|--------|
| Referenced theme/item path missing | Ask for it, stop |
| User parks at any gate | Save with the honest `status`, stop cleanly |
| Existing spec found | Never overwrite silently — revise or new file, user's call |
