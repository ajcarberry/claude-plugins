---
name: test-driven-development
description: Use when about to write or change code — implementing a feature, fixing a bug, refactoring — before the first line of implementation. Also use when tempted to write code first and test later, to skip tests because a change is small, or when no test harness exists and you need to decide what "verified" means for a config, infra, or content change.
---

# Flight Rule: Failing Check First

**Core principle:** Define the check that fails before and passes after — *then* change
anything. Where a test harness exists for the code you're changing, that check is a
failing test. Where none exists (config, infra, content), it is a concrete observable
command — a curl, a page load, a `nomad job status`, a rendered preview.

Announce when engaging: "Using test-driven-development: writing the failing check first."

## Iron Law

```
NO PRODUCTION CHANGE WITHOUT A CHECK THAT FAILS FIRST.
```

Code written before its check must be deleted — not kept "as reference", not
"adapted". Delete means delete. Rewriting it after the check exists takes minutes and
produces code you know is covered.

## The Cycle

1. **RED** — write one minimal check for one behavior. Run it. **Watch it fail, for
   the right reason.** If it passes immediately, you are checking existing behavior —
   start over. If you didn't watch it fail, you don't know it checks anything.
2. **GREEN** — write the minimum change that makes it pass. Run it. Confirm green.
3. **REGRESSION** — run the surrounding suite (or the adjacent checks). Nothing else
   broke.
4. **REFACTOR** — clean up under green: naming, duplication, extraction. Re-run.

Repeat per behavior. One behavior per check.

## No Harness? The Check Still Comes First

| Change | Failing check, defined before the change |
|---|---|
| Caddy/nginx route | `curl -s -o /dev/null -w '%{http_code}' <url>` → expect 404 now, 200 after |
| Nomad/k8s job | `nomad job status <job>` / health endpoint → absent now, healthy after |
| CSS/UI change | Page load + screenshot showing the wrong state now, right state after — verified in a real browser |
| CLI flag | Run the command → errors or lacks the flag now, works after |
| Docs/content | Rendered preview showing the gap now, the content after |

Writing the check first is what makes "done" observable instead of asserted — it is
the same evidence `verification-before-completion` will demand at the end.

## Exceptions — Require Explicit User Approval

Throwaway spikes (deleted afterward, never merged), generated code, and pure
mechanical renames with tool support. Name the exception aloud and get a yes before
proceeding without a check.

## Failure Modes

| Rationalization | Reality |
|---|---|
| "Too simple to test" | Simple code breaks daily; the check takes seconds to write. |
| "I'll add tests after it works" | Tests written after pass by construction — they verify nothing. |
| "The test would just duplicate the code" | Then the behavior is trivial to check — write the trivial check. |
| "Deleting hours of work is wasteful" | Sunk cost. Unverified code is a liability, not an asset. |
| "No harness exists, so TDD doesn't apply" | The Iron Law says *check*, not *test*. Define the observable command. |
| "It passed on the first run — great" | It never failed, so it proves nothing. Break the code, watch it fail, restore. |

## Red Flags — STOP

- Implementation code exists and no check for it has ever failed.
- You cannot explain *why* the check failed on RED.
- One check asserts several unrelated behaviors.
- The check mocks the very thing it's supposed to verify.
- You're about to say "I'll verify manually later."

## Writing Good Tests

When the check is a real test, design it well — see
[references/test-design.md](references/test-design.md) (three-layer strategy,
black-box default, table-driven structure, naming, assertion strategy, anti-patterns)
and [references/go.md](references/go.md) for Go-specific patterns.

## When NOT to Use

Reading, research, planning, or pure prose edits with no behavior to check — though
the rendered-preview rule above still applies to content that ships.
