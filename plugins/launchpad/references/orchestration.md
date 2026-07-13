# Orchestration — Work Packets, Model Tiering, Verification Asymmetry

How `/launch` puts an orchestrator and its subagents in the best position to
succeed. The orchestrator (main session) never implements — it dispatches, verifies,
and keeps the log.

## Work packets, not vibes

A packet is a self-contained brief. A subagent with a complete packet can't wander;
one told to "implement the auth part" will. `/mission-plan` decomposes the spec into
packets; `/launch` writes each to `.claude/mission/packets/P<N>.md` and dispatches
against it (subagents get **file paths, not pasted walls of text**).

```markdown
# P<N>: <goal in one sentence>

**Files in scope:** <exact paths — create or modify nothing outside them>
**Contracts:** <interfaces/types/signatures this packet must honor or expose>
**Spec slice:** <only the requirements this packet serves — not the whole spec>
**Done when:** <the observable check that proves it — command + expected result>
**Return:** ≤15 lines — status DONE | DONE_WITH_CONCERNS | BLOCKED | NEEDS_CONTEXT,
what changed, evidence (command + result), concerns if any.
**Tier:** haiku | sonnet | opus
```

Packets are ordered so contracts exist before their consumers: interfaces and
failing checks first (the TDD flight rule doing double duty) — subagents converge
faster with something to make pass.

## Model tiering

| Tier | Work |
|---|---|
| **Opus** (orchestrator) | spec decomposition, architecture packets, cross-packet integration, final review |
| **Sonnet** | scoped implementation packets |
| **Haiku** | mechanical packets: renames, fixtures, boilerplate, log parsing |

Turn count beats token price — don't make a cheap model take five turns over what a
strong one does in one. When unsure, tier up.

## The dispatch loop

1. **Dispatch** — fresh subagent per packet; prompt = the packet file path plus
   project context pointers (CLAUDE.md path, relevant source dirs). Never the
   conversation history.
2. **Receive** — the ≤15-line report. Reports are claims, not evidence.
3. **Verify** — asymmetrically: a stronger model (or the orchestrator's own fresh
   command run) checks the work against the packet's done-check and contracts.
   Nothing self-certifies.
4. **Log** — append packet, status, and evidence to `.claude/mission/log.md`.

**On BLOCKED, change something** — more context, a split packet, a different
approach. Never redispatch the identical prompt. Three failures on one packet →
stop and surface to the user.

## Context hygiene

The orchestrator's context is a budget. Reports stay ≤15 lines; briefs and diffs
travel as files; the mission log — not the conversation — is the source of truth.
If the orchestrator is reading whole files a subagent already read, something is
mis-briefed.

## When NOT to orchestrate

Fewer than ~5 packets, or single independent problems → implement in the main
session under the flight rules (express `/launch`). The orchestration layer has to
earn its overhead.
