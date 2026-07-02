---
description: Reentry and touchdown — merge, deploy, observe, run landing checks against the live system, then clean up
allowed-tools: Bash, Read, Write, Grep, Glob, Task, Skill, AskUserQuestion
---

# Land — Merge, Deploy & Verify

The mission closes here: merged, deployed, and **verified in reality** — not at "PR
created". Runs only after `/orbit` reports GO.

## Step 0: Go-for-Landing Gate

Verify, fresh (never from memory):

1. **CI green** — `gh run list --branch <branch> --limit 1 --json status,conclusion`
2. **Reviews resolved** — `gh pr view --json reviewDecision,mergeable`
3. **Landing queue known** — collect `[landing]` V-checks from the PR body and/or
   the flight plan's Verification section

Any NO → report exactly what's blocking and point back to `/orbit`. **STOP.**
No PR at all? Suggest `/orbit` first — or, for direct-merge workflows, confirm with
the user before proceeding without one.

## Step 1: Rollback Path & Backup

Before anything irreversible:

- **State the rollback path** in one or two lines: how this deploy reverts
  (`git revert` + redeploy, previous job version, `terraform apply` of prior state).
  No known rollback path = NO-GO; say so.
- **Backup-before-destructive** (`data-safety`): if the deploy includes migrations
  or touches persistent state, snapshot/dump first and **verify the backup exists
  and is non-empty**. Get typed confirmation ("destroy") from the user for
  irreversible steps.

## Step 2: Merge

Confirm base branch (mission brief `parent:`, fallback `main`), then ask (header
"Merge"): "Squash merge" / "Merge commit" / "Cancel". Execute via
`gh pr merge --squash|--merge --delete-branch=false`. Verify the merge landed
(`git log <base> --oneline -1` after `git fetch`).

## Step 3: Deploy

Determine the deploy method, in priority order:

1. A domain-pack landing-mechanics skill, if one is enabled (it knows the stack)
2. The project's documented deploy command (CLAUDE.md, Makefile, README)
3. CI/CD auto-deploy on merge — if so, just watch it (`gh run list` on the base branch)

If none is identifiable, say so and ask the user for the deploy command rather than
guessing. Run the deploy; watch it complete using condition-based waiting (poll the
scheduler/health endpoint — no blind sleeps).

## Step 4: Observe & Validate

1. **Observe** — watch the deployed system's health signals until stable: health
   endpoints, scheduler status, error logs, dashboards. Poll conditions, bounded
   timeouts.
2. **Execute the landing queue** — run every `[landing]` V-check against the live
   system, including the negative ones (kill the container, watch the alert fire).
   Record each result with its evidence (`verification-before-completion`).

**Unstable or a landing check fails → ABORT TO ORBIT:**
execute the rollback path from Step 1, verify the system is back to healthy, and
report what failed with its evidence. The branch/PR state is preserved for another
orbit iteration. **STOP** after a rollback — diagnosis (`systematic-debugging`)
comes before any re-landing attempt.

## Step 5: Cleanup

Only after touchdown is verified:

- Update the PR: check off completed landing checks with a results comment
  (`gh pr comment`).
- Worktree cleanup (only if in a worktree — compare `git rev-parse --show-toplevel`
  with the main worktree path): ask "Clean up worktree" / "Keep". Remove via
  `git -C <main-repo> worktree remove <path>`; warn that the current directory
  disappears. Offer `--force` only if normal removal fails.
- Delete the remote branch if the user wants (`git push origin --delete <branch>`).

## Step 6: Touchdown Report

    Touchdown confirmed!
      Merged:   <PR url> → <base>
      Deployed: <method / job / environment>
      Landing checks: <N>/<N> passed  (<list any with evidence one-liners>)
      Rollback: <not needed | executed — see report above>
      Worktree: <cleaned up | kept>

    Mission complete. Lessons worth keeping? Note them for the skills —
    /debrief will automate this later.

## Error Handling

| Scenario | Action |
|----------|--------|
| CI failing / reviews unresolved | NO-GO — point to /orbit, stop |
| No rollback path identifiable | NO-GO — surface it, stop |
| Backup can't be verified | Stop before deploy; never proceed on "probably" |
| Merge conflict | Stop; suggest rebasing in orbit |
| Deploy method unknown | Ask the user; never guess a deploy command |
| Deploy hangs | Bounded waits; on timeout, report state and ask |
| Landing check fails | Abort-to-orbit: rollback, verify healthy, report, stop |
| `gh` unavailable | Manual merge instructions; landing checks still run |
