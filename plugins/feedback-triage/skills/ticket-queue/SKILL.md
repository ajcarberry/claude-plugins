---
name: ticket-queue
description: Use when reading, creating, updating, merging, or closing feedback-triage tickets — anything touching .feedback-triage/, the FT-NNNN queue, its index/ledger, watermarks, or ft.py; or when a hook blocks a direct edit to queue files.
---

# Ticket Queue — One Writer, One Ledger

The queue is the system of record. Its value is that it is **complete, unique,
and current** — so all changes go through `ft.py`, which locks, validates, and
logs every write. Full schema and command table:
[queue-schema.md](../../references/queue-schema.md).

```bash
FT="python3 ${CLAUDE_PLUGIN_ROOT}/scripts/ft.py"
$FT paths            # where everything lives
$FT stats            # counts by status / tier / spice, multi-raised tickets
$FT list --status new,needs-reinvestigation
$FT get FT-0007
```

## Rules

- **Never edit `queue/*.json` or `index.json` by hand** — the PreToolUse hook
  blocks it. If `ft.py` refuses a change, the refusal is the answer: fix the
  input, don't route around it.
- **Single writer.** Only the phase orchestrator calls write commands. Subagents
  write their results to files under `runs/` (and `investigations/`); the
  orchestrator applies them.
- **Read refusals.** Exit 1 = malformed input (fix and retry). Exit 2 = a rule
  said no (illegal transition, missing review, lint failure) — change the
  approach, never just retry.
- **Validate at the end of every phase:** `$FT validate` must print `"ok": true`
  before `state.sh save`. A failure is a bug to fix now, not later.
- **Persist** with `${CLAUDE_PLUGIN_ROOT}/scripts/state.sh pull` at the start of a
  phase and `state.sh save "<phase>: <summary>"` at the end.

## Status meanings

`new` (tracked, untouched) → `investigating` (claimed) → `investigated` (tier
work done) → `reported` (in Slack). `needs-reinvestigation` = recheck found a
material change. `blocked` = two failed investigations; needs a human.
Closed: `resolved`, `duplicate`, `invalid`.

## Fixing mistakes

| Mistake | Fix |
|---|---|
| Two tickets are the same issue | `$FT merge FT-B FT-A --reason "<shared symptom>"` (keeps the older/richer as A) |
| Item should not be tracked | recheck verdict `invalid` with evidence |
| Wrong type / title / summary | recheck verdict `corrected` with a patch |
| Wrong spiciness factors | `$FT spice FT-A --impact N --reach N [--bump ±1 --reason ...]` |
| A claim stuck after a crash | claims expire after 6 h; `$FT claim` picks them up again |
