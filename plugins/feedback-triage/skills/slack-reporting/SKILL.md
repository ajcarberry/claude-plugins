---
name: slack-reporting
description: Use when writing or sending a feedback-triage report to Slack for the engineering team — summarising an investigated FT-NNNN ticket, writing headline/what/findings/recommendation prose, choosing the spiciness wording, or when ft.py lint rejects report text.
---

# Slack Reporting — Same Shape Every Time, Readable in 20 Seconds

The report replaces the engineer reading the original issues. It must carry the
problem, the evidence, and the next action — and look identical in shape every
time, so readers learn where to look.

## Division of labour

- **You write five prose fields.** Content only: no emoji, no bold, no links.
- **`ft.py render` does everything else** — emoji, spiciness peppers, tier badge,
  repro badge, raise count, source links, PR link, layout — from
  `templates/slack/` and `theme.json`. A project overrides the look in
  `.claude/feedback-triage/slack/` and `.claude/feedback-triage/theme.json`.
- **The hook refuses** any Slack message naming a ticket that is not a rendered
  outbox file, so reports can't drift from the template.

## Writing the fields

Follow [slack-style.md](../../references/slack-style.md) (ASD-STE100 rules, ELI18,
field limits, examples). The short version:

- **headline** — the user-visible problem in ≤ 12 words. "Login returns 500 after
  the SSO session expires". Not the fix, not the component name.
- **what** — who hits it, when, what they see. ≤ 2 sentences.
- **findings** — 1–3 verified facts, most decisive first: the repro result, the
  root cause (file/function in backticks), the scope. Each ≤ 20 words. Only facts
  from the investigation file; if it isn't there, it doesn't go here.
- **recommendation** — a command to the team, shaped by tier:
  high → where an engineer should start; medium → "Pick option A: …" + why;
  low → "Review and merge the PR." + the one thing to check.
- **ask** — optional, one decision only a human can make.

## Spiciness in prose

The pepper count comes from `ft.py`; don't restate it ("this is very urgent").
Make the prose *justify* it: a 🌶️🌶️🌶️🌶️ ticket's findings must show the data
loss or the reach; a 🌶️ ticket reads calmly.

## Lint loop

`ft.py report-set <ID> --json <file>` lints and stores. On exit 2, read every
error, rewrite those fields, and retry. Warnings (passive voice, end punctuation)
are worth fixing too — they are the difference between consistent and almost
consistent.

## Delivery

`report.mode: thread` (default): post the digest, then each ticket file as a
reply in the digest's thread, highest spice first. Send the outbox text
**verbatim** and record each send with `ft.py sent`. Draft-only unless
`report.auto_send` is true or the run was started with `--yes`; never post
without one of those or the user's OK.
