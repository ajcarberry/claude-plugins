---
name: web-landing-mechanics
description: Use when deploying a web app or site and verifying the deployment — /land's deploy, observe, and validate steps in a web project (preview deploys, production promotion, post-deploy smoke checks).
---

# Web Landing Mechanics

How `/land`'s generic loop (deploy → observe → validate → stabilize-or-rollback)
executes for web projects.

## Deploy

- Prefer the platform's preview→promote flow (Vercel/Netlify/CF Pages): deploy
  preview, validate there, then promote — promotion is also your rollback lever.
- Self-hosted: build → deploy behind the proxy → health-check before switching
  traffic. Know the previous artifact/tag before overwriting it.
- CI/CD auto-deploys on merge? Watch the run, don't re-deploy.

## Observe (condition-based, no blind sleeps)

- Poll the deployed URL until it returns 200 with fresh content (check a version
  marker or build hash, not just status).
- Watch error telemetry for the first minutes: platform logs, Sentry/error tracker,
  server 5xx rates.

## Validate — landing V-checks

- Load the changed pages **on the deployed URL** (not localhost) — browser console
  clean, screenshots as evidence (`browser-verified-web-work` against production).
- Exercise the critical path the change touched: form submits, auth flow, checkout.
- Negative checks as planned: bad input rejected with the right message, 404s render
  the 404 page.

## Rollback

Promotion-based platforms: promote the previous deployment. Self-hosted: redeploy
the previous artifact/tag. Verify recovery the same way you verified the deploy.
