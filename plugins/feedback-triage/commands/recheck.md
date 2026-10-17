---
description: Out-of-band loop — fact-check, validate, and update ONLY already-tracked tickets against their sources (built for /loop, Routines, or CI; asks no questions)
allowed-tools: Bash, Read, Write, Glob, Grep, Task, Skill, ToolSearch
argument-hint: "[ticket ids] [--all]"
---

# Recheck — Keep Tracked Tickets True

Load `Skill: feedback-triage:ticket-verification` and `Skill: feedback-triage:ticket-queue`.
`ft` below means `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/ft.py`.

This command is safe to run unattended: it **never asks questions, never creates
tickets or sources, never posts, never opens PRs**. It only updates tickets that
already exist, through `ft recheck-apply`.

## Step 1: Select

- `state.sh pull` (`${CLAUDE_PLUGIN_ROOT}/scripts/state.sh`).
- `$ARGUMENTS` ids → those tickets. `--all` → `ft due recheck --min-age-hours 0`.
  Otherwise `ft due recheck` (oldest-checked first, capped by
  `recheck.max_per_run`).
- Nothing due → print `Recheck: nothing due.` and **STOP** (no save, no noise —
  this is the common case on a loop).

## Step 2: Verify (fan out)

Run id `recheck-<UTC yyyymmddThhmmss>`. Dispatch one `ticket-verifier` per ticket
(parallel, cap `investigate.max_parallel`) with: ticket path, investigation path
if any, base branch, export paths of any configured sources that use `export`, `out` = `<runs>/<run-id>/verdict-<ID>.json`.

## Step 3: Apply

For each verdict file: `ft recheck-apply --json <file>`.
- Exit 1 (bad verdict) → redispatch that verifier once with the error text.
- Exit 2 (rule refused, e.g. a patch outside the allowed fields) → do not retry;
  log it with `ft log recheck-refused --id <ID> --reason "<stderr>"`.
- Untracked feedback the verifier mentioned → list it in the summary for the next
  intake. Do not upsert it.

## Step 4: Validate, persist, summarise

`ft validate` (must be ok) → `state.sh save "recheck: <n> checked"`.

```
Recheck <run-id>: <n> checked
  confirmed <n> · corrected <n> · resolved <n> · reinvestigate <n> · invalid <n>
  Changes: <FT-… field → new value; one line each, max 10>
  Seen but untracked (for intake): <urls or none>
```

Tickets moved to `needs-reinvestigation` are picked up by the next
`/feedback-triage:investigate`; resolved ones are announced in the next report's
digest. Scheduling options: [scheduling.md](../references/scheduling.md).
