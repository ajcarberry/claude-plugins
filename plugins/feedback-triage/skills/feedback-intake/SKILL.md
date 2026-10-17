---
name: feedback-intake
description: Use when reading GitHub issues or Slack channels to find bug reports and feature requests, deciding whether a message is feedback at all, or extracting ticket metadata (title, summary, severity, environment, linked PRs) from a report.
---

# Feedback Intake — Read Everything, Classify Everything

Every item read gets a class. Nothing is skipped silently: missing a report is as
bad as tracking one twice.

## Classify

| Class | Test |
|---|---|
| `bug` | something behaves differently from what the user expected or was promised |
| `feature` | a user wants a capability, option, or change that does not exist |
| `question` | asks how to do something that works today; no defect, no want |
| `noise` | chatter, thanks, bot posts, announcements, team status updates |

- A question that reveals a defect ("how do I export? the csv is missing a row")
  is a **bug**. A complaint that implies a want ("export is so slow") is a
  **feature** unless it names something broken.
- Closed GitHub issues: closed as completed → `noise`, reason "closed: fixed
  upstream"; closed as not planned → reason "closed: declined". Record `state`
  so a reopen brings it back.
- One message, two issues → two items, same URL; the second sets
  `source.ref` to the first's ref plus `~2` (`github:acme/app#12~2`).

## Refs

- GitHub: the issue URL. Slack: the **thread root** permalink. Replies that only
  say "same here"/"+1" are not items — add their authors to `plus_ones`. GitHub
  👍 reactions and "+1" comments count the same way.
- Put every GitHub/Slack URL in the text into `links`.
- `linked_prs`: every PR linked to or mentioned on the issue (timeline
  cross-references, "closes #N", comments) as `{"url", "state"}`. Investigators
  use these to avoid duplicating a fix already in flight.

## Fields

| Field | Rule |
|---|---|
| `title` | ≤ 90 chars, neutral. Bug: the symptom ("Login fails after SSO session expires"). Feature: the capability, not the mechanism ("Machine-readable list output", not "Add --json flag") |
| `summary` | ≤ 3 sentences of facts the source states. No guesses, no fixes |
| `excerpt` | ≤ 400 chars, verbatim — error text, steps, versions |
| `severity` | bugs only, from evidence: `critical` (data loss, security, outage) · `major` (core flow fails) · `minor` (workaround) · `trivial`; empty if unclear |
| `environment` | only what is stated: `version`, `os`, `browser`, `plan`, `platform` |
| `component`, `labels` | product area if obvious; GitHub labels verbatim |

Never invent a value to make a ticket look complete. Empty is honest.
