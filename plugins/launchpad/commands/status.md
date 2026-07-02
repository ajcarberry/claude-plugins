---
description: Mission re-entry — where the mission stands, what's next, what's blocked. Read-only.
allowed-tools: Bash, Read, Grep, Glob
---

# Status — Mission Re-Entry

Read-only situation report for missions spanning days or sessions. Makes no changes.

## Gather (skip anything missing — absence is information)

1. `.claude/mission-brief.md` — task, branch, date, parent
2. Latest `.claude/specs/*.md` — approved design
3. `.claude/flight-plan.md` — phases, steps, V-checks
4. `.claude/flight-log.md` — last completed step, blockers
5. Git: `git branch --show-current`, `git status --porcelain`,
   `git log <parent>..HEAD --oneline` (fall back to `main` if no parent)
6. GitHub (non-fatal if `gh` missing): `gh pr status --json url,state,reviewDecision`,
   `gh run list --branch <branch> --limit 1 --json status,conclusion`

## Report

    ## Mission Status

    **Mission:** <task, or "no mission in progress in this directory">
    **Branch:** <branch> (<N> commits ahead of <parent>; <clean | M uncommitted changes>)
    **Phase:** <e.g. "Implementing — Phase 2 of 3" from flight plan + log; or "planning" / "in orbit">

    **Done:**     <compact list from flight log / commit log>
    **Next:**     <the next unfinished step or the next command in the sequence>
    **Blocked:**  <blockers from the flight log, failing CI, unresolved reviews — or "nothing">

    **PR:** <url + state + review decision | "not created">   **CI:** <passing | failing | running | unknown>

Close with exactly one suggested next action ("Next: `/launch` to continue Phase 2" /
"Next: `/orbit` — the branch has no PR yet"). If there is no mission state at all,
say so and list the entry points: `/mission`, `/stage`, `/hop`.

## Rules

- **Read-only.** No writes, no fetches that mutate state, no fixes — even for
  problems found. Report them.
- Stale mission (brief > 3 days old, branch already merged)? Say so plainly —
  "this mission may already be complete" — and suggest checking `git log`.
