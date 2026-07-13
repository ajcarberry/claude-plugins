---
description: Review community-raised GitHub issues and PRs against the roadmap and specs — classify, and draft alignment feedback
argument-hint: "[issue/PR numbers | filters, e.g. 'label:needs-triage']"
allowed-tools: Bash, Read, Write, Glob, Grep, Task, Skill, AskUserQuestion
---

# Triage — Keep the Tracker Aligned with the Direction

Load `Skill: tpm:triage-alignment` first — it owns the source-of-truth lookup,
classification, and feedback tone.

## Workflow

### Step 1: Scope

- `$ARGUMENTS` names issues/PRs or a filter → triage exactly those.
- Otherwise: `gh issue list` + `gh pr list` for open items with no maintainer
  response or a needs-triage label, newest first, capped at ~15 per run (say what
  was left out).

### Step 2: Source of Truth

Locate roadmap + specs per the skill (default `docs/roadmap.md`, `specs/`).
Missing → warn once, triage on judgment, and note each verdict as
"no written roadmap — maintainer judgment".

### Step 3: Classify Each Item

Per the skill: verify first (read fully, check duplicates, read PR diffs, reproduce
cheap claims), then classify **aligned / misaligned / needs-decision**. Batch
independent verifications through parallel subagents (one per item, ≤15-line
verdicts) when the list is long.

### Step 4: Draft Feedback

For each item, draft the maintainer response in the skill's tone (thank
concretely → reasoning with roadmap/spec citation → aligned path if any →
decisive close). needs-decision items get no public reply yet — they get a line in
the routing list instead.

### Step 5: Report + Approve

```
Triage: <N> items
  aligned:        <n> — <labels/milestones applied or proposed>
  misaligned:     <n> — replies drafted below
  needs-decision: <n> — routed to /roadmap (reactive)
```

Show every drafted reply. Then AskUserQuestion per batch: post all / post selected /
edit / don't post. **Nothing is posted to GitHub without explicit approval.**

## Error Handling

| Scenario | Action |
|----------|--------|
| `gh` unavailable | Stop — triage is GitHub work; say what's needed |
| No roadmap/specs found | Warn, judgment-only mode, flag verdicts as such |
| Item already triaged | Skip, note it |
| User declines posting | Save drafts to `docs/feedback/triage-<date>-drafts.md` |
