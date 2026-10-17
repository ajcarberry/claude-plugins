# Evals — Measuring Quality and Consistency

Headless runs of the real commands against a fixture product, scored by scripts.
The unit tests (`../tests/`) cover the deterministic layer; these cover the
judgment layer.

## Fixture

- `fixtures/app/` — `tasklite`, a tiny Python CLI with planted defects: an
  off-by-one in CSV export, UTC-vs-local due dates, a non-atomic save that can
  empty the data file, a `KeyError` on unknown ids.
- `fixtures/github-issues.json` (7 issues) and `fixtures/slack-export.json`
  (13 messages) — duplicates in different words across platforms, a Slack post
  that links a GitHub issue, a question that is really a bug report, one message
  holding two issues, `+1` thread replies, a closed-and-fixed issue, chatter, a
  how-to question, and a bot post.
- `fixtures/expected.json` — the 8 true tickets, which refs belong to each,
  acceptable tiers, spice floors, and the 4 refs that must be ignored.

## Running

```bash
evals/run.sh setup /tmp/ft-e1          # fresh git project + config + empty queue
evals/run.sh intake /tmp/ft-e1         # → score_intake.py
evals/run.sh investigate /tmp/ft-e1    # (--no-pr) → ft.py list
evals/run.sh report /tmp/ft-e1         # (--dry-run) → score_reports.py
evals/run.sh recheck /tmp/ft-e1        # (--all) → ft.py list
evals/score_reports.py /tmp/ft-e1 /tmp/ft-e2 …   # cross-run agreement
```

`EVAL_MODEL` sets the orchestrator model (default opus). A full pipeline over the
fixture costs about $8 and takes about 30 minutes.

## Metrics

| Metric | Script | Target |
|---|---|---|
| coverage — every item tracked or ignored | score_intake | 1.0 |
| noise ignored, none tracked | score_intake | 4/4 |
| dedup precision / recall (pairwise over refs) | score_intake | 1.0 / 1.0 |
| split message → two tickets | score_intake | true |
| type accuracy | score_intake | 8/8 |
| idempotence — rerun creates nothing | log count | 0 new |
| tier within the acceptable set | score_reports | 8/8 |
| spice floor (data loss ≥ Hot) | score_reports | 1/1 |
| lint errors / warnings on stored reports | score_reports | 0 / 0 |
| rendered message shape | score_reports | no deviations |
| cross-run tier / spice agreement | score_reports | as high as the cases allow |

## Results log

Runs on 2026-10-17. Each iteration changed skills/rubrics/scripts, then re-ran.

| Run | Change under test | Intake | Tiers ok | Lint | Notes |
|---|---|---|---|---|---|
| i1 | first draft | GitHub only | — | — | fixture bug (Slack dated 2025); orchestrator correctly refused out-of-window items |
| i2, i3 | fixed fixture | perfect ×2; rerun of i2 created 0 | 6/8, 8/8 | 0 / 0 | agreement 5/8: sync scoped down to dodge the high list; JSON shape treated as an open product question; `claim --help` claimed the queue |
| i3 recheck | upstream close + new comment + new untracked issue | — | — | — | fixed ticket resolved (merge commit cited), new info → reinvestigate, untracked issue not tracked, rest confirmed; unchanged-data control: all confirmed |
| i4, i5 | rubric v2 (tier as asked; which open questions count; reach by flow); titles name capabilities | perfect ×2; identical F1 title | 8/8, 8/8 | 0 / 0 | sync and JSON now agree everywhere; unreproduced perf report reframed as a feature (medium vs high) |
| i6 | rubric v3 (cause unknown → high covers perf/"faster" requests; rare-trigger reach); no-PR rendering | perfect | 8/8 | 0 / 0 | perf → high; CSV bug spice consistent; "Do:" lines uniform |

Remaining variance is in the genuinely borderline case: the atomic-save fix
(B3) lands low or medium depending on whether the investigator judges the file
mode/symlink change as user-visible. Both are acceptable, and medium is the
rubric's tiebreak.

Bugs the evals and the tests found in the deterministic layer: `--help` acting
as a real command, `git -C <dir> push` bypassing the PR gate, `state.sh`
resolving the git dir from the caller's cwd, outbox run-id collisions,
reinvestigated tickets reusing stale report prose.

Not covered here: live Slack/GitHub APIs (the fixture uses exports), PR creation
against a real remote (`--no-pr`), and Slack delivery (`--dry-run`). The hook and
`ft.py` paths for those are unit-tested.
