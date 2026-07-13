# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Reusable Claude Code plugins that raise the quality and consistency of AI-assisted
work. The thesis: **context quality determines agent quality** — these plugins ship
the efficiency machinery agentic workflows need (work packets, model tiering,
verification asymmetry, deterministic hook enforcement) as portable, shareable
context. The plugins themselves are the source of truth — there is no separate
design doc to keep in sync (the v4 design rationale lives in git history and the
PR record).

Four plugins, each useful alone; launchpad is the only one that calls the others,
always optionally with a stated fallback:

- **launchpad** (`plugins/launchpad/`) — dev lifecycle: `/stage` (worktree + brief
  + stakes) → `/mission-plan` (spec + work packets, optional) → `/launch`
  (implementation) → `/orbit` (validate → self-review → PR → iterate) → `/land`
  (merge + cleanup). Iron-Law flight rules; hooks enforce a dirty/clean validation
  stamp.
- **tpm** (`plugins/tpm/`) — product lifecycle: `/feedback` (signal → themes, with
  dig mode), `/triage` (issues/PRs vs. roadmap), `/roadmap`, `/spec`, `/comms`
  (audience-tailored drafts).
- **docs** (`plugins/docs/`) — `/docs` plus the `writing-docs` skill (Diátaxis
  types, default style, project override).
- **commit** (`plugins/commit/`) — `/commit` plus `commit-conventions` (atomicity,
  message-style override order).

`global/` holds the ~40-line global CLAUDE.md baseline and its installer.

## Architecture

Top-level `.claude-plugin/marketplace.json` registers all four.

### Key design rules

- **The override convention** — every skill with a default checks for a
  project-specific definition first (a same-named project skill or a documented
  file: `.claude/validation.md`, `docs/STYLE.md`, project spec template,
  CONTRIBUTING.md) and defers to it entirely.
- **Skills teach; hooks enforce** — judgment lives in skills; hooks make
  deterministic file checks only (<100ms, dumb, escape hatch documented). The
  dirty/clean stamp at `.claude/mission/validation-stamp` is the mechanism:
  PostToolUse dirties it, the validation skill cleans it, PreToolUse gates
  push/PR/merge on it.
- **Stakes as mission state** — `/stage` writes `stakes: low|standard|high` into
  the brief (rubric: `launchpad/references/stakes.md`); validation, self-review,
  and `/land` scale off the field. Nobody re-litigates risk mid-mission.
- **Mission state schema** — `.claude/mission/` (brief, spec, log, stamp,
  packets), defined in `launchpad/references/mission-state.md`. Kept out of git
  via repo-local `info/exclude`; archived by `/land`.
- **Orchestration** — `launchpad/references/orchestration.md`: work packets, model
  tiering (opus decompose/review, sonnet implement, haiku mechanical), asymmetric
  verification, ≤15-line subagent reports.
- Iron-Law skills (`verification-before-completion`, `test-driven-development`,
  `systematic-debugging`) use the full house style (Iron Law, Go/No-Go gate,
  failure modes, red flags); they were validated against pressure scenarios at
  v4 (9/9 behavioral passes) and now iterate from real usage. All other skills
  use a lean format. The Iron Laws double as routers: evidence must match the
  surface touched, which pulls specialist skills in when installed.

## Developing plugins

Budgets: command specs ≤ ~200 lines; SKILL.md ≤ ~150 lines, references loaded on
demand. Skill `description` fields are pure trigger conditions (symptoms, keywords,
situations) — never workflow summaries. Commands load pipeline skills at fixed
points via `Skill:` directives.

Official references: [plugin authoring guide](https://code.claude.com/docs/en/plugins),
[claude-code/plugins](https://github.com/anthropics/claude-code/tree/main/plugins),
[claude-plugins-official](https://github.com/anthropics/claude-plugins-official).
Helper plugins for this work (enable in `.claude/settings.json`): `plugin-dev`,
`skill-creator`, `claude-md-management`.

CI validates frontmatter (`.github/scripts/validate-frontmatter.ts`): commands and
skills must have a `description`; run
`bun .github/scripts/validate-frontmatter.ts plugins/` before committing plugin
file changes.
