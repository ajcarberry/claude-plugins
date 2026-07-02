# Defense in Depth — After the Root Cause Is Fixed

Once a bug's origin is fixed and verified, ask: could one cheap guard make this
*class* of bug structurally impossible? Applied sparingly, this converts "fixed"
into "can't happen again".

## The Layers (pick the one that fits — rarely more than one)

1. **Entry validation** — reject bad input where it enters the system, with a message
   naming what was wrong. One validation at the boundary beats null checks scattered
   through every consumer.
2. **Invariant assertion** — if a state should be impossible, assert it where it
   would matter (`panic`/`raise` on violated invariants in internal code). Loud
   failure at the origin beats quiet corruption downstream.
3. **Environment guard** — if the bug came from a missing precondition (binary,
   migration, env var), add a startup check that fails fast with instructions.
4. **Instrumentation** — if the bug was invisible until late, add the one log line
   or metric that would have exposed it immediately.

## Rules

- **Root cause first.** Guards added *instead of* a root-cause fix are symptom
  patches — the thing this skill exists to prevent.
- **No impossible-scenario handling.** Guard against states that real inputs and
  real failures can produce; do not handle scenarios the type system or call graph
  already excludes. (Karpathy rule: no error handling for impossible scenarios.)
- **One guard, well placed** beats defensive code sprinkled everywhere. If you're
  adding the same check in three places, you're guarding the wrong layer.
