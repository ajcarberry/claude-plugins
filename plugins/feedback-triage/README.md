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
  its ticket is low tier with an approved independent review. Escape hatch:
  `FT_SKIP_GATE=1`.

References: [queue-schema](references/queue-schema.md) ·
[complexity](references/complexity.md) · [scheduling](references/scheduling.md)

## A report

Every report is standalone Markdown: the first line is the ticket title, a
friendly intro says where it came from, and it reads in one of two ways — a
**researched report** (what's happening, why, what we know), or the same plus a
**proposed fix** that is ready to merge (a linked upstream PR we tested, or our
own independently reviewed change). Internal queue ids never appear.

A real one, from the evaluation run on `python-humanize/humanize` issue #431:

````markdown
# intcomma shows large and tiny floats in scientific notation

👋 Hi team! This report comes from our feedback triage, which keeps an eye on GitHub issues and Slack for bug reports and feature requests. People ran into this one, we did the digging, and there's a fix we're confident is ready to merge.

**Type:** Bug · **Status:** Fix ready: an open upstream PR fixes it (we tested it) · **Reproduced:** Yes · **Reported by:** 3 people

## What's happening

Users who pass floats of 1e16 or more, or below 1e-4, to `intcomma` see '1e+16' with no commas. A revenue dashboard and a billing page show this.

## What we found

- We reproduced it on main: `intcomma(1e16)` returns '1e+16' and `intcomma(1e-05)` returns '1e-05'.
- `intcomma` formats floats with `f"{value:,}"`, which uses exponent notation at 1e16 or more, or below 1e-4.
- Open PR #449 also fixes it but duplicates PR #432, and it adds about 1.1 µs to every float call.
- Both PRs leave the string input '1e20' unchanged, which is outside the reported float case.

## Proposed fix

PR #432 adds a branch in `intcomma` that expands exponent floats with `Decimal` before grouping. It fixes every reported case, passes the full suite on main (856 passed), and changes no output in 300,140 fuzzed floats. Check CI and review state before merging, because we could not read them.

Review it here: https://github.com/python-humanize/humanize/pull/432

## Open question

Do you want to close PR #449 as a duplicate after you merge PR #432?

## Sources

- GitHub python-humanize/humanize#431 (TheNetherWatcher): https://github.com/python-humanize/humanize/issues/431
- Slack #app-feedback (nadia): https://acme.slack.com/archives/C0APPDEV/p1791100000000100
- Related PR (open): https://github.com/python-humanize/humanize/pull/449
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
