---
description: Out-of-band loop — fact-check, validate, and update ONLY already-tracked tickets against their sources (built for /loop, Routines, or CI; asks no questions)
allowed-tools: Bash, Read, Write, Glob, Grep, Task, Skill, ToolSearch
argument-hint: "[ticket ids] [--all]"
---

# Recheck — Keep Tracked Tickets True

`ft` = `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/ft.py`. Safe unattended: never asks,
never creates tickets or sources, never opens PRs. It changes tracked tickets
only, through `ft recheck-apply`.

1. `${CLAUDE_PLUGIN_ROOT}/scripts/state.sh pull`. Select: `$ARGUMENTS` ids;
   `--all` → `ft due recheck --min-age-hours 0`; else `ft due recheck`. Nothing due
   → print `Recheck: nothing due.` and **STOP** (no save).
2. Run dir `<runs>/recheck-<UTC ts>/`. Dispatch one `ticket-verifier` per ticket in
   parallel with: ticket path, investigation path if any, base branch, export
   paths of sources configured with `export`, `out` = `<run dir>/verdict-<ID>.json`.
3. `ft recheck-apply --json <file>` per verdict. Exit 1 → redispatch that verifier
   once with the error text. Exit 2 → don't retry; `ft log recheck-refused --id <ID>
   --reason "<stderr>"`. Untracked feedback a verifier mentions → list it for the
   next intake; never upsert it here.
4. `ft validate` → `state.sh save "recheck: <n> checked"`.

```
Recheck <run>: <n> checked — confirmed <n> · corrected <n> · resolved <n> · reinvestigate <n> · invalid <n>
  Changes: <FT-… field → value, ≤ 10 lines>   Seen but untracked: <urls or none>
```
