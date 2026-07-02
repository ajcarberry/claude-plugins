---
name: plan-before-apply
description: Use when changing infrastructure as code — terraform, nomad, kubernetes, ansible, docker-compose, DNS, proxy configs — before applying anything to a live environment. Also use when tempted to apply and see what happens.
---

# Plan Before Apply

Infra has no unit tests — the dry-run **is** the failing-check-first step
(`test-driven-development`'s no-harness branch). Applying to find out what happens is
debugging in production.

## The Loop

1. **Dry-run first, read all of it:**
   - `terraform plan` — every create/change/**destroy** accounted for; an unexpected
     destroy is a full stop, not a note
   - `nomad job plan` — placement succeeds, allocation diff matches intent
   - `kubectl apply --dry-run=server -f ...` / `kubectl diff`
   - `ansible-playbook --check --diff`
   - No dry-run mode (Caddy, DNS, compose)? Validate syntax
     (`caddy validate`, `docker compose config`) and state the expected observable
     diff before applying.
2. **The plan is the RED check** — it must show *exactly* the intended change, no
   more. Surprises in the plan get root-caused before apply, not after.
3. **Rollback path stated before apply** — previous job version, prior tf state,
   git revert of the config. No rollback path = high-stakes gate (stakes-rubric),
   ask before proceeding.
4. **Apply, then verify GREEN** — re-run the plan (should show no changes) and check
   the real observable: service healthy, DNS resolving, route responding.

## Red Flags — STOP

- Applying without reading the plan output ("it's a small change").
- A destroy in the plan you didn't explicitly intend.
- Editing live state by hand to make the plan agree.
- Persistent data in the blast radius without a fresh backup (`data-safety`).
