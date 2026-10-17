# feedback-triage

Feedback in, engineering-ready reports out. The plugin finds bug reports and
feature requests in GitHub issues and Slack, tracks each one **once** in a
persistent queue, researches each with a dedicated subagent, and produces a
templated, spiciness-rated Slack report ready to paste. The aim: the engineering team reads the
report, not the raw issues, and low-complexity fixes arrive as reviewed PRs.

Self-contained: it depends on no other plugin.

## Pipeline

```
           ┌──────────── /recheck (loop: /loop, Routine, CI) ─────────────┐
           ▼                                                              │
GitHub ─┐                                                                 │
        ├─▶ /intake ─▶ queue ─▶ /investigate ─▶ /report ─▶ Slack #eng      │
Slack ──┘   dedup +     FT-NNNN   per ticket:     digest + one             │
            link all     .json    high → findings  templated message ──────┘
            sources               medium → options  per ticket, 🌶️–🌶️🌶️🌶️🌶️
                                  low → reviewed PR
/sweep = recheck → intake → investigate → report        /queue = read-only view
```

| Command | Phase | Does |
|---|---|---|
| `/feedback-triage:setup` | — | sources, report channel, persistence, tool check |
| `/feedback-triage:intake` | 1 | read sources since each watermark; track every bug/feature once; link every place it was raised; record non-feedback as ignored |
| `/feedback-triage:recheck` | loop | fact-check **only tracked** tickets: still open? fixed upstream? new info? corrected fields? Never asks, never creates |
| `/feedback-triage:investigate` | 2 | one `bug-investigator` / `feature-analyst` per ticket; complexity-gated depth; an existing fix PR is tested and recommended instead of duplicated; low tier → `change-reviewer` → draft PR |
| `/feedback-triage:report` | 3 | `report-writer` prose → `ft.py lint` → `ft.py render` → paste-ready Slack text (digest + thread replies) |
| `/feedback-triage:sweep` | all | the full loop, no questions asked |
| `/feedback-triage:queue` | — | counts, spiciest, most-raised, one ticket in full |

## Design

**Skills teach, scripts decide, hooks enforce.**

- **`scripts/ft.py`** (stdlib Python) is the only writer of the queue. It owns
  the dedup ledger (one source ref → one ticket; cross-links attach; judged
  duplicates attach; non-feedback is recorded, never dropped), monotonic
  per-source watermarks, the status state machine, the tier contracts (medium
  needs ≥ 2 options, low needs a branch and an approved review), the spiciness
  formula, the Slack prose lint, and the template renderer.
- **Skills** hold judgment: what counts as feedback and what counts as a duplicate
  (`feedback-intake`), how to triage/repro/research/implement (`issue-investigation`
  + bug and feature playbooks), what a recheck may change (`ticket-verification`),
  how to write a report (`slack-reporting`), queue discipline (`ticket-queue`).
- **Agents** are tiered: sonnet reads sources (`source-reader`), verifies
  (`ticket-verifier`), and writes prose (`report-writer`); opus investigates
  (`bug-investigator`, `feature-analyst`) and reviews (`change-reviewer`).
  Subagents get file paths, never conversation history, and never write the
  queue — the orchestrator applies their result files through `ft.py`. Each actor
  loads only what it acts on (≈ 0.5–4k tokens of instructions).
- **Hooks** (`scripts/hook.py`, PreToolUse, deterministic file checks):
  no direct edits to queue files; no push/PR of an `ft/FT-NNNN-*` branch unless the
  ticket is low tier with an approved independent review. Escape hatch:
  `FT_SKIP_GATE=1`.

References: [queue-schema](references/queue-schema.md) ·
[complexity](references/complexity.md) · [spiciness](references/spiciness.md) ·
[scheduling](references/scheduling.md)

## A report

```
🌶️🌶️🌶️ *FT-0001 · CSV export drops the newest task*
🐛 Bug · 🔧 PR ready · Hot · raised 7× ✅ Repro'd
*What:* Users who export to CSV lose their most recent task. The file has one row too few.
*Found:*
• `export_csv` loops over `tasks[:-1]`, so it skips the last task.
• We reproduced it with a failing test on 2.4.1.
*Do:* Review and merge the PR. Check the new test covers an empty list.
👉 Review the PR: https://github.com/acme/tasklite/pull/12
🐙 tasklite#1 https://github.com/acme/tasklite/issues/1 · 💬 #product-feedback https://acme.slack.com/archives/…
```

Links are bare URLs so the text pastes cleanly into Slack's composer (`<url|label>`
markup only works through the API). Bold needs Slack → Preferences → Advanced →
"Format messages with markup". Look and wording are templated: `templates/slack/{ticket,digest}.txt` and
`theme.json`. Override per project in `.claude/feedback-triage/slack/` and
`.claude/feedback-triage/theme.json`.

## State and persistence

Config: `.claude/feedback-triage.json`. Queue: `.feedback-triage/` (configurable).
`state.persist`:

- `branch` (default) — the queue lives on an orphan `feedback-triage/state`
  branch, checked out as a worktree; every run pulls first and pushes after, so
  laptops, Routines, and CI share one queue without touching product branches.
- `commit` — committed to the current branch. `none` — local files.

## Install

```
/plugin install feedback-triage --marketplace ajcarberry/claude-plugins
```

Then run `/feedback-triage:setup` in the project whose feedback you want triaged.

## Requirements

`python3` ≥ 3.8, `git`. GitHub: `gh` (authenticated) or the GitHub MCP server.
GitHub reads use the REST API (`gh api`). Slack: a Slack MCP server for live
reading; without one, intake reads Slack JSON exports. Reports are always
paste-ready text — nothing is posted automatically.

## Scheduling

`/loop 6h /feedback-triage:recheck` for a session; a Routine or GitHub Actions
cron running `/feedback-triage:sweep` for the team. See
[scheduling.md](references/scheduling.md).

## Known limits

- **One writer at a time per queue.** `state.persist: branch` merges by git
  rebase. Overlapping runners (e.g. a CI recheck during a laptop investigate) can
  conflict; `state.sh` then keeps the losing run on a pushed backup branch and
  stops, but recovering an interrupted *investigate* (claims, opened PRs) needs a
  human. Schedule phases so they don't overlap.
- `ft/` branches that are not opened as PRs stay on the runner that built them.
- Slack replies in threads older than the read window are not read; recheck's
  "seen but untracked" URLs are printed, not queued.

## Development

```bash
python3 -m unittest discover -s plugins/feedback-triage/tests   # ft.py + hooks
plugins/feedback-triage/evals/run.sh setup /tmp/ft-eval          # fixture project
plugins/feedback-triage/evals/run.sh intake /tmp/ft-eval         # headless run + score
```

`evals/` holds a fixture product (`tasklite`, with planted bugs) and GitHub/Slack
exports with duplicates, cross-posts, a split message, and noise, plus scorers for
intake (coverage, dedup precision/recall, type accuracy) and investigation/report
quality (tier accuracy, spice floors, lint, message shape, cross-run agreement).
