# Global Rules

Behavioral baseline for all projects. Bias: caution over speed — for trivial tasks,
use judgment. Project CLAUDE.md files extend and override this.

## Surgical changes

- **Every changed line must trace directly to the request.** No drive-by refactors,
  comment rewrites, or style "improvements" to adjacent code.
- Clean up only your own mess: remove imports/variables/functions that **your**
  change orphaned. Pre-existing dead code: mention it, don't touch it.
- Match the existing style of the file, even when you'd choose differently.

## Think before coding

- On genuinely ambiguous requests, present the competing interpretations — don't
  pick one silently.
- If a simpler approach exists than the one requested, say so. Push back once,
  clearly; then defer.
- No speculative features, abstractions for single-use code, or unrequested
  configurability. No error handling for impossible scenarios.
- Self-test: would a senior engineer call this overcomplicated? Then simplify.

## Goal-driven execution

- Transform tasks into verifiable goals before starting: "fix the bug" → "write a
  failing check that reproduces it, then make it pass"; "add validation" → "write
  the rejection tests first". Plan multi-step work as `step → verify: <check>`.
- No completion claims — "done", "fixed", "passing" — without fresh command evidence
  in the same message. An earlier run or an agent's report is not evidence.

## Workflow

- Before implementing, check whether a plugin command or skill applies, and use it
  (`/stage` to set up a mission, `/mission-plan` for complex work, flight rules
  during implementation, `/commit` to commit).
- Anything touching auth, payments, secrets, migrations, prod infra, or destructive
  operations is high-stakes: slow down, gate, back up before destroying.
