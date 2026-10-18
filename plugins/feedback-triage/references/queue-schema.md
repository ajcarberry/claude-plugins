# Queue Schema — State, Config, Tickets, Statuses

`scripts/ft.py` is the only writer of queue files (`ft.py help` lists commands).

```
<state.dir>/                   # default .feedback-triage/, persisted per state.persist
├── index.json                 # ledger: next_id, refs → ticket, ignored refs (+reason), watermarks
├── queue/FT-0001.json         # one ticket per file
├── investigations/FT-0001.md  # phase-2 findings
├── runs/<run>/                # per-run scratch: candidates, verdicts, results (not persisted)
├── reports/outbox/<run>/      # one NN-<slug>.md per report + all-reports.md + manifest.json
├── reports/sent/<run>/        # runs recorded as posted
└── log.jsonl                  # append-only event log
<project>/.ft-worktrees/<id>/  # ticket worktrees (git-excluded)
```

## Config

`.claude/feedback-triage.json`; every key optional (defaults: `ft.py config`).

```json
{"state": {"dir": ".feedback-triage", "persist": "branch|commit|none",
           "branch": "feedback-triage/state", "remote": "origin"},
 "sources": {"github": [{"repo": "owner/name", "export": "<optional JSON export path>"}],
             "slack": [{"id": "C0123", "channel": "product-feedback", "export": "<optional>"}]},
 "intake": {"lookback_days": 14, "overlap_hours": 24},
 "investigate": {"max_parallel": 4, "max_per_run": 8, "base_branch": "main", "branch_prefix": "triage/",
                 "open_prs": true, "draft_prs": true, "setup": "<command run in each new worktree>"},
 "report": {"tracker": "Jira"},
 "recheck": {"max_per_run": 20, "min_age_hours": 12}}
```

Lower `investigate.max_parallel` to 1–2 where one build takes GBs of disk or all
cores (Rust, C++).

## Ledger guarantees

- One source ref (`github:owner/repo#N`, `slack:CHANNEL/TS`, `~N` for splits) → one
  ticket. Re-reading a tracked source refreshes its +1s, state, and linked PRs.
- A candidate that links a tracked source is refused until the orchestrator
  judges it: `duplicate_of` (the original's URL) or `distinct: true`.
- Non-feedback is recorded with a reason; a closed issue that reopens comes back.
- A new report on a resolved/invalid/blocked ticket reopens it
  (`needs-reinvestigation`).
- Watermarks only move forward, and only after a complete read.

## Ticket fields

| Field | Set by | Notes |
|---|---|---|
| `id`, `created_at`, `updated_at`, `history[]` | ft.py | |
| `type`, `title` (≤ 90), `summary` (≤ 600) | intake; recheck/investigate may correct | |
| `sources[]` | intake | `ref, url, author, raised_at, excerpt (≤ 400), relation (original\|duplicate\|mention), plus_ones, state, linked_prs, channel_name` |
| `labels`, `component`, `severity`, `environment` | intake, recheck | |
| `complexity` | investigate | `{tier, rationale}` — [complexity.md](complexity.md) |
| `investigation` | investigate | `file, repro, root_cause, existing_pr{url, verdict}, branch, review, pr_url, attempts` |
| `verification` | recheck | `last_checked_at, verdict, notes, evidence[], fixed_by` |
| `report`, `reported` | report | prose fields (linted); `at, hash, count` |

## Statuses

```
new → investigating → investigated → reported
        └→ blocked (2nd failure)      needs-reinvestigation ← recheck / new report
closed: resolved · duplicate (merged) · invalid
```
