---
description: Draft an audience-tailored update — community post or executive sponsor update — from the roadmap, decisions, and feedback record
argument-hint: "<community | exec> [topic/period]"
allowed-tools: Bash, Read, Write, Glob, Grep, Skill, AskUserQuestion
---

# Comms — Same Facts, Right Altitude

Load `Skill: tpm:stakeholder-comms` first — it owns the audience model and the
facts-only rule.

## Workflow

### Step 1: Audience and Scope

Audience from `$ARGUMENTS` (`community` | `exec`); missing → ask. Scope: the topic/
period given, or default to "since the last update" (find prior updates in
`docs/updates/`, or ask what period to cover).

### Step 2: Gather the Facts

Only from artifacts: roadmap (+ displacement log), latest themes doc and dig
findings, merged PRs / releases in the period (`gh`), decision records. Anything
not in an artifact doesn't go in the draft. Note contributor names for credit
(community) and commitment status (exec).

### Step 3: Draft

Render per the audience template —
[community-update](../templates/community-update.md) or
[exec-update](../templates/exec-update.md) — following the skill's rules: reasoning
attached to every decision, loops closed on feedback, bad news at the same fidelity
for both audiences, artifacts linked.

### Step 4: Review + Save

Show the full draft. AskUserQuestion: save / revise / cancel. On save, write to
`docs/updates/<YYYY-MM-DD>-<audience>.md` and stop:

```
Draft saved → docs/updates/<date>-<audience>.md
Posting is yours — nothing has been sent or published.
```

**This command never posts, sends, or publishes.** If both audiences need updates,
run it twice — same facts, two renderings.

## Error Handling

| Scenario | Action |
|----------|--------|
| No artifacts to draw from | Say which artifacts are missing; a comms run needs a roadmap or themes doc at minimum |
| Ambiguous audience | Ask — never guess altitude |
| User cancels | Discard the draft |
