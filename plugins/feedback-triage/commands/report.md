---
description: Phase 3 — write, lint, and render tracker-ready reports (Jira, Linear, GitHub, …) — one friendly, standalone Markdown report per investigated ticket, with a proposed fix when one is ready to merge
allowed-tools: Bash, Read, Write, Glob, Task, Skill
argument-hint: "[ticket ids] [--unattended]"
---

# Report — Paste-Ready Tickets, Same Shape Every Time

`ft` = `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/ft.py`. Nothing is sent: the output
is Markdown to paste into the team's tracker, one ticket per report.

1. `state.sh pull` (`${CLAUDE_PLUGIN_ROOT}/scripts/state.sh`). `ft due
   report-writing` (restricted to `$ARGUMENTS` ids if given) → `[{id, fix_ready}]`
   needing prose. Dispatch one `report-writer` per ticket in parallel (foreground calls in one message) with: ticket
   path, investigation path, `fix_ready`, `ft related <ID>` output, `out` =
   `<runs>/report-<UTC ts>/report-<ID>.json`.
2. `ft report-set <ID> --json <out>`. Exit 2 → redispatch that writer with the lint
   errors (≤ 2 retries); still failing → skip it this run and say so.
3. **Consistency check** — read the stored findings/fix of tickets that list each
   other as related. If two contradict, never rewrite one past what its own
   investigation supports: write **one** decision sentence naming both issues by
   title and redispatch both writers to use it verbatim as a finding.
4. `ft render` (`--ids <ids>` when `$ARGUMENTS` names tickets) → nothing due:
   `Report: nothing new.` **STOP**. Else it writes one `NN-<slug>.md` per report
   plus `all-reports.md`. A report that would show an internal id is held (`held`),
   the rest still render — name the held ones in the summary.
5. Print each report in its own fenced ```markdown block, fix-ready reports first.
   Then a short run summary (not part of any report): reports by kind, issues
   closed since the last report (`closed` from render), and the backlog
   (`backlog`: not yet investigated, blocked).
   Close with: "Paste each report into <report.tracker or "your tracker"> as its
   own ticket — the first line is the title."
6. A human is reading this session → `ft sent <run> --all`. `--unattended` (sweep,
   CI, Routines) → do **not** record it; end with "Paste the reports in
   `<run dir>`, then run `ft sent <run> --all`." Then `ft validate`, `state.sh save
   "report: <n> tickets"`.

To re-print a report later: `ft render --ids <ids>`.
