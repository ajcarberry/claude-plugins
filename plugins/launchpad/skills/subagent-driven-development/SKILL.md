---
name: subagent-driven-development
description: Use when executing a large implementation plan (~10+ steps or multi-hour) with subagent orchestration — /launch heavyweight mode — or when coordinating fresh-context implementer agents across many steps of any big build, migration, or refactor.
---

# Subagent-Driven Development

Heavyweight execution engine: a fresh implementer subagent per step keeps every step
sharp regardless of how long the mission runs. The orchestrator (main session) never
implements — it dispatches, reviews, and keeps the ledger.

## Per-Step Loop

1. **Brief** — write the step brief to a file (`.claude/launch/S<N>-brief.md`): the
   step text from the flight plan, exact file paths, relevant spec/guardrail
   excerpts, and its checks. Subagents get **file paths, not pasted walls of text**.
2. **Dispatch implementer** — fresh subagent with
   [references/implementer-prompt.md](references/implementer-prompt.md), substituting
   the brief path. Answer its questions if it has any.
3. **Receive report** — implementer reports ≤15 lines with status
   **DONE / DONE_WITH_CONCERNS / BLOCKED / NEEDS_CONTEXT** and evidence (commands +
   results).
4. **Review** — dispatch a reviewer with
   [references/step-reviewer-prompt.md](references/step-reviewer-prompt.md): two
   separate verdicts — (a) **spec compliance** (does the work do what the step
   required, no more, no less) and (b) **code quality**. Blocking findings → dispatch
   a fix (may reuse the implementer prompt with the findings appended).
5. **Log** — append the step to `.claude/flight-log.md` with status and evidence.

## Rules

- **On BLOCKED, change something.** More context, a split step, a different approach
  — never redispatch the identical prompt. Three failures on one step = stop, surface.
- **Model tiering:** cheap model for mechanical single-file steps, standard for
  multi-file work, strongest model for architecture-heavy steps and the final
  whole-branch review. Turn count beats token price — don't make a cheap model take
  five turns over what a strong one does in one.
- **Orchestrator context is a budget.** Reports stay ≤15 lines; diffs and briefs
  travel as files; the flight log — not the conversation — is the source of truth.
- Implementer reports are claims, not evidence — the reviewer (or the orchestrator's
  own fresh command run) verifies (`verification-before-completion`).

## When NOT to Use

Plans under ~10 steps — lean `/launch` (main-session execution) is faster and cheaper.
Single independent problems — dispatch one agent directly, no orchestration layer.
