---
description: Configure feedback-triage for this project — sources (GitHub repos, Slack channels), the tracker reports go to, persistence, worktree setup command, and a tool check
allowed-tools: Bash, Read, Write, Edit, ToolSearch, AskUserQuestion
argument-hint: "[--check]"
---

# Setup — Configure the Pipeline

`ft` = `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/ft.py`. Config lives in
`.claude/feedback-triage.json` (schema: [queue-schema.md](../references/queue-schema.md#config)).

`--check` → print `ft config`, `ft stats`, and the tool check below; **STOP**.

1. `ft init` (creates the state dir and a default config if absent).
2. One AskUserQuestion round, skipping what config already has:
   - GitHub repos to read (default: `git remote get-url origin`).
   - Slack channels to read, and the tracker reports will be pasted into (Jira, Linear, …).
   - Persistence: `branch` (recommended — the queue lives on its own
     `feedback-triage/state` branch shared by every run), `commit`, or `none`.
   - Base branch; whether PRs open as drafts (default yes).
   - `investigate.setup`: the command that makes a fresh checkout testable
     (e.g. `pip install -e '.[tests]'`, `npm ci`) — infer from the README/CI first.
   Write answers into the config with Edit.
3. Tool check: `gh api user` (REST; `gh issue list` may be GraphQL-blocked) or
   ToolSearch `+github`; ToolSearch `+slack read`; `python3 --version` (≥ 3.8).
   Missing Slack → intake reads Slack JSON exports only. Missing GitHub → GitHub
   sources are skipped. Say so plainly.
4. `state.sh pull` then `state.sh save "feedback-triage: setup"`
   (`${CLAUDE_PLUGIN_ROOT}/scripts/state.sh`).

```
feedback-triage configured — sources: <n GitHub, n Slack> · reports: paste into <tracker>
  State: <dir> (persist: <mode>) · Tools: GitHub <ok|missing> · Slack read <ok|missing>
  Next: /feedback-triage:intake · Loop: /loop 6h /feedback-triage:recheck
```
