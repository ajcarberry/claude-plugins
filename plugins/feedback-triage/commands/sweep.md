---
description: Run the whole feedback-triage pipeline — recheck → intake → investigate → report — interactively or unattended on a schedule
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, Task, Skill, ToolSearch
argument-hint: "[--skip recheck,intake,investigate,report]"
---

# Sweep — The Full Loop

Follow, in order, [recheck.md](recheck.md) → [intake.md](intake.md) →
[investigate.md](investigate.md) → [report.md](report.md) (with `--unattended`
unless a human is watching this session), skipping phases named
in `--skip`. Each phase pulls and saves state itself, so one phase failing leaves
the queue consistent and the next still runs. Never ask questions: an unreadable
source is skipped and named; PRs stay drafts when `investigate.draft_prs` is set.

End with the four phase summaries stacked, then:

```
Sweep complete · queue: <open> open · <new> new · <blocked> blocked
  Needs a human: <blocked ids, failed sources, skipped reports — or "nothing">
```
