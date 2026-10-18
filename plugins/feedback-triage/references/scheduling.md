# Scheduling — Running the Loop Out of Band

`/recheck` is built to run unattended: it asks no questions, touches only tracked
tickets, and is quiet when nothing is due. `/sweep` runs the whole pipeline
without questions; its report is paste-ready text in the outbox. Pick the runner that matches how long the loop must live.

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
sweep        weekdays 08:45    recheck → intake → investigate → report
```

## Headless (cron, CI, Routines)

```bash
claude -p "/feedback-triage:sweep" \
  --permission-mode dontAsk \
  --allowedTools "Bash,Read,Write,Edit,Glob,Grep,Task,Skill,ToolSearch,mcp__github__*"
```

With `--bare`, installed plugins are skipped — add `--plugin-dir <path-to>/feedback-triage`.

## GitHub Actions

Run the same headless command from a `schedule:`-triggered workflow with
`anthropics/claude-code-action` (prompt `/feedback-triage:sweep`), `contents: write`
and `pull-requests: write` permissions, and the plugin installed for your org.

## Unattended safety

- Reports are never sent: unattended runs leave `reports/outbox/<run>/*.md`
  unrecorded; after pasting them into the tracker, run `ft.py sent <run> --all`.
- PRs from unattended runs are drafts when `investigate.draft_prs: true` (default).
- The hooks still apply: no PR without an approved review, no hand-edited queue.
- Run one writer at a time per queue: two runners saving conflicting queue changes
  makes `state.sh save` stop with `"conflict": true` rather than guess.
