---
description: Draft, revise through HITL markers, and post the reply for one issue; labels, retitle, and close only as the maintainer directs
argument-hint: "<issue number> [post|labels|close]"
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, Agent, Skill
---

# /oss-triage:reply

Load `Skill: oss-triage:triage-reply`. Read `.oss-triage/config.md`.

- No `post|labels|close` word in `$ARGUMENTS`: read `repro/<n>/reply-draft.md`. If it has HITL markers, answer each in chat, apply, strip, show the changed lines. If it has none, run the adversarial reviewer if that has not happened, then present the draft path with `:1` and the proposed mechanics.
- `post`: the maintainer has said go on the current text. Post the comment with `--body-file`, then the label and title changes they approved, then close only if they said close. Confirm live state and report the URL.
- `labels` or `close`: do that step alone, as approved.

Never post text the maintainer has not seen in its final form. Log the outcome in the pass log.
