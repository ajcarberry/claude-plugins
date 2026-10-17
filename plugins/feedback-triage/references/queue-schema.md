# Queue Schema — State, Tickets, Transitions, `ft.py`

One state directory holds the queue. `scripts/ft.py` is the only writer of queue
files; the PreToolUse hook blocks direct edits to `queue/` and `index.json`.

```
<state.dir>/                 # default .feedback-triage/ (persisted per state.persist)
├── index.json               # the ledger: next_id, refs → ticket, ignored refs, watermarks
├── queue/FT-0001.json       # one ticket per file
├── investigations/FT-0001.md  # phase-2 findings (written by investigators)
├── runs/<run-id>/           # per-run scratch: candidates, verdicts, results (not persisted)
├── reports/outbox/<run>/    # rendered Slack messages awaiting delivery + manifest.json
├── reports/sent/<run>/      # delivered runs, moved here by `ft.py sent`
└── log.jsonl                # append-only event log
```

Config: `.claude/feedback-triage.json` in the project (created by `ft.py init`;
defaults in `ft.py` `DEFAULT_CONFIG`). Every key is optional.

## The ledger guarantees

- **One source, one ticket.** Every source ref (`github:owner/repo#N`,
  `slack:CHANNEL/TS`) maps to exactly one ticket. `upsert` of a known ref is a
  no-op returning the existing id. URLs and short refs normalise to the same key.
- **Cross-links attach, not duplicate.** A candidate whose text links to a tracked
  source attaches to that ticket as a `mention`.
- **Judged duplicates attach.** `duplicate_of` on a candidate attaches it as a
  `duplicate` source. Two tracked tickets found to be the same → `ft.py merge`.
- **Nothing silently dropped.** Non-feedback is recorded with `ft.py ignore` and a
  reason, so every source item read is either tracked or explained.
- **Watermarks only move forward**, and only after a source was read completely.

## Ticket fields

| Field | Set by | Notes |
|---|---|---|
| `id`, `created_at`, `updated_at`, `history[]` | ft.py | never hand-set |
| `type` | intake (investigate may correct) | `bug` \| `feature` |
| `title` | intake (recheck may correct) | ≤ 90 chars, the user problem, neutral |
| `summary` | intake (recheck/investigate may correct) | ≤ 600 chars, facts only |
| `sources[]` | intake | `ref, kind, url, author, raised_at, excerpt (≤400, verbatim), relation (original\|duplicate\|mention), plus_ones[], channel_name, state` |
| `labels`, `component`, `severity`, `environment` | intake, recheck | free metadata; `environment` = version/OS/browser/plan |
| `complexity` | investigate | `{tier: low\|medium\|high, rationale}` — [complexity.md](complexity.md) |
| `spiciness` | ft.py from investigator factors | `{factors{impact,reach,momentum,readiness}, bump, score, level}` — [spiciness.md](spiciness.md) |
| `investigation` | investigate | `file, repro, root_cause, branch, worktree, commit, review, pr_url, attempts` |
| `verification` | recheck | `last_checked_at, verdict, notes, evidence[], fixed_by, checks` |
| `report` | report | `headline, what, findings[], recommendation, ask` — linted |
| `reported` | ft.py sent | `at, hash, permalink, ts, count` |

## Statuses

```
new ──claim──▶ investigating ──investigated──▶ investigated ──sent──▶ reported
 ▲                 │  └─release (2nd fail)──▶ blocked                    │
 └──release────────┘                                                    │
needs-reinvestigation ◀──recheck: material change──────────────────────┘
closed: resolved (upstream fixed/closed) · duplicate (merged) · invalid (not feedback)
```

`resolved` can reopen to `needs-reinvestigation`. `duplicate` and `invalid` are
terminal. Illegal transitions exit 2.

## `ft.py` commands

Run as `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/ft.py <cmd>`. JSON in/out; `--json`
takes a file path, `-` (stdin), or an inline string. Exit 1 = bad input, 2 = a rule
refused it.

| Command | Phase | Does |
|---|---|---|
| `init`, `paths`, `config` | setup | create state + config; print resolved paths/config |
| `upsert --json C [--dry-run]` | intake | track one candidate → `created` \| `exists` \| `linked` \| `ignored` |
| `link ID --json SRC [--relation duplicate\|mention]` | intake | attach a source to a ticket |
| `ignore --ref R --reason T` | intake | record a read item as not-feedback |
| `merge DUP INTO --reason T` | intake/recheck | fold one tracked ticket into another |
| `search WORDS…` | intake | token-overlap candidates for semantic dedup |
| `watermark get\|set SOURCE [VALUE]` | intake | per-source read position |
| `claim [--limit N] [--ids A,B]` | investigate | atomically take tickets → `investigating` |
| `release ID --reason T [--blocked]` | investigate | give back; 2nd failure → `blocked` |
| `investigated --json RESULT` | investigate | apply an investigator result (validates tier contract) |
| `review ID --verdict approved\|changes [--downgrade]` | investigate | record the change-reviewer verdict |
| `pr ID --url U` / `gate-pr --branch B` | investigate | record / check a change request |
| `due report-writing\|report\|recheck` | report/recheck | what needs work now |
| `report-set ID --json R` / `lint --json R` | report | lint + store report prose |
| `render [--ids …]` / `sent RUN --file F --permalink P --ts T` | report | template → outbox; record delivery |
| `recheck-apply --json VERDICT` | recheck | apply a verifier verdict to an existing ticket |
| `get`, `list`, `stats`, `validate`, `spice`, `log` | any | read, integrity check, manual rescore |
