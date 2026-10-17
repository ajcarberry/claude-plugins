---
name: issue-investigation
description: Use when triaging or researching a tracked feedback ticket (FT-NNNN) — reproducing a reported bug, analysing a feature request's requirements, classifying complexity (low/medium/high), proposing fix or implementation options, or implementing a low-complexity fix on an ft/ branch.
---

# Issue Investigation — Triage, Then Go Exactly as Far as the Tier Allows

One ticket, one investigator, one outcome the engineering team can act on without
re-reading the original reports. Work in stages; complexity decides where you
stop.

```
1 TRIAGE ─▶ classify tier ─▶ high: write up, STOP
                            ─▶ medium: 2 RESEARCH options, STOP
                            ─▶ low:    2 RESEARCH + 3 IMPLEMENT on a branch, STOP
```

## 1. Triage (every ticket)

Read the ticket file and **every** source URL in it, including comments and
thread replies — later replies often hold the repro steps or the workaround.

- **Bug** → follow [bug-playbook.md](references/bug-playbook.md): reconstruct
  the incident (version, environment, timeline, recent commits in the area), then
  attempt a reproduction. The repro is the centre of a bug investigation.
- **Feature** → follow [feature-playbook.md](references/feature-playbook.md):
  find the underlying job the user is trying to do, write requirements and
  acceptance criteria, and check what already exists.
- **Wrong type?** A "feature request" for documented behaviour that is broken is a
  bug; a "bug" that is working as designed is a feature request. Correct it
  (`type` in the result) and investigate as the corrected type.

Then classify per [complexity.md](../../references/complexity.md) — rules in
order, first match wins, between low and medium choose medium. Score `impact` and
`reach` per [spiciness.md](../../references/spiciness.md) from evidence.

## 2. Research (medium and low)

- **Bug:** find the root cause — the line or decision that makes it fail, not the
  symptom. Trace from the repro to the cause. If you can't state the cause in one
  sentence, it is not found yet.
- **Feature:** find where it would live, what it would touch, and what it must not
  break.
- Write **at least two real options** (doing nothing or a workaround counts only
  if it is a real choice), each with: approach, files/areas touched, effort (S/M/L),
  risk, and what it does not solve. Recommend one and say why in one sentence.

## 3. Implement (low only)

- Work in the **ticket worktree** you were given (branch `ft/<ID>-<slug>`), for
  repro and changes alike. Never edit the main checkout. The orchestrator
  discards the worktree for medium/high tickets, so anything worth keeping (the
  repro test, its output) goes in the investigation file.
- Bug: the repro becomes a failing test **first**; watch it fail; fix the root
  cause; watch it pass; run the project's full test/lint command (CLAUDE.md →
  Makefile → package.json → language default).
- Feature: a test per acceptance criterion, then the smallest implementation
  that passes them.
- Commit on the branch with a message naming the ticket. **Do not push or open a
  PR** — the orchestrator does that after an independent review, and the hook
  enforces it.
- If the change outgrows the low rules (more files, a design choice, a high-list
  area), stop: re-classify as medium, keep the attempt as an option.

## Time-box

Stop digging when the next hour would not change the tier or the recommendation.
"Not reproduced after: X, Y, Z" is a valid finding. An honest gap beats a guess.

## Output — two files

1. **Investigation file** at the path you were given, from the template
   (`templates/investigation-bug.md` or `-feature.md`). Every claim cites its
   evidence: a command and its output, a file:line, a URL.
2. **Result JSON** at the path you were given — the orchestrator applies it with
   `ft.py investigated`, which refuses incomplete results:

```json
{"id": "FT-0007", "status": "DONE",
 "complexity": {"tier": "low|medium|high", "rationale": "<one sentence naming the deciding rule>"},
 "impact": 0, "reach": 0, "bump": 0, "bump_reason": null,
 "repro": "reproduced|partial|not-reproduced|not-attempted|n/a",
 "root_cause": "<one sentence, or null>", "options_count": 2,
 "investigation_file": "<path>", "type": "<only if corrected>",
 "branch": "<low only>", "worktree": "<low only>", "commit": "<low only>",
 "concerns": "<anything the reviewer or reader must know, or null>"}
```

`status: "BLOCKED"` (with `concerns` saying what is missing) when you could not
do the triage at all — no access, sources deleted, project won't build.
