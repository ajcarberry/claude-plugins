# Root-Cause Tracing

Errors surface far from their origin. Trace backward until you find the *first* place
the data or state went wrong — that is where the fix belongs.

## The Method

1. Start at the failure: exact error, stack trace, failing assertion.
2. Identify the immediate bad value or state ("`user` is nil", "port is 0",
   "response is HTML not JSON").
3. Ask: where did this value come from? Read that code. Is it wrong *there*?
4. Repeat step 3 until you reach the first point where correct input became incorrect
   output. That's the origin.
5. Fix at the origin. Everything downstream heals.

## Rules

- **Never fix mid-chain.** Patching an intermediate frame (converting the nil,
  defaulting the port) leaves the origin producing garbage for every other consumer.
- **Read code, don't skim it.** Most wrong hypotheses come from assuming what a
  function does instead of reading it.
- **Instrument when reading isn't enough.** A temporary log line at each hop of the
  chain locates the first bad hop in one run. Remove instrumentation after.
- **Diff against last-known-good.** If it worked before, `git log`/`git diff` the
  path between then and now — the origin is usually in the delta.

## Signs You Haven't Found the Origin Yet

- The fix requires handling a "weird" value rather than preventing it.
- You can't explain how the bad value was created, only where it was noticed.
- Fixing here would leave another caller of the same producer still broken.
