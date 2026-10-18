# feedback-triage

Feedback in, engineering-ready reports out. The plugin finds bug reports and
feature requests in GitHub issues and Slack, tracks each one **once** in a
persistent queue, researches each with a dedicated subagent, and produces a
standalone, tracker-ready report per issue (Markdown for Jira, Linear, GitHub, …).
The aim: the engineering team reads the report, not the raw issues, and fixes that
are ready to merge arrive with the report.

Self-contained: it depends on no other plugin.

## Pipeline

```
           ┌──────────── /recheck (loop: /loop, Routine, CI) ─────────────┐
           ▼                                                              │
GitHub ─┐                                                                 │
        ├─▶ /intake ─▶ queue ─▶ /investigate ─▶ /report ─▶ your tracker   │
Slack ──┘   dedup +    (internal  per ticket:      one Markdown             │
            link all    ids)      high → findings  report per issue ───────┘
            sources               medium → options (+ proposed fix when
                                  low → reviewed fix  one is ready to merge)
/sweep = recheck → intake → investigate → report        /queue = read-only view
```

| Command | Phase | Does |
|---|---|---|
| `/feedback-triage:setup` | — | sources, target tracker, persistence, tool check |
| `/feedback-triage:intake` | 1 | read sources since each watermark; track every bug/feature once; link every place it was raised; record non-feedback as ignored |
| `/feedback-triage:recheck` | loop | fact-check **only tracked** tickets: still open? fixed upstream? new info? corrected fields? Never asks, never creates |
| `/feedback-triage:investigate` | 2 | one `bug-investigator` / `feature-analyst` per ticket; complexity-gated depth; an existing fix PR is tested and recommended instead of duplicated; low tier → `change-reviewer` → draft PR |
| `/feedback-triage:report` | 3 | `report-writer` prose → `ft.py lint` → `ft.py render` → one paste-ready Markdown ticket per issue |
| `/feedback-triage:sweep` | all | the full loop, no questions asked |
| `/feedback-triage:queue` | — | counts, ready fixes, most-raised, one ticket in full |

## Design

**Skills teach, scripts decide, hooks enforce.**

- **`scripts/ft.py`** (stdlib Python) is the only writer of the queue. It owns
  the dedup ledger (one source ref → one ticket; cross-links attach; judged
  duplicates attach; non-feedback is recorded, never dropped), monotonic
  per-source watermarks, the status state machine, the tier contracts (medium
  needs ≥ 2 options, low needs a branch and an approved review), the report
  prose lint, and the template renderer — which refuses to output any internal
  queue id.
- **Skills** hold judgment: what counts as feedback and what counts as a duplicate
  (`feedback-intake`), how to triage/repro/research/implement (`issue-investigation`
  + bug and feature playbooks), what a recheck may change (`ticket-verification`),
  how to write a report (`issue-reporting`), queue discipline (`ticket-queue`).
- **Agents** are tiered: sonnet reads sources (`source-reader`), verifies
  (`ticket-verifier`), and writes prose (`report-writer`); opus investigates
  (`bug-investigator`, `feature-analyst`) and reviews (`change-reviewer`).
  Subagents get file paths, never conversation history, and never write the
  queue — the orchestrator applies their result files through `ft.py`. Each actor
  loads only what it acts on (≈ 0.5–4k tokens of instructions).
- **Hooks** (`scripts/hook.py`, PreToolUse, deterministic file checks):
  no direct edits to queue files; no push/PR of a triage branch (`triage/*`) unless
  its ticket is low tier with an approved independent review, and only for the
  exact commit the reviewer approved (checked on the remote for PRs). Pushes or PR
  calls it cannot parse are blocked while triage branches exist. Escape hatch:
  `FT_SKIP_GATE=1`.

References: [queue-schema](references/queue-schema.md) ·
[complexity](references/complexity.md) · [scheduling](references/scheduling.md)

## A report

Every report is standalone Markdown: the first line is the ticket title, a
friendly intro says where it came from, and it reads in one of two ways — a
**researched report** (what's happening, why, what we know), or the same plus a
**proposed fix** that is ready to merge (a linked upstream PR we tested, or our
own independently reviewed change). Internal queue ids never appear.

A real one, from the evaluation run on `epicgames/lore` issue #241 (a researched
report; a fix-ready one adds **Proposed fix**, the review link, and any
**Before you merge** steps the project's CONTRIBUTING.md leaves to a person):

````markdown
# lore status --scan silently drops a delete/modify merge conflict

👋 Hi team! This report comes from our feedback triage, which keeps an eye on GitHub issues and Slack for bug reports and feature requests. People ran into this one, so we did the digging for you: what's happening, why, and what we know so far.

**Type:** Bug · **Status:** Researched: fix approaches outlined, needs a decision · **Reproduced:** Yes · **Reported by:** 1 person

## What's happening

A user merges a branch that edits a file the current branch deleted, then runs `lore status --scan`. The conflict disappears, the commit succeeds, and the other branch's edit vanishes with no prompt.

## What we found

- We reproduced it on main: merge, run `lore status --scan`, then commit; the commit drops the edit.
- `diff_filesystem_missing_nodes` discards a merge-staged file missing on disk, and `commit_child` skips the conflict check for staged deletes.
- Versions 0.9.0 to 0.10.1 fail; a path-limited scan or a deleted modify/modify file also skips the conflict check.
- Fix A (recommended) guards the scan discard and the commit; fix B skips merge-staged nodes in all scan walks.

## Sources

- GitHub epicgames/lore#241 (KasparsSverns): https://github.com/epicgames/lore/issues/241
````

Layout and wording live in `templates/report/report.md` and `theme.json`;
override per project in `.claude/feedback-triage/report/`. Markdown pastes cleanly
into Jira, Linear, GitHub, Shortcut, and most trackers; a team on Jira wiki markup
can override the template.

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

- **The PR gate is a guardrail, not a security boundary.** It stops an honest agent
  from shipping an unreviewed change by mistake, and fails closed on commands it
  can't parse, but any process with a shell can reach git another way (a renamed
  binary, a script file, the GitHub API with a token). Keep the real boundary
  server-side: triage PRs open as drafts, and use branch protection with required
  human review on the base branch.

- **One writer at a time per queue.** `state.persist: branch` merges by git
  rebase. Overlapping runners (e.g. a CI recheck during a laptop investigate) can
  conflict; `state.sh` then keeps the losing run on a pushed backup branch and
  stops, but recovering an interrupted *investigate* (claims, opened PRs) needs a
  human. Schedule phases so they don't overlap.
- Triage branches that are not opened as PRs stay on the runner that built them.
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
quality (tier accuracy, lint, report shape, cross-run agreement).
