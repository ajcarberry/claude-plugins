---
name: verification-before-completion
description: Use when about to claim work is done, complete, fixed, passing, working, or deployed — before saying "done", "fixed", "should work now", marking a todo completed, reporting success to the user, or committing. Also use when relying on a subagent's report of success or on test results from earlier in the session.
---

# Flight Rule: Verification Before Completion

**Core principle:** Evidence before claims. Every time.

Announce when engaging: "Verifying before claiming completion."

## Iron Law

```
NO COMPLETION CLAIM WITHOUT FRESH VERIFICATION EVIDENCE IN THE SAME MESSAGE.
```

"Done", "fixed", "passing", "working", "deployed", a checked todo, a commit message
describing success — all of these are completion claims. Each one requires evidence
produced *after* the last change.

## Go/No-Go Gate

Run this gate before any completion claim:

1. **IDENTIFY** — the command or observation that would prove the claim
   (test run, build, curl, page load, `nomad job status`).
2. **RUN** — execute it fresh, after the final change. Output from before the last
   edit proves nothing.
3. **READ** — the full output, not just the exit banner. Count failures. Read stderr.
4. **VERIFY** — does the output actually demonstrate the specific claim? A green
   suite doesn't prove the *feature* works if no test covers it.
5. **CLAIM** — state what was run and what it showed. Then, and only then, claim.

No-Go at any step means: do not claim. Say what is unverified and verify it.

## Bug Fixes: the Red–Green–Red Proof

For any non-trivial bug fix, prove the fix is causal, not coincidental:

1. Check fails (or bug reproduces) before the fix — RED
2. Apply fix → check passes — GREEN
3. Revert the fix → check fails again — RED (proves the fix, not luck, made it pass)
4. Restore the fix → GREEN

Steps 3–4 can be skipped only when the fix is a single obvious change verified by a
targeted failing test written first (see `test-driven-development`).

## Failure Modes

| Rationalization | Reality |
|---|---|
| "It compiled, so it works" | Compilation proves syntax, not behavior. Run the check. |
| "The tests passed earlier" | Earlier was before your last edit. Fresh run or no claim. |
| "This change is trivial" | Trivial changes break builds daily. The check takes seconds. |
| "The subagent reported success" | Agent reports are claims, not evidence. Verify independently. |
| "I'll verify right after committing" | Order inverted. Evidence gates the commit, not the reverse. |
| "The logic is obviously correct" | Obviously-correct logic is where unverified bugs live. |
| "There's no way to test this here" | Then say exactly that — an explicit "unverified: needs X" beats a false "done". |

## Red Flags — STOP

- You are typing "done", "fixed", "should work", "this resolves", or checking a todo
  and there is no command output above it in the same message.
- Your claim contains "should", "probably", or "likely".
- You are citing output produced before the most recent edit.
- The verification exists but you didn't read past its first line.

## What Counts as Evidence

Fresh command output with exit status; a failing-then-passing check; an HTTP response
body; a screenshot of the rendered page (see `browser-verified-web-work` for web
changes); a log line you watched appear. Not evidence: memory, inference, another
agent's summary, or a passing run from before the last change.

## When NOT to Use

Pure discussion, planning, or research where no completion claim is being made. The
moment a claim forms, this rule applies.
