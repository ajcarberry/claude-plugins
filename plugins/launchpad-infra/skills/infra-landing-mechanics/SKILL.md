---
name: infra-landing-mechanics
description: Use when deploying infrastructure changes to a cluster or homelab and verifying them live — /land's deploy, observe, and validate steps for nomad/terraform/kubernetes environments, including live failure-injection checks and rollback.
---

# Infra Landing Mechanics

How `/land` executes for cluster/homelab infrastructure.

## Deploy

- Note the current version first (`nomad job inspect <job> | jq .Job.Version`,
  `terraform state pull` snapshot, current k8s revision) — that's the rollback target.
- Apply the planned change (`nomad job run`, `terraform apply` of the reviewed plan,
  `kubectl apply`). One change set at a time; don't batch unrelated applies into a
  landing.

## Observe (condition-based, bounded — no blind sleeps)

- Scheduler state: `nomad job status` until allocations are running and healthy /
  `kubectl rollout status` until complete.
- Service health: Consul checks green, health endpoint 200s, target scraped by
  Prometheus.
- Logs of the new allocation for the first minutes — clean of crash loops and new
  errors.

## Validate — landing V-checks, including failure injection

- Run every `[landing]` check from the plan against the live system.
- **Negative checks run for real**: kill the container/allocation and watch the
  alert arrive (`nomad alloc stop`, then watch Alertmanager/Slack); block the
  dependency and watch the circuit breaker/queue behave as designed. Time them
  against the plan's stated windows.
- Confirm the alert *clears* after recovery — a stuck alert is also a failure.

## Rollback (abort-to-orbit)

`nomad job revert <job> <previous-version>` / `terraform apply` the prior plan /
`kubectl rollout undo`. Then verify recovery with the same health observations as
the deploy — rollback isn't done until the system is verified back to its previous
healthy state.
