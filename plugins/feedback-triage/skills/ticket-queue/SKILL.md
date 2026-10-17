---
name: ticket-queue
description: Use when the user asks to inspect or fix the feedback-triage queue directly — merge or split tickets, move a mis-linked source, rescore spiciness, unblock a ticket, check watermarks — or when a hook blocks a direct edit to .feedback-triage queue files.
---

# Ticket Queue — Fix It Through ft.py

All queue changes go through `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/ft.py`, which
locks, validates, and logs; a hook blocks hand edits to `queue/` and `index.json`.
A refusal is the answer — fix the input (exit 1) or the approach (exit 2). Schema:
[queue-schema.md](../../references/queue-schema.md). Commands: `ft.py help`.

| Need | Command |
|---|---|
| Two tickets are one issue | `merge <newer> <older> --reason "<shared symptom>"` |
| A source is on the wrong ticket | `move-source <ref> --to <id> --reason …` |
| Wrong type/title/summary | `recheck-apply` with verdict `corrected` + patch |
| Wrong spice factors | `spice <id> --impact N --reach N [--bump ±1 --reason …]` |
| Blocked ticket, now unblocked | `/feedback-triage:investigate <id>` (claims blocked tickets by id) |
| Integrity check | `validate` (must be ok before `state.sh save`) |

Persist after a manual fix: `${CLAUDE_PLUGIN_ROOT}/scripts/state.sh save "<what>"`.
