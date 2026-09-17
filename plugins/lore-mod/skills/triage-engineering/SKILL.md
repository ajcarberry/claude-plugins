---
name: triage-engineering
description: Rules for the running engineering list (FOR-ENGINEERING.md) and for the Slack summary to the dev team, including the per-item live check before sending. Load when adding to the list or drafting the summary.
---

# Triage engineering list and summary

## The list (`FOR-ENGINEERING.md`, template `templates/for-engineering.md`)

Two sections. **Confirmed**: community-reported, validated first-hand, reviewed with the maintainer; columns: what the community did, what we confirmed, why engineering should hear it, status. **Reported, not yet validated**: candidates under active validation only; unconfirmed items are dropped, not carried. Nothing we found ourselves goes on the list. Entries describe what the user did and what we saw; never a root cause or an implementation. Community-built tools qualify as awareness items. A contributor waiting on an answer qualifies. Quick factual questions for a specific owner (release owner, code owner) are framed as questions.

## The Slack summary (template `templates/slack-eng-summary.md`)

Reference as sent: the maintainer's message of 2026-09-17 (`reference/eng-summary-example.md`). Shape:

- One-line opener: what was done, at what scale, with what outcome, then "A few things came out of it worth sharing:". No greeting.
- One paragraph per item, blank line between, no bullet glyphs. Lead token is a markdown link with the reference as its text: `[Issue#208](url) - `, `[PR#82](url) - `; awareness items lead `FYI - `. Every other issue or PR named inside gets the same link form.
- Inside each paragraph: what happened, plain narrative; current state, including what moved today and who did it, @-mentioning whoever owns the next step or built the thing; one direct question to the team or the owner, ending with the @-mention. 60 to 110 words.
- Order: urgency first (anything red or blocking), then process questions, then waiting contributors, then patterns worth borrowing, FYI last. No closing line.
- Voice: first person singular for observations ("I see that", "Was thinking"), first person plural for team decisions and property ("do we want to", "our prebuilt binaries"). Contractions. Hedges where the writer is not the expert ("apparently", "not necessarily a bug", "seems like"; a "(?)" or ":shrug" is fine). Questions, never directives. A change's value in one clause; what it does in plain words; no root cause, no implementation. Community members credited by handle, their work framed as proposals. Backticks for versions, file names, config keys.

## Before it goes out

Dispatch `lore-mod:live-checker`, one per item, with the paragraph text. Each reports still accurate, changed, or partly changed with the exact phrase to fix. Apply fixes, then hand the file to the maintainer with HITL markers. On the first pass three of seven items needed corrections between drafting and sending.

## After it goes out

Fill the sent log; mark each item sent with the date.
