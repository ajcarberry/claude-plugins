---
name: systematic-debugging
description: Use when investigating a bug, error, test failure, crash, flaky behavior, or anything behaving unexpectedly — before proposing or applying any fix. Also use when a previous fix didn't work, the same error keeps returning, or you're about to add a retry, sleep, or defensive check to make a symptom go away.
---

# Flight Rule: Root Cause Before Remedy

**Core principle:** A fix without a root cause is a guess wearing a fix's clothes.

Announce when engaging: "Using systematic-debugging: tracing root cause before fixing."

## Iron Law

```
NO FIX WITHOUT A ROOT CAUSE YOU CAN STATE IN ONE SENTENCE.
```

If you cannot complete the sentence "This fails because ___, which originates at
___", you are not ready to change code.

## The Process

1. **REPRODUCE** — make the failure repeatable. Capture the exact error, input, and
   conditions. A bug you can't reproduce is a bug you can't verify fixed.
2. **TRACE** — follow the failure backward from where it *appears* to where it
   *originates*. Read the actual code path; find the first place a value or state
   goes wrong. See [references/root-cause-tracing.md](references/root-cause-tracing.md).
3. **CONFIRM** — prove the hypothesis with evidence before acting on it: a log line,
   a debugger value, a minimal experiment. One confirmed cause beats three plausible
   ones.
4. **FIX AT THE ORIGIN** — write the failing check first (`test-driven-development`),
   fix where the problem starts — not where it surfaces — and watch red turn green
   (`verification-before-completion`).

## The 3-Strikes Rule

```
THREE FAILED FIXES = STOP. The problem is your model of the system.
```

Do not attempt a fourth variation. Re-trace from scratch, question the architecture,
or surface what you know and ask. Repeating near-identical fixes is the definition of
guess-and-check.

## Failure Modes

| Rationalization | Reality |
|---|---|
| "Just add a null check where it crashes" | The crash site is the messenger. Why is the value null? |
| "A retry / sleep will fix the flakiness" | Timing hacks hide race conditions. Poll a real condition instead — see [condition-based-waiting](references/condition-based-waiting.md). |
| "It's probably X — let me try that" | Probably is a hypothesis. Confirm it before changing code. |
| "The bug must be in the library" | It's in your code until proven otherwise. Trace your side first. |
| "One more tweak will do it" | That's strike counting. After three, stop. |
| "No time for process — this is urgent" | Guess-and-check under pressure takes longer. Every time. |

## Red Flags — STOP

- Proposing a fix before reproducing the failure.
- The fix touches the line where the error *appears*, not where it originates.
- Adding defensive code without knowing why the bad state occurs.
- You are writing the second (or third) variation of the same fix.
- The words "just in case" appear in your reasoning.

## After the Fix

Once the root cause is fixed and verified, consider whether one cheap guard would
make this *class* of bug structurally impossible — see
[references/defense-in-depth.md](references/defense-in-depth.md). Apply sparingly:
no error handling for impossible scenarios.

## When NOT to Use

Expected failures during RED-phase TDD (the failing check is the point), or
first-time setup errors with a known documented cause. The moment a failure
surprises you, this rule applies.
