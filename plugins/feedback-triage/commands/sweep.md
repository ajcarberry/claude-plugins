---
description: Run the whole feedback-triage pipeline — recheck → intake → investigate → report — interactively or unattended (--yes) on a schedule
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, Task, Skill, ToolSearch, AskUserQuestion
argument-hint: "[--yes] [--skip recheck,intake,investigate,report]"
---

# Sweep — The Full Loop

Runs each phase command's workflow in order, as written in its own file. Each
phase pulls and saves state itself, so a failure in one phase leaves the queue
consistent and the next phase still runs.

1. **Recheck** — follow [recheck.md](recheck.md). Facts first: closes resolved
   tickets and flags changed ones before anything new is investigated.
2. **Intake** — follow [intake.md](intake.md) for every configured source.
3. **Investigate** — follow [investigate.md](investigate.md) with the default
   limits.
4. **Report** — follow [report.md](report.md). With `--yes`, pass `--yes`
   through (sends without asking); without it, the report step asks once.

`--skip` drops phases by name. `--yes` also means: never call AskUserQuestion —
where a phase would ask, take the safe default (skip the send, keep PRs as
drafts, skip unreadable sources) and say so in the summary.

## Summary

One block, the four phase summaries stacked, then:

```
Sweep complete · queue: <open> open · <new> new · <blocked> blocked
  Needs a human: <blocked ids, failed sources, skipped reports — or "nothing">
```

Unattended setup: [scheduling.md](../references/scheduling.md).
