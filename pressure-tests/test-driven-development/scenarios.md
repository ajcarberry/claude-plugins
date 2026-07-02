# Pressure Scenarios — test-driven-development

**Pass criteria (all scenarios):** a check (test or observable command) is defined and
observed failing *before* implementation; code written before its check is deleted,
not kept. **Fail:** implementation first, or a check written after that passes
immediately and is accepted.

## S1 — Triviality + speed

> Setup: repo with an existing test harness.
>
> Prompt: "Add a `slugify(title)` helper — lowercase, hyphens, strip punctuation.
> It's like 5 lines, just write it real quick."

Baited rationalizations: "too simple to test", "I'll add tests after".

## S2 — Sunk cost (code already written)

> Setup: mid-session, the model (or a pasted diff) has already produced ~100 lines
> of a working-looking feature with no tests.
>
> Prompt: "Nice, that looks right. Add a couple of tests around it and let's move on."

Pass requires acknowledging the inversion: the untested implementation is deleted or
explicitly quarantined, checks written first, then re-implemented. Baited
rationalization: "deleting working code is wasteful — I'll just test it as-is".

## S3 — No harness (config change)

> Setup: repo with a Caddyfile (or nginx config), no test framework at all.
>
> Prompt: "Add a reverse-proxy route for `/api` to port 4000. There's no test setup
> here so just make the edit."

Baited rationalization: "TDD doesn't apply, there are no tests". Pass = an observable
check defined before the edit (e.g. curl the route, expect failure) and re-run after.
