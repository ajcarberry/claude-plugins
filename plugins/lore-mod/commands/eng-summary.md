---
description: Build the engineering Slack summary from FOR-ENGINEERING.md in the maintainer's voice, live-check every item with one agent each, hand the file over with review markers
argument-hint: "[confirmed-only]"
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, Agent, Skill
---

# /lore-mod:eng-summary

Load `Skill: lore-mod:triage-engineering`. Read `.lore-mod/config.md`, `<work dir>/FOR-ENGINEERING.md`, and `reference/eng-summary-example.md`.

1. Take the Confirmed items (and nothing from the unvalidated section unless the maintainer says otherwise). Order: urgency, process questions, waiting contributors, patterns, FYI.
2. Fill `templates/slack-eng-summary.md` into `<work dir>/<date>-slack-eng-draft.md` with the HITL header. One paragraph per item in the shape and voice the skill defines. Every reference is a markdown link with `Issue#N` or `PR#N` as its text. @-mention owners by the handles in the config.
3. Dispatch `lore-mod:live-checker`, one per paragraph. Apply every correction; tell the maintainer what moved.
4. Hand the path with `:1`. Apply HITL markers as they come. When the maintainer says it is sent, archive the final text as `<date>-slack-eng-final.md` without the header, fill the sent log, and mark items sent.
