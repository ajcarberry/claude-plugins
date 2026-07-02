# Launchpad Infra Pack

Infrastructure domain skills for the launchpad flight sequence:

- **plan-before-apply** — dry-runs as the failing-check-first step; rollback path required before any apply
- **infra-landing-mechanics** — how `/land` deploys, observes, validates (with live failure injection), and rolls back on nomad/terraform/kubernetes

Thin by design — grows from real friction, not speculation.
