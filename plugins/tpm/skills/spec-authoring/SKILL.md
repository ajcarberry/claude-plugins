---
name: spec-authoring
description: Use when writing a spec, PRD, or problem statement — turning an idea, feedback theme, or roadmap item into a spec, running the /spec or /mission-plan flow, or judging whether a spec section is ready to approve.
---

# Spec Authoring — Problem, Proposal, Implementation

## Override convention (check first)

A project template supersedes the default: look for `specs/TEMPLATE.md`, then a
project skill named `spec-authoring`. Neither → use the
[plugin template](../../templates/spec.md).

## The three sections and their gates

A spec is three sections, approved **in order** — the frontmatter `status` field
tracks the gate (`draft → problem-approved → proposal-approved → implementing →
done`). Don't draft ahead of the gate: a proposal written before the problem is
agreed is a solution shopping for a justification.

1. **Problem** (≤ 1 page, ~400 words) — who it's for, the problem and its forces
   (numbered), objectives with scope, assumptions and open questions.
2. **Proposal** (≤ 1 page, ~400 words) — **functional and user-oriented.** What
   the experience becomes, written so a stakeholder can validate it without
   knowing the codebase. Implementation vocabulary — tech stack, file names,
   architecture — is a defect here, not detail.
3. **Implementation** — the only section allowed to talk about *how*. No page
   limit; it grows during execution.

The page limits are enforced, not aspirational: a Problem section over a page
means the problem isn't understood yet; a Proposal over a page is smuggling
implementation.

## Traceability, lightweight

Three tags, no machinery: forces are numbered (`1.`, `2.`), objectives cite their
force (`OBJ-1 — … (#1)`), proposals cite their objective (`(OBJ-1)`), and
Implementation's **Done When** carries one observable check per objective. An
objective no proposal serves, or a proposal no objective demands, is a finding —
cut it or fix the problem statement.

## Rules of substance

- **Objectives are outcomes**, never activities: "both audiences navigate
  effectively", not "reorganize the nav".
- **Evidence over assertion** — ground the problem in feedback themes, dig
  findings, or observed reality; a problem statement without evidence is an
  opinion.
- **Assumptions are written down** with when they must be decided; the ones that
  shape everything downstream get flagged as early decisions.
- **TBD is legal** in Open Questions and Implementation. It is **illegal** in the
  Problem Statement, Objectives, and Proposal — those sections being unfinished
  means the gate isn't passed.
- **Honesty is the value.** State what's out of scope, what doesn't work yet, and
  where existing alternatives are genuinely better. Padding dilutes it.

## Authoring flow

Interview the user in batches (AskUserQuestion), not one question at a time —
audience, forces, what's out of scope, what's already decided. Explore the
relevant code/docs before drafting so the spec names real constraints. Draft a
section → present → gate → next section.

## Agentic conventions

Frontmatter is machine-parseable (title, date, status, participants). When the
spec hands to launchpad, Implementation carries a `## Work Packets` section in
the orchestration format and **Done When** becomes the validation contract
`/orbit` checks against.
