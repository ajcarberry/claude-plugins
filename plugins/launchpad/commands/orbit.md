---
description: Get the branch into review and keep it healthy — validate, self-review, open the PR; on re-entry, respond to review feedback
argument-hint: "[PR title]"
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, Task, Skill, AskUserQuestion
---

# Orbit — Validate, Review, PR, Iterate

Two modes, detected by PR state. Orbit is re-enterable: run it again whenever
feedback arrives. Merging is `/land`'s job — orbit never merges.

## Workflow

### Step 0: Preflight

`git branch --show-current` — refuse on `main`:
> You're on `main` — orbit is for feature branches. `/stage` first.

Gather: base branch (`parent:` from `.claude/mission/brief.md`, fallback `main`),
stakes (`stakes:` from the brief). Detect mode: `gh pr view` succeeds → **Mode B
(respond)**; otherwise → **Mode A (first orbit)**.

## Mode A — First Orbit: Validate → Self-Review → PR

### A1: Uncommitted Changes

`git status --porcelain`. If dirty, invoke `Skill: commit:commit-conventions` and
commit (fallback: commit matching recent `git log` style). Still dirty after (user
declined) → ask: proceed without committing / retry / cancel.

### A2: Validate

Invoke `Skill: launchpad:validation` and run it to completion. It ends with the
stamp written clean — the push gate depends on it. Failures are blocking: root
cause first (`systematic-debugging`), no pushing around a red check.

### A3: Self-Review

Invoke `Skill: launchpad:self-review` (depth follows stakes). Blocking findings →
fix, then **re-run A2** (fixes dirty the stamp). Nits → carry to the PR body.

### A4: Push

`git push -u origin <branch>`. On failure ask: retry / stop.

### A5: CI Watch

`gh run list --branch <branch> --limit 1 --json status,conclusion,name --jq '.[0]'`
(skip with a note if `gh` is unavailable).
- **Running** → ask: wait (poll every 15s, up to 3 times, then re-ask) / proceed
  without CI / stop.
- **Failed** → read `gh run view --log-failed`, fix at root cause, commit,
  re-validate, push again. That's orbit working, not an error.
- **Passed** → proceed.

### A6: Create PR

Verify commits ahead of base (`git log <base>..HEAD --oneline`); none → warn, **STOP**.

**Title:** `$ARGUMENTS` → brief `task:` → humanized branch name.
**Body:**

```markdown
## Summary
(2–5 bullets from the spec/brief and commit log)

## Validation
- <each check run in A2, with result>
- Self-review: <clean | N blocking fixed>

## Notes
- Nit: <carried nits, if any>
```

Show title + body, ask: create / edit / skip / cancel. Create via
`gh pr create --title ... --body-file <tmp> --base <base>`; show the URL. No `gh` →
print the compare URL from `git remote get-url origin`.

## Mode B — Respond to Feedback

### B1: Fetch

`gh pr view --json reviews,comments,reviewDecision` plus
`gh api repos/{owner}/{repo}/pulls/<n>/comments` for inline threads. Nothing new →
report current state (reviews, CI) and stop.

### B2: Process Each Item

Feedback is a claim, not an order: **verify against the codebase first**. Where the
reviewer is right, fix it — check first, then fix (`test-driven-development`).
Where they're wrong or it's out of scope, draft a reply with reasons; post replies
only with the user's OK. Never implement a suggestion you haven't verified.

### B3: Re-validate and Push

Any fixes → re-run `Skill: launchpad:validation` (stamp must be clean), commit,
push, repeat the CI watch (A5).

## Final Report (both modes) + STOP

```
Orbit status: <GO | NO-GO> for landing
  CI:         <passing | failing | unknown>
  Reviews:    <approved | changes requested | none yet>
  Validation: <clean @ timestamp>
  PR:         <url>

GO — run /land to merge and clean up.
NO-GO — <the specific blockers>.
```

Append the orbit events to `.claude/mission/log.md`. **STOP — no merging.**

## Error Handling

| Scenario | Action |
|----------|--------|
| On `main` | Refuse |
| Validation fails | Blocking — root-cause fix, never push around it |
| CI fails | Read log, fix, re-validate, push (normal orbit work) |
| No commits ahead of base | Warn, stop before PR |
| `gh` unavailable | Compare URL; skip CI/review automation with a note |
| User cancels | Stop gracefully; orbit is safely re-enterable |
