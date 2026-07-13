---
title: <Name> Spec
date: <YYYY-MM-DD>
status: draft   # draft → problem-approved → proposal-approved → implementing → done
participants: [<who>]
---

# <Name>

## Problem

<!-- ≤ 1 page (~400 words). Approved before the Proposal is written. -->

### Who is this for?

- <audience — and what they need from this spec (alignment, prioritization, context)>

### Problem Statement

<The problem and why it matters — what stalls or breaks if it goes unsolved.
When more than one force is at work, number them:>

1. **<Force>.** <What makes this hard, with the evidence.>
2. **<Force>.** <…>

### Objectives and Scope

<!-- Objectives are outcomes, not activities. Each cites the force it answers. -->

**OBJ-1 — <outcome> (#1)**

- <observable sub-outcome>
- <observable sub-outcome>

**OBJ-2 — <outcome> (#2)**

- <…>

**Out of scope:** <what this spec deliberately does not address>

### Assumptions and Open Questions

- **<Topic>.** <The assumption or question, and when it must be decided — early
  decisions that shape everything downstream get flagged as such.>

## Proposal

<!-- ≤ 1 page (~400 words). Functional and user-oriented: what the experience
     becomes, not how it's built. No tech stack, no file names, no architecture —
     that vocabulary belongs in Implementation. Approved before Implementation
     is planned. -->

### Summary

<One proposal per objective, numbered to match:>

1. **<Proposal name>** — <one line> (OBJ-1)
2. **<Proposal name>** — <one line> (OBJ-2)

### <Proposal name> (OBJ-1)

<What someone can do or experience once this exists. Written so a user or
stakeholder can validate it without knowing the codebase.>

### <Proposal name> (OBJ-2)

<…>

## Implementation

<!-- The only section allowed to talk about *how*. No page limit — it grows as
     it's executed. TBD is legal here; it is not legal in Problem or Proposal. -->

### Done When

<!-- One observable check per objective — command, page load, measurable state.
     These are what /orbit validates against when launchpad runs the work. -->

- OBJ-1: <check>
- OBJ-2: <check>

### Plan

<Whichever shape fits the work:
— handed to launchpad `/launch` → a `## Work Packets` section in the
  orchestration format (goal, files, contracts, spec slice, done-check, tier);
— product/program work → a prioritized backlog table with per-item
  specifications (type, covers, answers, takeaway).>
