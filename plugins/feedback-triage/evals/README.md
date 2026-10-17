# Evals — Measuring Quality and Consistency

Headless runs of the real commands against a fixture product, scored by scripts.
The unit tests (`../tests/`) cover the deterministic layer; these cover the
judgment layer.

## Scenarios

**`realworld/`** — the real `python-humanize/humanize` repository at HEAD plus a
snapshot of 10 of its real issues (bodies paraphrased by the fetch tool; titles,
metadata, comments, and linked PRs exact) and a small Slack export whose messages
are synthetic but describe behaviour verified on the real code. Real traps: most
bugs already have fix PRs in flight (some competing, some broken), #400 is closed
as a duplicate of a PR that is already merged, and the intword tickets (#356,
#227) touch the same code. Set `HUMANIZE=<clone>` for `run.sh setup`.

**`fixtures/`** — synthetic, fully known truth:

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
SCENARIO=realworld evals/run.sh setup /tmp/ft-e1   # or fixtures (default)
evals/run.sh intake /tmp/ft-e1         # → score_intake.py
evals/run.sh investigate /tmp/ft-e1    # (--no-pr) → ft.py list
evals/run.sh report /tmp/ft-e1         # → score_reports.py
evals/analyze.py /tmp/ft-e1-<phase>-<ts>.jsonl    # cost, subagents, plugin files read
evals/context_cost.py                  # static instruction tokens per actor
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

### Round 1 — synthetic fixture only (6 runs)

Intake reached perfect scores from the second run; tier accuracy went 6/8 → 8/8
across three rubric revisions (scope-down loophole, which open questions count,
"cause unknown → high" for performance reports, reach by affected flow).

### Round 2 — real-world scenario, adversarial review + fact-check every iteration (max 3)

Each iteration: change → full headless run on real humanize issues (+ fixture as a
regression guard) → a fresh-context reviewer attacks the plugin → an independent
fact-checker re-runs every claim in the reports against the real code and PRs.

| | Baseline | Iteration 1 | Iteration 2 | Iteration 3 |
|---|---|---|---|---|
| Intake dedup precision / recall (real) | 0.67 / 0.67 | 1.0 / 1.0 | 1.0 / 1.0 | 1.0 / 1.0 |
| Report claims checked / wrong | 47 / 3 | ~54 / 6 | 60 / 2 (+1 imprecise) | 68 / 1 |
| Misleading tickets | 2 | 1 + 1 partly | 1 + 1 mildly | 0 on facts; 1 CTA (links a PR the text says to close) |
| Duplicate fix branches built over open upstream PRs | 4 (+3 recommended) | 0 | 0 | 0 |
| Wrong PR attributions | 2 hidden | 3 | 2 (+1 missed) | 0 |
| Tickets dropped from the report | 0 | 0 | 1 (capacity, unannounced) | 0 |
| Reviewer: high-severity defects found | — | 7 | 3 | 1 |
| Static instruction tokens (all actors) | 24.3k | 13.4k | 13.5k | 13.8k |
| Cost: intake / investigate / report (real) | $0.95 / $10.71 / $1.19 | $0.80 / $9.23 / $1.62 | $0.71 / $9.37 / $1.39 | $0.73 / $9.16 / $1.38 |

What moved the numbers: `duplicate_of` by the original's URL instead of a
predicted ticket id (dedup); testing linked upstream PRs before building
(duplicate work); `existing_pr` restricted to PRs the issue links, and lint
refusing a recommendation that names a different PR than the rendered link (PR
attribution); `fixed_on_base` plus a deeper fetch (merged fixes hidden by shallow
clones); digest backlog line (silent drops).

Remaining, by design decision rather than iteration: concurrent runners sharing
the git-branch queue can still conflict in ways that lose a run's work (see the
plugin README, "Known limits").

Not covered: live Slack/GitHub APIs (sandbox blocks unattached repos' API; the
reader's REST path is untested live), opening real PRs (`--no-pr`).
