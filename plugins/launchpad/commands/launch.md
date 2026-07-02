---
description: Execute the flight plan — phase by phase with a durable flight log; subagent orchestration for big builds
argument-hint: "[--heavy | --solo]"
allowed-tools: Bash, Read, Write, Edit, Grep, Glob, Task, Skill, AskUserQuestion
---

# Launch — Execute the Flight Plan

Implementation phase of the mission. Requires a flight plan; maintains a durable
flight log so the mission survives crashes, compaction, and multi-day gaps.

## Preconditions

Read `.claude/flight-plan.md`. If missing:
> No flight plan. Run `/flight-plan` first — or use `/hop` if this is a small task.
**STOP.**

Read `.claude/flight-log.md` if it exists → **resume**: find the last DONE entry and
continue from the next step. Announce what's being resumed.

## Mode Selection

| Mode | When | Mechanics |
|------|------|-----------|
| **Lean** (default) | Most missions | Main session implements phase by phase |
| **Heavyweight** (`--heavy`, or offer it when the plan has ~10+ steps / clearly multi-hour scope) | Big builds where context rot is real | Fresh implementer subagent per step + per-step review — load `launchpad:subagent-driven-development` and follow it |
| **Solo** (`--solo`) | Constrained environments without subagents | Lean mode, no agent dispatches anywhere |

If the plan is large and the user didn't pass a flag, ask once (header "Mode"):
"Lean" / "Heavyweight" with a one-line cost note. Never silently pick heavyweight.

## The Flight Log

Create `.claude/flight-log.md` before the first step (or append to the existing one):

    ---
    mission: <from flight plan frontmatter>
    mode: <lean | heavyweight | solo>
    ---
    # Flight Log

    | Step | Status | Evidence / Notes |
    |------|--------|------------------|
    | S1   | DONE   | `go test ./auth` → PASS (14 tests) |
    | S2   | BLOCKED | missing CSI volume — needs user |

**Append after every step, before moving on.** Status vocabulary: DONE /
DONE_WITH_CONCERNS / BLOCKED / NEEDS_CONTEXT. Evidence is a real command + result,
per `verification-before-completion` — not "looks good".

## Work Loop (lean mode)

For each phase in the plan:

1. **Implement each step** — failing check first (`test-driven-development`), fix at
   root cause when things break (`systematic-debugging`), browser-verify web changes
   (`browser-verified-web-work`). Log each step on completion.
2. **Phase checkpoint** — run the phase's checkpoint and any **orbit-tagged V-checks**
   covering it. If a check fails: investigate root cause before proceeding (the
   plan's recovery hint says where to look).
3. **Commit the phase** — stage the phase's changes and invoke `Skill: launchpad:commit`.
4. Continue to the next phase.

**On BLOCKED:** log it, then change something before retrying — different approach,
more context, or ask the user. Never re-run the identical attempt. Three failed
attempts at one step = stop and surface it (3-strikes rule).

## Final Review

After all phases: run the full remaining orbit V-checks, then a **whole-branch
review** — one strong reviewer (strongest available model) over
`git diff <parent>..HEAD` with the flight plan and spec, per the peer-review skill's
standard tier (panel if the stakes rubric says high). Fix blocking findings, log them.

## Handoff

    Launch complete!
      Phases:   <N>/<N>    Steps: <M> (<X> DONE, <Y> with concerns)
      V-checks: <orbit checks run/passed; landing checks deferred to /land>
      Log:      .claude/flight-log.md
      Next:     /orbit — push, PR, and review iteration

**STOP.** Do not push or create a PR — that's `/orbit`.

## Error Handling

| Scenario | Action |
|----------|--------|
| No flight plan | Point to /flight-plan or /hop, stop |
| Flight log shows all steps DONE | Say the mission looks complete; suggest /orbit |
| Checkpoint fails repeatedly | 3-strikes: stop, log BLOCKED, surface to user |
| /commit finds blocking issues | Fix them in-place; they count as work in the current phase |
| Session dies mid-phase | Flight log makes resume safe — next /launch continues |
