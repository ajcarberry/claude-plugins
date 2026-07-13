# TPM

The product lifecycle for a TPM/maintainer — grounded in running an open-source
project with a GitHub repo, a Discord community, and a dev team in Slack. Two
directions of flow: **inbound** (signals → themes → roadmap/specs) and **outbound**
(alignment feedback → audience-tailored comms). Every command stands alone;
launchpad's `/mission-plan` is just one caller of `spec-authoring`.

```
Discord/Slack/GitHub ──> /feedback ──> themes ──> /roadmap ──> /spec ──> (launchpad)
                            │ dig                    ▲
GitHub issues/PRs ──────> /triage ── needs-decision ─┘
                            │
                         /comms ──> community + exec drafts (never auto-posted)
```

## Commands

- **`/feedback`** — aggregate raw signal (exports, `gh`, connected MCP tools —
  source-agnostic) into ranked themes with evidence counts. `dig <theme>` pulls a
  flagged thread to the bottom and produces a findings note.
- **`/triage`** — issues/PRs classified **aligned / misaligned / needs-decision**
  against the roadmap and specs; alignment replies drafted in maintainer tone;
  nothing posted without approval.
- **`/roadmap`** — proactive horizon planning (stated prioritization frame,
  stakeholder question lists) or reactive slotting with explicit displacement.
- **`/spec`** — idea → spec: Problem → Proposal → Implementation, each section
  gated in order (problem-approved → proposal-approved). The handoff point to
  launchpad.
- **`/comms`** — one set of facts rendered for a named audience: community post or
  exec sponsor update. Drafts only; never posts.

## Skills

`feedback-synthesis` (clustering, evidence discipline, frequency vs. severity, the
dig), `triage-alignment` (verify-before-judging, classification, OSS feedback
tone), `roadmap-planning` (both modes, displacement log, hygiene),
`stakeholder-comms` (audience model, facts-only, same-news-both-audiences),
`spec-authoring` (three gated sections, 1-page limits on Problem and Proposal,
functional-not-implementation proposals, lightweight OBJ-N traceability;
`specs/TEMPLATE.md` supersedes the plugin template).

## Conventions

- **Source of truth:** roadmap at `docs/roadmap.md`, specs in `specs/` — the
  project's declared locations supersede (override convention).
- **Artifacts:** themes → `docs/feedback/<date>-themes.md`; updates →
  `docs/updates/<date>-<audience>.md`.
- **Boundaries:** drafts everywhere — nothing is posted to GitHub, Discord, or
  email without explicit approval.
