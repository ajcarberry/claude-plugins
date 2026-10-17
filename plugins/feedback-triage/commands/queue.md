---
description: Show the feedback-triage ticket queue — counts, the spiciest open tickets, multi-raised issues, or one ticket in full
allowed-tools: Bash, Read
argument-hint: "[FT-NNNN | status]"
---

# Queue — Read-Only View

`ft` = `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/ft.py`. Never writes.

- `FT-NNNN` → `ft get <id>`: title, type, status, tier + rationale, spice + factors,
  every source (relation, link, author), repro, linked/existing PRs, last recheck
  verdict, investigation file path, last 5 history events.
- a status → `ft list --status <status>`.
- nothing → `ft stats` + `ft list`: counts by status, the 5 spiciest open tickets,
  the 5 most-raised, watermarks.
