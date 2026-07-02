---
name: receiving-code-review
description: Use when processing code review feedback — PR comments, reviewer findings, or critique of your work — before implementing any suggested change or replying to the reviewer. Also use when tempted to agree quickly and implement everything asked without checking it.
---

# Receiving Code Review

Technical correctness over social comfort. Feedback is data to verify, not orders to
execute — and not an occasion for performance.

## Process — per feedback item

1. **UNDERSTAND** — restate the concern in your own words. If any item is unclear,
   stop and ask about *all* unclear items before implementing *any* of them.
2. **VERIFY** — check the claim against the actual codebase. Does the bug exist? Is
   the suggested pattern already used elsewhere? Would the change break something the
   reviewer can't see?
3. **EVALUATE** — right for this codebase and this task's scope? A reviewer
   suggestion that adds unrequested "professional" features gets the YAGNI test:
   grep for actual usage/need before adding.
4. **RESPOND** — technical acknowledgment or reasoned pushback. Then implement
   agreed items one at a time, each with its check (`test-driven-development`).

## Rules

- **No performative agreement.** "You're absolutely right!" is banned. Actions speak
  — verify, then fix or push back.
- **Pushback is legitimate** when: the change breaks existing behavior, the reviewer
  lacks context you have, it's a YAGNI violation, or it's technically wrong. State
  the reason in one or two sentences with evidence.
- **When your pushback was wrong:** "Verified — you're correct, my understanding was
  wrong. Fixing." No extended apology.
- Batch-implementing every item unexamined is as much a failure as ignoring them.

## When NOT to Use

Purely mechanical feedback (typos, formatting the linter agrees with) — just fix it.
