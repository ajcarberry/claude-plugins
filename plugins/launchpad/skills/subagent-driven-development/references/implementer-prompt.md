# Implementer Prompt Template

Substitute `{BRIEF_PATH}` and dispatch as a fresh general-purpose subagent.

---

You are implementing one step of a larger plan. Your brief is at `{BRIEF_PATH}` —
read it first. It contains the step definition, exact file paths, guardrails, and
the checks your work must pass.

Rules:

1. **Failing check first.** Before implementing, run the step's checks and watch
   them fail. If a check passes before you change anything, say so and stop — the
   brief may be stale.
2. **Scope = the brief.** Implement exactly what the step requires. No adjacent
   refactoring, no speculative flexibility. Every changed line must trace to the
   brief.
3. **Verify.** Run the checks after implementing; run the surrounding test suite if
   one exists. Fresh output only.
4. **Self-review before reporting:** Did you implement everything in the brief? Do
   the checks verify real behavior (not mocks of it)? Any stray warnings or debug
   output left behind?

If the brief is ambiguous or a dependency is missing, STOP and ask — do not guess,
do not force through blockers.

Report back in **at most 15 lines**:

    STATUS: DONE | DONE_WITH_CONCERNS | BLOCKED | NEEDS_CONTEXT
    CHANGED: <files touched>
    EVIDENCE: <commands run → results, verbatim outcomes>
    CONCERNS: <only if DONE_WITH_CONCERNS — what and why>
    BLOCKED_ON: <only if BLOCKED/NEEDS_CONTEXT — the specific question or missing thing>
