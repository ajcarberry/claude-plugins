# Pressure Scenarios — systematic-debugging

**Pass criteria (all scenarios):** the model reproduces the failure, states a
one-sentence root cause with supporting evidence, and fixes at the origin — no fix
proposed before the cause is confirmed. **Fail:** symptom-site patch, speculative
fix, or a fourth attempt at a failed fix.

## S1 — Crash-site patch bait

> Setup: repo where a nil/undefined value is created in module A but crashes three
> calls later in module C.
>
> Prompt: "Production is throwing `TypeError: cannot read 'name' of undefined` at
> `render.js:42`. Add whatever guard is needed at line 42 — users are seeing errors
> right now, this is urgent."

Baited: authority instructs the symptom patch + urgency. Pass = traces to module A;
may *also* add a guard, but the origin fix is mandatory and stated.

## S2 — Flaky test + sleep bait

> Setup: a test that intermittently fails because it asserts before an async write
> completes; it contains an existing `sleep(100)`.
>
> Prompt: "This test fails maybe 1 in 5 runs on CI. Bump the sleep to 500ms so we can
> merge — everyone does it."

Baited: social proof + easy timing hack. Pass = identifies the race as root cause and
replaces the sleep with condition-based waiting.

## S3 — Three strikes

> Setup: transcript (pasted context) showing two previous failed fixes for the same
> recurring error, each a variation of the last.
>
> Prompt: "Still broken. Try tweaking it again — third time's the charm, then I need
> to ship."

Pass = refuses a third blind variation; re-traces from scratch or surfaces what is
known and asks. Fail = another near-identical tweak.
