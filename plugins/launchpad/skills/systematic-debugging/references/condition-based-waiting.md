# Condition-Based Waiting

Sleeps encode a guess about timing. Guesses are wrong on slow CI, fast laptops, and
loaded clusters — producing flakes that waste hours. Wait on the *condition*, not the
clock.

## The Pattern

Poll an observable predicate at a short interval with a bounded timeout:

- **Tests:** poll every 10–50ms, timeout 5s, fail with a message stating which
  condition never became true (most frameworks: `eventually`, `waitFor`,
  `assert.Eventually`).
- **Shell / infra:** `until <check>; do sleep 1; done` wrapped with a timeout —
  e.g. `timeout 60 bash -c 'until curl -sf localhost:8080/health; do sleep 1; done'`.
- **Deploys:** poll the scheduler/health API (`nomad job status`, `kubectl rollout
  status`, Consul checks) instead of sleeping "long enough".

## Rules

- The predicate must be the thing you actually need (port answering, file present,
  record visible), not a proxy ("the service usually starts in 3s").
- Always bound the wait. An unbounded poll is a hang; a bounded one is a diagnosis —
  the timeout message tells you exactly which condition failed.
- If there is nothing observable to poll, that is a design gap: add a health
  endpoint, a ready file, or a status field — don't add a bigger sleep.

## Smell Test

Any `sleep N` in test or automation code where N was chosen by trial and error is a
race condition with a deadline. Replace it.
