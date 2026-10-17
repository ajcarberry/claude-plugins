# Scheduling — Running the Loop Out of Band

`/recheck` is built to run unattended: it asks no questions, touches only tracked
tickets, and is quiet when nothing is due. `/sweep --yes` runs the whole pipeline
unattended. Pick the runner that matches how long the loop must live.

| Runner | Lives | Use when |
|---|---|---|
| `/loop 6h /feedback-triage:recheck` | while this Claude Code session stays open (recurring loops expire after 7 days) | trying it out; a session you keep open on a box |
| Desktop scheduled task | on your machine, across restarts | one maintainer, local repo |
| Claude Code Routine (cloud, min 1 h) | in the cloud, no machine needed | team default; pair with `state.persist: branch` |
| GitHub Actions `schedule:` | in CI | org already runs Claude in Actions; auditable logs |

All runners share one queue through `state.persist: branch` — each run starts with
`state.sh pull` and ends with `state.sh save`, so a recheck from CI and an intake
from a laptop see the same tickets.

## Suggested cadence

```
recheck      every 6 h         cheap; keeps facts fresh, closes resolved tickets
sweep --yes  weekdays 08:45    recheck → intake → investigate → report
```

## Headless (cron, CI, Routines)

```bash
claude -p "/feedback-triage:sweep --yes" \
  --permission-mode dontAsk \
  --allowedTools "Bash,Read,Write,Edit,Glob,Grep,Task,Skill,ToolSearch,mcp__slack__*,mcp__github__*"
```

With `--bare`, installed plugins are skipped — add `--plugin-dir <path-to>/feedback-triage`.

## GitHub Actions sketch

```yaml
on:
  schedule: [{ cron: "45 8 * * 1-5" }]
  workflow_dispatch:
jobs:
  sweep:
    runs-on: ubuntu-latest
    permissions: { contents: write, pull-requests: write, issues: read }
    steps:
      - uses: actions/checkout@v4
        with: { fetch-depth: 0 }
      - uses: anthropics/claude-code-action@v1
        with:
          anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
          prompt: "/feedback-triage:sweep --yes"
          # plus the Slack MCP server config and plugin install for your org
```

## Unattended safety

- `report.auto_send: true` (or `--yes`) is required to post to Slack without a
  human; otherwise the run renders the outbox and stops.
- PRs from unattended runs are drafts when `investigate.draft_prs: true` (default).
- The hooks still apply: no hand-written Slack reports, no PR without review, no
  direct queue edits.
