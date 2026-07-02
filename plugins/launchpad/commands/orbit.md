---
description: Push, create the PR, watch CI, and iterate on review feedback until go-for-landing
argument-hint: "[PR title]"
allowed-tools: Bash, Read, Write, Grep, Glob, Task, Skill, AskUserQuestion
---

# Orbit — PR, CI & Review Iteration

Ascent complete, now circling: get the branch into review and keep it healthy until
**go-for-landing**. The worktree stays alive throughout — orbit is where iteration
happens. Merging, deploying, and cleanup are `/land`'s job.

## Workflow

### Step 0: Preflight

`git branch --show-current` — refuse on `main`:
> You're on `main` — orbit is for feature branches. `/stage` or `/hop` first.

Gather: worktree path (`git rev-parse --show-toplevel`), main repo path
(`git worktree list --porcelain | head -1 | sed 's/worktree //'`), base branch
(mission brief `parent:`, fallback `main`).

### Step 1: Uncommitted Changes

`git status --porcelain`. If dirty, invoke `Skill: launchpad:commit`. If still dirty
after (user cancelled), ask: "Proceed without committing" / "Retry commit" / "Cancel".

### Step 2: Orbit V-Checks

If `.claude/flight-plan.md` has a Verification section, run every **[orbit]**-tagged
check that `/launch` hasn't already logged as passing in the flight log (re-run any
that are cheap). Failures are blocking: fix at root cause (`systematic-debugging`)
before pushing. Log results in the flight log.

### Step 3: Docs Check

Invoke `Skill: docs` — let it run autonomously; nothing to update is normal. If it
made changes, invoke `Skill: launchpad:commit` again.

### Step 4: Push

`git push -u origin <branch>`. On failure ask: "Retry push" / "Stop".

### Step 5: CI Watch

`gh run list --branch <branch> --limit 1 --json status,conclusion,name --jq '.[0]'`
(skip with a note if `gh` is unavailable).

- **Running** → ask (header "CI"): "Wait for CI" (poll every 15s, up to 3 times, then
  re-ask) / "Proceed without CI" / "Stop".
- **Failed** → read the failure log (`gh run view --log-failed`), fix at root cause,
  commit, push again. This is orbit working as intended, not an error.
- **Passed** → proceed silently.

### Step 6: Create PR

Skip if a PR already exists (`gh pr view` succeeds) — go to Step 7.

Verify commits ahead of base (`git log <base>..HEAD --oneline`); if none, warn and
**STOP**.

**Title** (priority): `$ARGUMENTS` → mission brief `task:` → humanized branch name.

**Body:**

```markdown
## Summary
(2-5 bullets from the commit log, spec, and flight plan objective)

## Verification — orbit checks (run pre-merge)
- [x] V1 [orbit]: `go test ./...` — PASS
- [x] V3 [orbit]: plan validates against staging config

## Landing checks — deferred to deploy (/land's work queue)
- [ ] V2 [landing]: kill the prometheus container → Slack alert within 3m
- [ ] V5 [landing]: dashboard renders with live data
```

Every `[landing]` check from the flight plan MUST appear in the landing-checks
section — this is `/land`'s work queue; nothing gets silently dropped. No flight
plan? Derive a checklist from the diff instead.

Show title + body, then ask (header "PR"): "Create PR" / "Edit" / "Skip PR" /
"Cancel". Create via `gh pr create --title ... --body-file ... --base <base>`
(write body to a temp file first). Show the URL. If `gh` is missing, print the
compare URL derived from `git remote get-url origin`.

### Step 7: Review Iteration

Check for feedback: `gh pr view --json reviews,comments,reviewDecision`.

For each piece of reviewer feedback: process per `receiving-code-review` — verify
against the codebase before implementing, push back with reasons where warranted,
fix agreed items with checks first, commit, push. Repeat CI watch after each push.

If there's no feedback yet, that's fine — orbit can be re-entered anytime
(`/orbit` again, or `/status` to check state).

### Step 8: Go/No-Go for Landing

Report the gate:

    Orbit status: <GO | NO-GO> for landing
      CI:        <passing | failing | unknown>
      Reviews:   <approved | changes requested | none yet>
      Orbit V-checks: <N>/<N> passing
      Landing queue:  <M> checks deferred to /land
      PR:        <url>

    GO — run /land to merge, deploy, and verify.
    NO-GO — <the specific blockers>.

**STOP.** Do not merge — that's `/land`, and it needs your go.

## Error Handling

| Scenario | Action |
|----------|--------|
| On `main` | Refuse with message |
| Orbit V-check fails | Blocking — root-cause fix before push |
| CI fails | Read log, fix, push again (normal orbit work) |
| No commits ahead of base | Warn, stop before PR |
| `gh` unavailable | Manual compare URL, skip CI/review automation |
| PR already exists | Skip creation, continue to review iteration |
| User cancels | Stop gracefully; orbit is safely re-enterable |
