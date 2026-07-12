---
description: Implement the mission — packet orchestration when a spec exists, express mode straight from the brief when it doesn't
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, Task, Skill, AskUserQuestion
---

# Launch — Implementation

Implementation only: no pushing, no PR — that's `/orbit`. The flight rules
(`test-driven-development`, `systematic-debugging`,
`verification-before-completion`) are in effect throughout, in both modes.

## Workflow

### Step 1: Preflight

- Read `.claude/mission/brief.md`. Missing → point to `/stage`, **STOP**.
- `git branch --show-current` — refuse to launch on `main`.
- Mode select: `.claude/mission/spec.md` with a `## Work Packets` section →
  **orchestrated**. Spec without packets, or no spec → **express**.

### Step 2a: Orchestrated Mode

Run the dispatch loop from [orchestration.md](../references/orchestration.md):

1. For each packet, write `.claude/mission/packets/P<N>.md` in the reference's
   format, then dispatch a fresh subagent at the packet's model tier. Prompt =
   packet file path + project context pointers, never conversation history.
   Independent packets dispatch in parallel; contract-providing packets go first.
2. Receive the ≤15-line report. Reports are claims, not evidence.
3. Verify asymmetrically — run the packet's done-check yourself, or dispatch a
   stronger-model checker for architecture-heavy packets. Nothing self-certifies.
4. Append packet, status, and evidence to `.claude/mission/log.md`.
5. On BLOCKED, change something (context, packet split, approach) — never
   redispatch verbatim. Three failures on one packet → **stop and surface**.

The orchestrator never implements. If you're editing code in this mode, a packet
was mis-scoped — fix the packet.

### Step 2b: Express Mode

Implement in the main session, straight from the brief (and spec, if one exists
without packets). The flight rules carry the discipline: failing check first, root
cause before remedy, fresh evidence before any "done." Log meaningful progress to
`.claude/mission/log.md` as you go — the log survives compaction; the conversation
doesn't.

### Step 3: Checkpoint Commits

Commit at coherent boundaries (a packet lands, a check passes) — invoke
`Skill: commit:commit-conventions` for staging and message rules. Fallback (commit
plugin not installed): match the style of recent `git log`, stage only related
changes together. Never push.

### Step 4: Docs

Near the end, invoke `Skill: docs:writing-docs` to check whether the change needs
doc updates; "nothing to update" is a normal outcome. Fallback (docs plugin not
installed): note that docs weren't checked. Commit any doc changes as their own
checkpoint.

### Step 5: Report + STOP

```
Launch complete.
  Packets:  <N/N done | express>
  Commits:  <count>
  Docs:     <updated | nothing to update | not checked>
  Log:      .claude/mission/log.md

  Run /orbit to validate, self-review, and open the PR.
```

Unfinished packets or open concerns → list them instead and say what's needed.
**STOP.** Validation and PR are `/orbit`'s job.

## Error Handling

| Scenario | Action |
|----------|--------|
| No mission brief | Point to `/stage`, stop |
| On `main` | Refuse |
| Packet BLOCKED ×3 | Stop, surface to user with the three attempts |
| Subagent dispatch fails | Retry once, then fall back to express for that packet |
| commit/docs plugin missing | Use stated fallback, note it once |
