---
description: Show the feedback-triage ticket queue — counts, the spiciest open tickets, multi-raised issues, or one ticket in full
allowed-tools: Bash, Read, Skill
argument-hint: "[FT-NNNN | status]"
---

# Queue — Read-Only View

`ft` below means `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/ft.py`. This command
never writes.

- **`FT-NNNN`** → `ft get <id>`. Show: title, type, status, tier + rationale,
  spice level + factors, every source (relation, link, author), repro, PR,
  last recheck verdict, and the investigation file path. Then the last 5
  history events.
- **a status** (e.g. `blocked`) → `ft list --status <status>`.
- **nothing** → `ft stats` and `ft list --status investigated,reported,new,needs-reinvestigation,blocked`:

```
Queue · <total> tickets (<open> open)
  new <n> · investigating <n> · investigated <n> · reported <n> · blocked <n> · reinvestigate <n>
  resolved <n> · duplicate <n> · invalid <n>   ignored refs: <n>
  Spiciest open:   <🌶️… FT-… title> (top 5)
  Raised most:     <FT-… ×n> (top 5)
  Watermarks:      <source → value>
```

Changes go through the phase commands, or `ft merge` / `ft spice` per
`Skill: feedback-triage:ticket-queue` — never by editing queue files.
