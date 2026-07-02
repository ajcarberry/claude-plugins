---
name: product-spec-authoring
description: Use when writing a PRD, product spec, decision document, or one-pager — turning a product idea into a document stakeholders can approve, or recording a product/technical decision and its alternatives.
---

# Product Spec Authoring

Product documents are `/mission` specs with stakeholders. Same discipline: problem
before solution, alternatives on the record, success observable.

## PRD Shape (scale to the decision's weight)

1. **Problem** — who hurts, how much, evidence. If this section is weak, stop:
   no solution section rescues an unvalidated problem.
2. **Outcome** — what changes for the user/business, stated measurably ("support
   tickets about X drop", "setup time under 5 minutes") — the product analog of
   V-checks. "Improve experience" is not an outcome.
3. **Solution sketch** — enough shape to estimate and to argue with; not an
   implementation plan (that's `/flight-plan`'s job when it becomes buildware).
4. **Alternatives considered** — one line each with the rejection reason. This is
   what makes the doc a decision record instead of a pitch.
5. **Out of scope** — explicit non-goals; the anti-scope-creep list.
6. **Open questions** — named, each with an owner; unanswered ≠ hidden.

## Decision Docs

For a recorded decision (cousin of the docs plugin's ADR template): context →
decision → alternatives with rejection reasons → consequences (including the bad
ones — a decision doc with no downsides recorded wasn't thought through).

## Rules

- One document, one decision. Bundled decisions get bundled rejections.
- Requirements needing contract-grade precision (compliance, external commitments):
  borrow EARS patterns from `launchpad:requirements-authoring`.
- Write for the skeptical reader — every claim either has evidence or is labeled an
  assumption.
