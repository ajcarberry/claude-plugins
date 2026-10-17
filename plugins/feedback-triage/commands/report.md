---
description: Phase 3 — write, lint, and render the engineering team's Slack report as copy-paste-ready text — a digest plus one templated, spiciness-rated message per investigated ticket
allowed-tools: Bash, Read, Write, Glob, Task, Skill
argument-hint: "[ticket ids] [--unattended]"
---

# Report — Paste-Ready Slack Text, Same Shape Every Time

`ft` = `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/ft.py`. Nothing is sent: the output
is text to paste into Slack.

1. `state.sh pull` (`${CLAUDE_PLUGIN_ROOT}/scripts/state.sh`). `ft due
   report-writing` (restricted to `$ARGUMENTS` ids if given) → tickets needing
   prose. Dispatch one `report-writer` per ticket in parallel with: ticket path,
   investigation path, `ft related <ID>` output (their recommendations), `out` =
   `<runs>/report-<UTC ts>/report-<ID>.json`.
2. `ft report-set <ID> --json <out>`. Exit 2 → redispatch that writer with the lint
   errors (≤ 2 retries); still failing → skip it this run and say so.
3. **Consistency check** — read the stored recommendations of tickets that list
   each other as related. If two contradict, never rewrite one past what its own
   investigation supports. Write **one** decision sentence ("FT-0002 and FT-0004
   need one choice: named units or plain digits.") and redispatch both writers to
   use it verbatim as `ask`. Never edit rendered files.
4. `ft render` (`--ids <ids>` when `$ARGUMENTS` names tickets) → nothing due: `Report: nothing new.` **STOP**. Else it writes the
   run dir with `paste.txt` (digest, then each ticket message, separated by
   "reply in thread" markers).
5. Print `paste.txt`: the digest in one fenced ```text block, then each ticket
   message in its own block, highest spice first. Then:
   `Post the digest in <report.channel or "your eng channel">, then each message
   as a reply in its thread. Bold needs Slack → Preferences → Advanced → "Format
   messages with markup".`
6. A human is reading this session → `ft sent <run> --all` (the printed report is
   the delivery). `--unattended` (sweep, CI, Routines) → do **not** record it; end
   with "Paste `<paste.txt path>`, then run `ft sent <run> --all`." Then
   `ft validate`, `state.sh save "report: <n> tickets"`.

To re-print a report later: `ft render --ids <ids>`.
