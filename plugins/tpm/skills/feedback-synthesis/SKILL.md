---
name: feedback-synthesis
description: Use when aggregating raw community or user feedback — Discord/Slack threads, GitHub discussions and issues, support tickets, interview notes, CSV exports — into themes, or when deciding whether a feedback theme needs deeper investigation (a "dig").
---

# Feedback Synthesis — Raw Signal to Themes

## Sources

Source-agnostic: work from whatever exists — exported chat logs, `gh` for GitHub
discussions/issues, connected MCP tools (Discord, Slack) when present, CSVs, notes.
Never block on a missing source; name what was and wasn't covered in the output.

## Clustering discipline

- Cluster by **user problem**, not by feature request. "Add a --json flag" and
  "output is hard to parse in CI" are one theme: machine-readable output.
- Keep the user's words: every theme carries 1–3 verbatim quotes.
- **Frequency ≠ severity.** Track both: how many voices, and how bad the worst
  case is. One report of data loss outranks fifteen requests for a dark theme.
- Resist premature solutions — themes state problems. Solutions belong in
  `/roadmap` and `/spec`.

## Evidence discipline

Every theme cites its sources and counts: `(7 mentions: 4 Discord, 2 issues,
1 interview — links/refs)`. A theme with no citable evidence is an impression, not
a theme — either find the evidence or drop it.

## When a theme needs a dig

Flag `needs-dig` when the signal is real but not actionable yet: the reports
conflict, the root problem is unclear, severity is unknown, or the theme
contradicts what the roadmap assumed. Don't flag themes that are merely large —
size alone is already actionable.

**The dig:** pull one thread to the bottom — search the full history for related
reports, read the connected issues/PRs, read the relevant code to see what's
actually happening. Output is a short findings note: what's really going on, who's
affected and how badly, what evidence changed, recommendation (roadmap item / spec /
close as understood). Findings feed `/roadmap` (reactive) or `/spec`.

## Output

Use the [feedback-themes template](../../templates/feedback-themes.md) — themes
ranked by (severity, then frequency), each with evidence, quotes, and a status
(`ready` | `needs-dig` | `dug` with findings link).
