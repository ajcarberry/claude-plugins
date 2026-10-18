---
description: Phase 2 — fan out one subagent per tracked ticket to triage and research it; complexity decides the depth (high → findings, medium → options, low → reviewed change request), and an existing fix PR is reviewed instead of duplicated
allowed-tools: Bash, Read, Write, Glob, Grep, Task, Skill, ToolSearch
argument-hint: "[ticket ids] [--limit N] [--no-pr]"
---

# Investigate — One Ticket, One Investigator, Tier-Gated Depth

`ft` = `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/ft.py`; `wt` =
`${CLAUDE_PLUGIN_ROOT}/scripts/worktree.sh`. Exit 1 = fix the input; exit 2 = a rule
refused. Subagents get paths, never conversation history, and never write the queue.

## 1. Claim

`state.sh pull` (`${CLAUDE_PLUGIN_ROOT}/scripts/state.sh`), then `ft claim --limit
<--limit or investigate.max_per_run>` (`--ids` from `$ARGUMENTS`). Nothing claimed →
`Investigate: queue is clear.` **STOP** — unless `ft due review` lists low tickets
whose review never finished (a crashed run): resume those at step 4, or, if
`wt path <ID>` finds no worktree, `ft review <ID> --verdict changes --notes
"worktree lost" --downgrade`. Then `state.sh save "investigate: claimed <ids>"` at
once, so other runners see the claims. Run dir `<runs>/investigate-<UTC ts>/`.

## 2. Dispatch (waves of at most `investigate.max_parallel`)

Dispatch each wave as foreground subagent calls (`run_in_background: false`) sent
in one message, so they run in parallel and the turn waits for them — a headless
run that ends its turn kills background subagents. Tickets listed in each other's `related` go one after another (later ones can read
earlier findings). Per ticket:
1. `wt create <ID> <slug of title>` → worktree (runs `investigate.setup` if set).
2. `bug-investigator` (bug) or `feature-analyst` (feature) with: ticket path,
   worktree, `investigation` = `<investigations>/<ID>.md`, `result` =
   `<run dir>/result-<ID>.json`, project root, `related` ids (from the claim), and
   `prior_attempt` if the ticket has one.

## 3. Apply

- `BLOCKED` / no result → `ft release <ID> --reason "<concern>"` (2nd failure →
  `blocked`; add `--infra` when the environment failed — disk, network, killed —
  not the ticket); `wt discard <ID>`.
- `DONE` → `ft investigated --json <result>`. Exit 1 → redispatch once with the
  error text; still refused → release.
- No branch built (high, medium, or an existing PR covers it) → `wt discard <ID>`.
- Branch built (low) → step 4.

## 4. Low tier — independent review, then change request

1. `change-reviewer` (foreground) with ticket, investigation, worktree, branch, base.
2. `approved` → `ft review <ID> --verdict approved --notes "<one line>" --commit
   $(git -C <worktree> rev-parse HEAD)` (the gate only lets that exact commit out).
   `changes` → record it, redispatch the investigator with `revise` = the notes,
   review again. Second `changes` (or the revise is BLOCKED) → `ft review <ID>
   --verdict changes --notes … --downgrade` and `wt remove <ID>` (branch kept). The
   ticket returns as `needs-reinvestigation`; the next claim must classify it
   medium with the attempt as one option.
3. Approved, `investigate.open_prs` true, no `--no-pr`, and no `handoff` step saying
   the project needs a person to write or sign the PR (human-written description,
   sign-off on every commit): `git -C <worktree> push -u
   origin <branch>`; open the PR (`gh pr create` or GitHub MCP) against base, draft
   if `investigate.draft_prs`, title = the ticket title (no internal id), body from
   [pr-body.md](../templates/pr-body.md); `ft pr <ID> --url <url>`; `wt remove <ID>`.
   Otherwise `wt remove <ID>` (branch stays local; the report names the handoff). The hook refuses push/PR unless
   the ticket is low with an approved review — fix the state, never bypass.

## 5. Validate, persist, summarise

`ft validate` → `state.sh save "investigate: <n> done"`.

```
Investigate <run>: <n> tickets — high <n> · medium <n> · low <n> · existing PR <n>
  Repro: <n> reproduced · <n> not   PRs opened: <urls or none>   Blocked: <ids or none>
  Next: /feedback-triage:report
```
