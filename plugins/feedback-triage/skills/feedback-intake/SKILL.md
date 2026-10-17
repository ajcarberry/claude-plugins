---
name: feedback-intake
description: Use when reading GitHub issues or Slack channels to find bug reports and feature requests, deciding whether a message is feedback at all, extracting ticket metadata from a report, or deciding whether two reports describe the same issue (duplicate vs. related vs. distinct).
---

# Feedback Intake — Find It, Track It Once

The goal is a queue engineering can trust: **every** bug report and feature
request in the sources, each tracked **exactly once**, each linked to **every**
place it was raised. Missing one and tracking one twice are equal failures.

## 1. Is it feedback?

Classify every item read — none may be skipped silently.

| Class | Test | Then |
|---|---|---|
| `bug` | something behaves differently from what the user expected or was promised | candidate |
| `feature` | a user wants a capability, option, or change that does not exist | candidate |
| `question` | asks how to do something that works today; no defect, no want | `ignore` with reason |
| `noise` | chatter, thanks, bot posts, announcements, our own team's status updates | `ignore` with reason |

- GitHub issues **closed** before you read them: closed as completed/fixed →
  `ignore` "closed: fixed upstream"; closed as not planned → `ignore` "closed:
  declined". Open issues are always candidates.
- A question that reveals a defect ("how do I export? the button does nothing") is
  a **bug**. A complaint that implies a want ("exporting is so slow") is a
  **feature** unless it names something broken.
- One message can hold two issues. Split it: two candidates, same URL; the second
  sets `ref` explicitly with a `~2` suffix (`github:acme/app#12~2`) so the ledger
  tracks both.
- Reports from our own engineers count when they describe user-facing problems.

## 2. The source ref (what makes dedup deterministic)

- GitHub: the issue URL → `github:owner/repo#N`. PRs are not feedback unless the
  config includes them.
- Slack: the **thread root** permalink → `slack:CHANNEL/TS`. Replies that only add
  "same here" / "+1" are not new candidates — put their authors in `plus_ones`.
  A reply that raises a *different* issue is its own candidate with its own ts.
- Put every GitHub/Slack URL found in the text into `links[]` — `ft.py` uses them
  to attach cross-posts to the ticket that already tracks the linked source.

## 3. Extract metadata

| Field | Rule |
|---|---|
| `title` | ≤ 90 chars, neutral. Bug: the symptom — "Login fails after SSO session expires", not "URGENT login broken!!". Feature: the capability, not the mechanism — "Machine-readable list output", not "Add --json flag" |
| `summary` | ≤ 3 sentences of facts the source states. No guesses, no fixes |
| `excerpt` | ≤ 400 chars **verbatim** — the most informative lines (error text, steps) |
| `severity` | bugs only, the reporter's evidence: `critical` (data loss, security, outage) · `major` (core flow fails) · `minor` (workaround) · `trivial` — empty if unclear |
| `environment` | only what the source states: `version`, `os`, `browser`, `plan`, `platform` |
| `component` | product area if obvious from text or issue labels; else empty |
| `labels` | existing GitHub labels, verbatim |

Never invent a field to make a ticket look complete. Empty is honest.

## 4. Same issue or not?

Run `ft.py search <key words>` for every would-create candidate, and compare
candidates in the same batch with each other.

- **Duplicate** (`duplicate_of`): same user problem **and** same observable
  symptom or same want. Different words, channels, and reporters are expected.
  *"SSO logout loop on Safari"* and *"can't log back in after being idle, keeps
  redirecting"* → duplicate if both show the redirect loop after expiry.
- **Distinct**: same area, different symptom or different want. *"Export is slow"*
  and *"export drops the last row"* are two tickets. A feature request that
  would fix a bug is a separate ticket from the bug.
- **Unsure** → keep distinct, and add the other ticket's id to the summary
  ("Possibly related: FT-0004"). Recheck and investigation can merge later;
  an unmerge is impossible to do cleanly.

Write the reason for every `duplicate_of` in `duplicate_reason` — one sentence
naming the shared symptom.

## Candidate file format

Readers write one file per source; see the `source-reader` agent for the exact
JSON. The orchestrator applies it with `ft.py upsert` / `ft.py ignore` — readers
never write to the queue.
