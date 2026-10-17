# Orchestration — Fan-Out, Tiering, Verification, Single Writer

Every phase command is an orchestrator. It dispatches subagents, checks what they
return, and is the **only** caller of `ft.py` write commands. Subagents read the
queue and write files under `runs/` and `investigations/`; they never mutate the
queue. This keeps every queue change on one lock, in one log, through one
validator.

## Agents and tiers

| Agent | Model | Phase | Writes |
|---|---|---|---|
| `source-reader` | sonnet | intake | `runs/<run>/candidates-<source>.json` |
| `ticket-verifier` | sonnet | recheck | `runs/<run>/verdict-<id>.json` |
| `bug-investigator` | opus | investigate | `investigations/<id>.md`, `runs/<run>/result-<id>.json`, ticket worktree |
| `feature-analyst` | opus | investigate | same as bug-investigator |
| `change-reviewer` | opus | investigate (low tier) | nothing — returns a verdict; the orchestrator records it with `ft review` |
| `report-writer` | sonnet | report | `runs/<run>/report-<id>.json` |

The orchestrator (main session) does dedup judgment, applies results, and decides
retries. Reading and writing prose is cheap; deciding what is true is not — the
strong model sits where judgment compounds (investigation, review).

## The dispatch packet

Subagents get **paths and parameters, never conversation history**:

```
Ticket: FT-0007 · bug · ticket file: <abs path to queue/FT-0007.json>
Write:  <abs path to investigations/FT-0007.md>, <abs path to runs/<run>/result-FT-0007.json>
Base:   main · Branch prefix: ft/ · Project: <project root> (read its CLAUDE.md)
Return: ≤ 15 lines — STATUS (DONE | BLOCKED), tier, one-line outcome, file paths.
```

## The loop

1. **Dispatch** in parallel, capped by `investigate.max_parallel` (default 4).
   Independent tickets only — two tickets touching the same code are dispatched
   one after the other.
2. **Receive** the ≤ 15-line report. A report is a claim, not evidence.
3. **Check** the written files exist and parse; `ft.py` validates the contract
   (a medium result without two options, a low result without a branch, a lint
   failure — each is refused with exit 1/2, and the refusal text goes back into
   the retry).
4. **Apply** with the matching `ft.py` command.
5. **On refusal or BLOCKED, change something** — add the refusal text, narrow the
   ask, or supply the missing context. Never redispatch an identical prompt.
   Second failure on one ticket → `ft.py release --blocked` and move on; one bad
   ticket never stalls the batch.

## Asymmetric verification

Nothing self-certifies. A low-tier change is checked by `change-reviewer` — a
fresh opus context that did not write it — before any branch is pushed; the PR
hook refuses otherwise. Report prose is checked by `ft.py lint`, which is
deterministic. Recheck verdicts must carry evidence (`ft.py` refuses verdicts
without it).

## Context hygiene

The orchestrator never reads whole source files a subagent already read. If it
needs to, the packet was mis-scoped. Keep per-ticket notes in the files, not in the
conversation — the files survive compaction and the next scheduled run.
