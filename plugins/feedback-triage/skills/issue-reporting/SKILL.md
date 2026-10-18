---
name: issue-reporting
description: Use when writing a feedback-triage report for the engineering team's issue tracker (Jira, Linear, GitHub, …) — summarising an investigated ticket into headline/what/findings/fix prose, applying ASD-STE100 / ELI18 style, or fixing text that ft.py lint rejected.
---

# Issue Reporting — A Ticket an Engineer Can Pick Up Cold

The report becomes a ticket in the team's tracker. Whoever opens it has never seen
the original issues and should not need to. You write the prose fields; `ft.py
render` adds the friendly intro, status line, sources, and layout from
`templates/report/`, so every report has the same shape. Prose holds **no** emoji,
bold, headers, or links — and **never an internal queue id** (`FT-…`); refer to an
issue by its title or GitHub number. Lint refuses ids.

## Two kinds of report

- **Researched report** — a problem worth solving, with the research: what happens,
  why, scope, what exists. No `fix` field.
- **Fix-ready report** — the same, plus a fix we are confident can merge: a linked
  upstream PR we tested (`existing_pr` verdict `fixes`), or our own change that
  passed independent review. `fix` is required here and refused anywhere else.

## Fields

| Field | Limit | Content |
|---|---|---|
| `headline` | ≤ 12 words, no end punctuation | the user-visible problem or want — becomes the ticket title |
| `what` | ≤ 2 sentences | who hits it, when, what they see (feature: what they want and why) |
| `findings` | 1–4 items, ≤ 20 words each | verified facts, most decisive first: repro (with the inputs/flags needed), root cause (`fn` in backticks), scope, prior art, other PRs and their state; for medium tickets, the fix approaches in one line each |
| `fix` | fix-ready only, ≤ 3 sentences | what the fix changes, the evidence it works, and the one thing to check before merging (never a `handoff` step: the template prints those). A PR named here must be the linked fix PR |

Only facts from the investigation file. A conflict with a related ticket, or a
decision the team must make, is one finding that names the related issue by title.

## Style — ASD-STE100, written for a smart 18-year-old

1. One idea per sentence; ≤ 20 words. Active voice, subject first.
2. Simple present/past tense. Plain verbs: use, fail, show, add, fix, stop.
3. One word per meaning — say "error" every time, not error/failure/crash.
4. No hedges or filler; state confidence once: "Not confirmed." "We reproduced it."
5. Numbers as digits with units: "3 users", "2.4.1", "after 60 minutes".
6. Internal code names in `backticks`, only when an engineer needs them.

Bad: "We've basically been seeing a number of reports that might possibly relate
to SSO." Good: "Users who stay idle for 60 minutes cannot log in again."

`ft.py lint` enforces the countable rules and bans filler words (just, simply,
very, really, basically, leverage, utilize, in order to, …). Fix every error;
warnings are hints.
