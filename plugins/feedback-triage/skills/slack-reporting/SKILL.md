---
name: slack-reporting
description: Use when writing a feedback-triage report for the engineering team's Slack — summarising an investigated FT-NNNN ticket into headline/what/findings/recommendation/ask prose, applying ASD-STE100 / ELI18 style, or fixing text that ft.py lint rejected.
---

# Slack Reporting — Five Fields, Plain Words

The report replaces reading the original issues. You write five prose fields;
`ft.py render` adds every emoji, badge, pepper, link, and line break from the
template, so every report has the same shape. Prose holds **no** emoji, bold,
headers, or links.

## Fields

| Field | Limit | Content |
|---|---|---|
| `headline` | ≤ 12 words, no end punctuation | the user-visible problem or want — not the fix, not the component |
| `what` | ≤ 2 sentences | who hits it, when, what they see (feature: what they want to do and why) |
| `findings` | 1–3 items, ≤ 20 words each | one verified fact each, most decisive first: repro result, root cause (`fn` in backticks), scope, an existing PR's verdict. Keep the conditions needed to see it (inputs, flags) |
| `recommendation` | ≤ 2 sentences | a command to the team (required for medium/low) |
| `ask` | 1 sentence, optional | the one decision only a human can make |

Recommendation by outcome:
- **Existing PR fixes it** → "Review and merge PR #N." + the one thing to check.
- **Low, our fix** → "Review and merge the PR." (no PR opened → "the branch.") +
  the one thing to check. The template prints the link — don't repeat it.
- **Medium** → "Pick option A: <what it is>" + why — readers never see the
  options, so name the option's content.
- **High** → where an engineer should start.

Only facts from the investigation file. A PR named in the recommendation must be
the one the template links (`ft.py lint` checks). A conflict with a related
ticket goes in `ask`, naming it.

## Style — ASD-STE100, written for a smart 18-year-old

1. One idea per sentence; ≤ 20 words. Active voice, subject first.
2. Simple present/past tense. Plain verbs: use, fail, show, add, fix, stop.
3. One word per meaning — say "error" every time, not error/failure/crash.
4. Instructions are commands: "Merge the PR." "Pick option B."
5. No hedges or filler; state confidence once: "Not confirmed." "We reproduced it."
6. Numbers as digits with units: "3 users", "2.4.1", "after 60 minutes".
7. Internal names in `backticks`, only when an engineer needs them to act.

Bad: "We've basically been seeing a number of reports that might possibly relate
to SSO." Good: "Users who stay idle for 60 minutes cannot log in again."

`ft.py lint` enforces the countable rules and bans filler words (just, simply,
very, really, basically, leverage, utilize, in order to, …). Fix every error;
warnings (passive voice, end punctuation) are hints.
