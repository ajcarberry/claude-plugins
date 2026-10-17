---
description: Phase 2 — fan out one subagent per tracked ticket to triage and research it; complexity decides the depth (high → findings, medium → options, low → reviewed change request)
allowed-tools: Bash, Read, Write, Glob, Grep, Task, Skill, ToolSearch, AskUserQuestion
argument-hint: "[ticket ids] [--limit N] [--no-pr]"
---

# Investigate — One Ticket, One Investigator, Tier-Gated Depth

Load `Skill: feedback-triage:ticket-queue`. Investigators load
`issue-investigation` themselves. `ft` below means
`python3 ${CLAUDE_PLUGIN_ROOT}/scripts/ft.py`; `wt` means
`${CLAUDE_PLUGIN_ROOT}/scripts/worktree.sh`. Dispatch rules:
[orchestration.md](../references/orchestration.md). Tier rules:
[complexity.md](../references/complexity.md).

## Step 1: Claim

- `state.sh pull` (`${CLAUDE_PLUGIN_ROOT}/scripts/state.sh`).
- `ft claim --limit <--limit or investigate.max_per_run>` (`--ids` from
  `$ARGUMENTS` if given). Nothing claimed → `Investigate: queue is clear.` **STOP**.
- Run id `investigate-<UTC yyyymmddThhmmss>`; `ft paths` for absolute paths.

## Step 2: Dispatch (fan out)

Per claimed ticket, in parallel (cap `investigate.max_parallel`; tickets naming
the same component go one after another):
1. `wt create <ID> <slug of title>` → worktree path.
2. Dispatch `bug-investigator` (type bug) or `feature-analyst` (type feature)
   with: ticket path, worktree, `investigation` = `<investigations>/<ID>.md`,
   `result` = `<runs>/<run>/result-<ID>.json`, project root. Nothing else.

## Step 3: Apply each result

- `BLOCKED` or no result file → `ft release <ID> --reason "<concern>"` (2nd failure
  becomes `blocked`); `wt discard <ID>`.
- `DONE` → `ft investigated --json <result>`. Exit 1 names the missing contract
  piece (e.g. medium without 2 options) → redispatch once with that text as
  `revise`; still refused → release.
- Tier **high/medium** → `wt discard <ID>` (the investigation file holds the repro).
- Tier **low** → Step 4.

## Step 4: Low tier — independent review, then change request

1. Dispatch `change-reviewer` with ticket, investigation, worktree, branch, base.
2. `approved` → `ft review <ID> --verdict approved --notes "<one line>"`.
   `changes` (first time) → `ft review <ID> --verdict changes --notes …`, redispatch
   the investigator with `revise` = the notes, then review again. Second `changes`
   → `ft review <ID> --verdict changes --notes … --downgrade` (becomes medium; the
   attempt stays as an option) and `wt discard <ID>`.
3. Approved and `investigate.open_prs` true and no `--no-pr`:
   `git -C <worktree> push -u origin <branch>`, then open the PR (`gh pr create`
   or the GitHub MCP `create_pull_request`) against the base, draft if
   `investigate.draft_prs`, title `<ID>: <ticket title>`, body from
   [pr-body.md](../templates/pr-body.md) filled from the investigation. Then
   `ft pr <ID> --url <url>` and `wt remove <ID>`. The hook blocks the push/PR if
   the ticket is not low tier with an approved review — fix the state, never
   bypass.

## Step 5: Validate, persist, summarise

`ft validate` → `state.sh save "investigate: <n> done"`.

```
Investigate <run-id>: <n> tickets
  🧠 high <n> · 🧭 medium <n> · 🔧 low <n> (PRs: <urls>)
  Repro: <n> reproduced · <n> not reproduced   Blocked: <ids or none>
  Reclassified by review: <ids or none>

  Next: /feedback-triage:report
```

## Error Handling

| Scenario | Action |
|----------|--------|
| `wt create` fails (base missing, dirty) | Release the ticket with the error; continue the batch |
| Investigator times out | Treat as BLOCKED |
| Push/PR refused by hook | Read the reason; the ticket state is wrong — fix it through `ft`, never `FT_SKIP_GATE` |
| No GitHub write access | Keep the branch local, note "PR not opened: <reason>" in the summary; report still shows options |
