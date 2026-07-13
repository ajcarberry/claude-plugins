---
name: triage-alignment
description: Use when reviewing community-raised GitHub issues, bug reports, or PRs against the project's roadmap and specs — classifying them, deciding whether a contribution fits the project's direction, or drafting maintainer feedback on one.
---

# Triage Alignment — Issues and PRs vs. the Project's Direction

## Source of truth (find it first)

Alignment means alignment *to something*. Locate the project's canonical roadmap
and specs — default locations `docs/roadmap.md` and `specs/`, superseded by
whatever the project declares (CLAUDE.md, CONTRIBUTING.md). If neither exists,
say so and triage on maintainer judgment only — flag that the project needs a
written roadmap for triage to be consistent.

## Verify before judging

An issue is a claim. Before classifying: read it fully, check for duplicates in
the tracker, reproduce cheap claims (a command, a glance at the code), read a PR's
actual diff — not just its description. Misjudging a contributor's work because
you skimmed it costs community trust that doesn't come back.

## Classification

- **aligned** — fits the roadmap/specs. Action: label, milestone, (for PRs) queue
  for real review.
- **misaligned** — conflicts with written direction or adds scope the roadmap
  deliberately excludes. Action: explain and redirect (see tone), don't leave it
  hanging.
- **needs-decision** — the roadmap is silent, or this is new evidence that the
  roadmap might be wrong. Action: route to `/roadmap` (reactive mode) or a dig —
  never quietly absorb direction changes through triage.

A valid bug is **aligned by default** — bugs don't need roadmap justification;
only their *priority* does.

## Feedback tone (OSS-specific, part of the skill)

Someone gave the project free work or a free bug report. Feedback that redirects
without demoralizing: thank them concretely for the specific thing; state the
reasoning, citing the roadmap/spec by link — direction, not preference; offer the
aligned path if one exists ("this fits better as X", "the Y issue is where this is
tracked"); be decisive — a kind, clear "no, because…" beats a vague "maybe later"
that strings a contributor along.

## Boundaries

Draft feedback; **never post to GitHub without the user's OK**. Triage classifies
and routes — it doesn't rewrite the roadmap (that's `/roadmap`) and doesn't do
deep code review of aligned PRs (that's a review pass, after triage).
