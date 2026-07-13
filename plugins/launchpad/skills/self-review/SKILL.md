---
name: self-review
description: Use when a change is complete and about to become a PR — /orbit's pre-PR step — or when asked to review the branch's whole diff before requesting human review.
---

# Self-Review — Fresh Eyes Before the PR

The implementer can't review itself: its context is polluted with its own
intentions. A fresh-context subagent that never saw the implementation conversation
approximates an independent reviewer. That's the mechanism — everything else is
calibration.

## Depth follows stakes

Read `stakes:` from `.claude/mission/brief.md` (no mission → judge by the
[stakes reference](../../references/stakes.md)):

- **low** — quick inline pass by the orchestrator over the full diff. No subagent.
- **standard** — **one fresh-context subagent** reviews the full diff against the
  spec/brief. Its prompt covers all dimensions: does the work match the spec (no
  more, no less), bugs and regressions, fit with existing patterns, security.
- **high** — add a **second reviewer** with a specialist security/data lens
  (secrets, injection, permissions, data loss, migration safety). Run both in
  parallel.

## What the reviewer receives

Diff against the base branch (`git diff <base>...HEAD`), the spec or brief, the
project's CLAUDE.md path — and repository access. Reviewers **must verify concerns
against the codebase before reporting** (read surrounding files, confirm referenced
functions exist). An unverified concern the reviewer could have verified is the
reviewer's failure.

## Filter — the independent-reviewer test

For each concern: *would a different qualified reviewer, given the same diff and
the same project rules, independently flag this?* If not, drop it.

Drop on sight:

- Pre-existing issues on lines this diff didn't touch
- Stylistic preferences not codified in project rules
- Anything validation already catches (lint, types, tests)
- Speculative concerns not verified against source
- Correct content worded differently than the reviewer prefers
- Scope the spec intentionally defers

## Classify and resolve

Surviving concerns are **blocking** (incorrect behavior, data loss, security issue,
or violates an explicit project rule) or **nit** (worth a mention, prefixed "Nit:").

- **Blocking** → fix before the PR opens. Fixes dirty the validation stamp —
  re-run `validation` after.
- **Nits** → carry into the PR description; don't block on them.
- Log the verdict to `.claude/mission/log.md`.
