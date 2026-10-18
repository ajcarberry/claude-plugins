---
name: issue-investigation
description: Use when triaging or researching a tracked feedback ticket (FT-NNNN) — reproducing a reported bug, analysing a feature request's requirements, checking an existing fix PR, classifying complexity (low/medium/high), proposing fix or implementation options, or implementing a low-complexity fix on a triage branch.
---

# Issue Investigation — Triage, Then Go Exactly as Far as the Tier Allows

One ticket, one outcome an engineer can act on without reading the original
reports. Work in your **ticket worktree** only; the main checkout stays clean. If
the project needs setup (deps, codegen) and none ran, do it in the worktree first
— a missing dependency is not a "not reproduced".

## 1. Triage (every ticket)

1. Read the ticket and **every** source, comments included. Shallow clone? Fetch
   history first (`git fetch --depth 500 origin <base>`) — it hides merged fixes.
   Already fixed on the base branch (a merged PR or commit; the repro passes on
   base)? Write the investigation file and return `fixed_on_base: {"commit",
   "evidence"}` — the ticket closes; nothing else to do.
2. **Fix already in flight?** Only PRs the ticket's sources link (`linked_prs`) or
   whose comments name them — don't trawl the repo's PR list. For each: `git fetch origin pull/<N>/head:pr-<N>` and read its diff
   (`git diff <base>...pr-<N>`; shallow clone → `git show pr-<N>`). Run the repro
   or its tests against it. Verdict: `fixes` · `partial` · `wrong` · `unverified`
   (could not fetch). Merged already (`git merge-base --is-ancestor pr-<N>
   origin/<base>`)? Then it is `fixed_on_base`, not an open PR to review. Note the
   author if it is a bot or automation account.
   Not linked but clearly the same change? Add `unlinked_reason` inside
   `existing_pr`. `fixes` → never build a branch (`ft.py` refuses it); the
   recommendation becomes "review PR #N" plus anything it misses.
3. **Bug** → [bug-playbook.md](references/bug-playbook.md): reconstruct, reproduce,
   root-cause. **Feature** → [feature-playbook.md](references/feature-playbook.md):
   the job behind the request, requirements, what exists.
4. Wrong type? A "feature" for documented behaviour that is broken is a bug; a
   "bug" that works as designed is a feature. Correct it via `type`.
5. Classify per [complexity.md](../../references/complexity.md) (first matching
   rule wins).
6. **Related tickets** (given in your prompt): read their investigation files if
   they exist. Your recommendation must not contradict theirs — if the right
   answer conflicts, say so in `concerns` and name the ticket.
7. **`prior_attempt`** (a branch whose low-tier change failed review twice): the
   tier is at most medium; read the branch and the review notes, and make the
   attempt one of the options.

## 2. Research (medium, low)

Bug: the root cause as one sentence — "`fn` in `file:line` does X when Y; it should
Z". Feature: where it lives, what it touches, what it must not break. Write **≥ 2
real options** (approach · touches · effort S/M/L · risk · leaves out) and
recommend one in one sentence.

## 3. Implement (low, unless a PR already `fixes` it; `partial`/`unverified` still need our tested change)

Bug: the repro becomes a failing test first; watch it fail; fix the cause; watch
it pass; run the full suite. Feature: a test per acceptance criterion, then the
smallest implementation. Commit on the branch referencing the upstream issue ("Fixes #431"), never the internal FT id. **Never push or
open a PR** — the orchestrator does that after independent review. Outgrowing the
low rules mid-way → re-classify medium and keep the attempt as an option.

Time-box: stop when the next hour would not change the tier or the
recommendation. "Not reproduced after X, Y, Z" is a finding.

## Output

1. **Investigation file** from `templates/investigation-<type>.md`; every claim
   cites evidence (command + output, file:line, URL).
2. **Result JSON** (applied by `ft.py investigated`, which refuses incomplete
   results):

```json
{"id": "FT-0007", "status": "DONE",
 "complexity": {"tier": "low|medium|high", "rationale": "<one sentence naming the deciding rule>"},
 "repro": "reproduced|partial|not-reproduced|not-attempted|n/a",
 "root_cause": "<one sentence or null>", "options_count": 2,
 "existing_pr": {"url": "…", "verdict": "fixes|partial|wrong|unverified"},
 "investigation_file": "<path>", "type": "<only if corrected>",
 "branch": "<low, built>", "worktree": "<low, built>", "commit": "<low, built>",
 "concerns": "<or null>"}
```

Omit `existing_pr` when there is none. `status: "BLOCKED"` + `concerns` only if
triage itself was impossible (no access, sources gone, project won't build).
