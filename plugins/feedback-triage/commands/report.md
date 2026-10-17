---
description: Phase 3 — write, lint, render, and send the engineering team's Slack report — one templated, spiciness-rated message per investigated ticket under a digest
allowed-tools: Bash, Read, Write, Glob, Task, Skill, ToolSearch, AskUserQuestion
argument-hint: "[ticket ids] [--yes] [--dry-run]"
---

# Report — Slack, Same Shape Every Time

Load `Skill: feedback-triage:slack-reporting` and `Skill: feedback-triage:ticket-queue`.
`ft` below means `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/ft.py`.

## Step 1: Write prose (fan out)

- `state.sh pull` (`${CLAUDE_PLUGIN_ROOT}/scripts/state.sh`).
- `ft due report-writing` → tickets needing (new or refreshed) report prose.
  Restrict to `$ARGUMENTS` ids if given.
- Dispatch one `report-writer` per ticket in parallel with ticket path,
  investigation path, `out` = `<runs>/<run>/report-<ID>.json`.
- Apply: `ft report-set <ID> --json <out>`. Exit 2 → redispatch that writer with
  the lint errors (max 2 retries); still failing → skip the ticket this run, list
  it in the summary.

## Step 2: Render

`ft render` (or `--ids …`) → outbox run dir + manifest: `00-digest.txt` then one
file per ticket, highest spice first. Nothing due → `Report: nothing new.`
**STOP**. Never edit rendered files — re-run `report-set` and `render` instead.

## Step 3: Deliver

- `--dry-run` → show the rendered messages and outbox path. **STOP**.
- Find the Slack send tool (ToolSearch `+slack send message`). None → show the
  messages and outbox path: "Post these, then record each with
  `ft sent <run> --file <file> --permalink <url>`." **STOP**.
- Unless `--yes` or `report.auto_send` is true: show the digest and the ticket
  messages, then AskUserQuestion — send all / send selected / don't send.
- Send to `report.channel`, each file's text **verbatim**:
  - `mode: thread` — send the digest; then each ticket file as a reply with the
    digest's `thread_ts`.
  - `mode: messages` — each ticket file as its own message; skip the digest.
  After **each** send: `ft sent <run> --file <file> --permalink <url> --ts <ts>`.
- The hook refuses any ticket-naming Slack text that is not an outbox file.

## Step 4: Persist + summarise

`ft validate` → `state.sh save "report: <n> sent"`.

```
Report <run>: <n> tickets → <#channel | outbox>
  🌶️🌶️🌶️🌶️ <n> · 🌶️🌶️🌶️ <n> · 🌶️🌶️ <n> · 🌶️ <n>   Closed announced: <n>
  Digest: <permalink>      Skipped (lint): <ids or none>
```

## Error Handling

| Scenario | Action |
|----------|--------|
| A send fails mid-run | Stop sending; already-sent files are recorded; re-run sends only the rest |
| Report channel unset | Ask once (interactive) or render-only (unattended) |
| User declines | Leave the outbox in place; nothing is marked sent |
