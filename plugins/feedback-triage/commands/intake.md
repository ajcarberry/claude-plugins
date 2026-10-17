---
description: Phase 1 — ingest bug reports and feature requests from GitHub issues and Slack into the deduplicated ticket queue, linking every place each issue was raised
allowed-tools: Bash, Read, Write, Glob, Grep, Task, Skill, ToolSearch, AskUserQuestion
argument-hint: "[source ids | export file paths] [--since YYYY-MM-DD]"
---

# Intake — Every Report, Tracked Once

Load `Skill: feedback-triage:feedback-intake` and `Skill: feedback-triage:ticket-queue`.
`ft` below means `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/ft.py`. You are the
orchestrator and the only queue writer —
[orchestration.md](../references/orchestration.md).

## Step 1: Preflight

- `ft paths`. No index → run `/feedback-triage:setup` first; **STOP**.
- `${CLAUDE_PLUGIN_ROOT}/scripts/state.sh pull`.
- Sources = `$ARGUMENTS` (source ids like `github:acme/app`, `slack:C0123`, or
  export file paths) else every source in `ft config`. A configured source with
  an `export` path is read from that file instead of the live API. None → say what was looked
  for, point to setup, **STOP**.
- Run id: `intake-<UTC yyyymmddThhmmss>`; scratch dir `<runs>/<run-id>/`.

## Step 2: Windows

Per source: `ft watermark get <source>`. Window start = watermark minus
`intake.overlap_hours` (re-reading the overlap is safe — the ledger makes it
idempotent); no watermark → now minus `intake.lookback_days`; `--since` overrides
both. Export files have no watermark.

## Step 3: Read (fan out)

Dispatch one `source-reader` agent per source, in parallel (cap
`investigate.max_parallel`), each with: source, channel name, window, `out` =
`<run dir>/candidates-<source-slug>.json`, and the export path if any. Wait for
all. A reader that fails or returns `PARTIAL` keeps its source's watermark where
it was — say so in the summary.

## Step 4: Deterministic pass

For each candidates file, check every top-level item read appears in `items` (`len(items) ≥ read_count`) (mismatch → redispatch
that reader once with the gap named). Then per item:
- `question` / `noise` → `ft ignore --ref <url> --reason "<class>: <reason>"`.
- `bug` / `feature` → `ft upsert --dry-run --json <item>`: `exists` / `ignored` →
  done; `would-link` → apply with `ft upsert --json <item>`; `would-create` →
  Step 5.

## Step 5: Judgment pass — same issue?

For every would-create item, run `ft search <title + key symptom words>` and
compare against the hits **and** the other would-create items in this run, per
the skill's duplicate rules. Process oldest `raised_at` first, so the earliest
report becomes the original. Then:
- Duplicate → `ft upsert --json` with `duplicate_of` and `duplicate_reason` added.
- Distinct → `ft upsert --json <item>` (add "Possibly related: FT-…" to the summary
  when unsure).
- Two existing tickets now clearly the same → `ft merge <newer> <older> --reason …`.

## Step 6: Advance watermarks

For each source whose reader returned `complete: true`:
`ft watermark set <source> <high_water>`. Never for partial reads.

## Step 7: Validate, persist, report

`ft validate` must be ok (fix before continuing). `ft log intake --run <id>`.
`state.sh save "intake: <n> new, <n> linked"`.

```
Intake <run-id>
  Sources:  <read ok> (partial/failed: <list or none>)
  Read:     <N items> → <new> new · <linked> linked to existing · <exists> already tracked · <ignored> not feedback
  Multi-raised: <FT-… (×n), …>
  Queue:    <total open> open (<new> awaiting investigation)

  Next: /feedback-triage:investigate
```

## Error Handling

| Scenario | Action |
|----------|--------|
| Source unreadable (auth, tool missing) | Skip it, keep its watermark, name it in the summary |
| `ft` refuses an item (exit 1) | Fix the field it names, retry once; else log and list it as unprocessed |
| `ft validate` fails | Stop before saving; report the problems |
| `state.sh save` cannot push | Report it; local queue is intact; next pull rebases |
