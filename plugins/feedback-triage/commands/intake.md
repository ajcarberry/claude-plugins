---
description: Phase 1 — ingest bug reports and feature requests from GitHub issues and Slack into the deduplicated ticket queue, linking every place each issue was raised
allowed-tools: Bash, Read, Write, Glob, Grep, Task, Skill, ToolSearch
argument-hint: "[source ids | export file paths] [--since YYYY-MM-DD]"
---

# Intake — Every Report, Tracked Once

`ft` = `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/ft.py` (JSON out; exit 1 = fix the
input, exit 2 = a rule refused — change approach, don't retry blind). You are the
only queue writer; queue files are never edited by hand.

## 1. Preflight

- `ft paths` — no index → tell the user to run `/feedback-triage:setup`; **STOP**.
- `${CLAUDE_PLUGIN_ROOT}/scripts/state.sh pull`.
- Sources = `$ARGUMENTS` (`github:owner/repo`, `slack:C0123`, or export paths)
  else `ft config` sources. A source with `export` is read from that file.
- Run dir: `<runs>/intake-<UTC yyyymmddThhmmss>/`.

## 2. Read (fan out)

Per source: `ft watermark get <source>`. Window `from` = watermark −
`intake.overlap_hours` (overlap is safe: the ledger is idempotent); no watermark →
`first_run: true`, `from` = now − `intake.lookback_days`; `--since` overrides.
Dispatch one `source-reader` per source in parallel with source, window, `out` =
`<run dir>/candidates-<slug>.json`, export path if any.

## 3. Deterministic pass

Check every top-level item read is in `items`; if not, redispatch that reader once
naming the gap. Then per item, **oldest `raised_at` first**:
- `question`/`noise` → `ft ignore --ref <url> --reason "<class>: <reason>"`.
- else `ft upsert --dry-run --json <item>`:
  `exists` (refreshes +1s/state when run for real — run it) · `ignored` → done ·
  `would-create` / `links-tracked` → step 4.

## 4. Judgment — same issue?

For each remaining item, compare it with `ft search <key symptom words>` hits, any
`links-tracked` ids, items already handled this run, and — since search is only
word matching — the one-line titles from `ft list --status
new,investigating,investigated,reported,needs-reinvestigation,blocked --format brief`.

- **Duplicate** → same user problem **and** same symptom or same want. Different
  words, channels, reporters are expected. Upsert with `duplicate_of` = the
  original's `source.ref` if it has one, else its **URL** (never a guessed FT id), and a one-sentence
  `duplicate_reason` naming the shared symptom.
- **Distinct** → same area, different symptom or want ("export is slow" vs
  "export drops a row"); a feature that would fix a bug is distinct from the bug.
  A message that links a tracked issue but describes something else → upsert with
  `distinct: true`.
- **Unsure** → distinct, with "Possibly related: <id>" in the summary. Merging
  later is easy; splitting is not.

Wrong link afterwards → `ft move-source <ref> --to <id> --reason …`. Two tracked
tickets that are one issue → `ft merge <newer> <older> --reason …`.

## 5. Watermarks, validate, persist

Per source with `complete: true`: `ft watermark set <source> <high_water>` (never
for partial reads). `ft validate` must be ok → `state.sh save "intake: <summary>"`.

```
Intake <run>: <N> read → <new> new · <linked> linked · <tracked> already tracked · <ignored> not feedback
  Sources: <ok> (partial/failed: <list or none>)   Multi-raised: <FT-… ×n>
  Next: /feedback-triage:investigate
```

Unreadable source → skip it, keep its watermark, name it. `ft validate` fails →
stop before saving and report the problems.
