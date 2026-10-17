---
description: Configure feedback-triage for this project — sources (GitHub repos, Slack channels), report channel, persistence, and a first dry run
allowed-tools: Bash, Read, Write, Edit, ToolSearch, AskUserQuestion
argument-hint: "[--check]"
---

# Setup — Configure the Pipeline

`ft` below means `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/ft.py`. Load
`Skill: feedback-triage:ticket-queue` for the queue rules.

## Mode: Check (`--check`)

Print `ft paths`, `ft config`, `ft stats`, and the tool check from Step 3. Report
what is missing. **STOP.**

## Step 1: Initialise

`ft init` — creates the state dir and `.claude/feedback-triage.json` (defaults)
if absent. Existing config → read it and treat this run as an edit.

## Step 2: Gather (one AskUserQuestion round, skip what config already has)

- **GitHub repos** to read issues from (default: this repo's `origin`, from
  `git remote get-url origin`).
- **Slack channels** to read feedback from, and the **report channel** for the
  engineering team. Resolve names to IDs with the Slack MCP tools when present.
- **Persistence**: `branch` (recommended — queue on its own
  `feedback-triage/state` branch, shared by every run), `commit` (on the current
  branch), or `none`.
- **Base branch** for fixes (default: the repo's default branch) and whether
  change requests open as drafts (default yes).

Write the answers into the config with Edit (it is not a queue file). Keys and
defaults: [queue-schema.md](../references/queue-schema.md) and `ft config`.

## Step 3: Tool check

- GitHub: `gh auth status`, else ToolSearch `+github list issues`.
- Slack: ToolSearch `+slack read` and `+slack send`.
- `python3 --version` (3.8+), `git --version`.

Missing Slack → intake reads Slack exports only and reports render to the outbox
for manual posting. Missing GitHub → GitHub sources are skipped. Say so plainly.

## Step 4: Persist + first look

`${CLAUDE_PLUGIN_ROOT}/scripts/state.sh pull`, then `state.sh save "feedback-triage: setup"`.
Commit `.claude/feedback-triage.json` only if the user asks (it is project
config, normally committed with their next change).

```
feedback-triage configured.
  Sources:   <n GitHub repos, n Slack channels>
  Reports:   <#channel | outbox only>  (auto_send: <true|false>)
  State:     <dir> (persist: <mode>)
  Tools:     GitHub <ok|missing> · Slack read <ok|missing> · Slack send <ok|missing>

  Next: /feedback-triage:intake        (first run reads the last <lookback_days> days)
  Loop: /loop 6h /feedback-triage:recheck   · scheduling: references/scheduling.md
```
