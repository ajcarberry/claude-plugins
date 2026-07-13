---
name: roadmap-planning
description: Use when creating a roadmap, running quarterly/horizon planning, prioritizing themes or features, or slotting a new request, spec, or dig finding into an existing roadmap.
---

# Roadmap Planning — Proactive and Reactive

## Find the roadmap

Default location `docs/roadmap.md`; the project's declared location supersedes.
Use the [roadmap template](../../templates/roadmap.md) when creating one.

## Proactive mode — planning ahead of specs

Inputs: feedback themes (from `feedback-synthesis`), project strategy, and honest
capacity. Then:

- **Brainstorm wide before narrowing** — candidate items from themes, strategy
  gaps, and maintenance debt; no filtering during collection.
- **Prioritize with a stated frame** — effort/impact by default, RICE when the
  numbers exist to support it. The frame is stated in the roadmap so the community
  can argue with the reasoning, not the conclusion.
- **Generate the stakeholder questions** — every uncertain item produces a
  concrete question for a named audience ("Discord: how are people running this in
  CI?", "sponsors: is the Q4 commitment still the constraint?"). Unasked questions
  are how roadmaps drift from reality.
- Fewer items, honestly scoped, beats a wish list. "Later" is a real column.

## Reactive mode — new input arrives

A new spec, dig finding, or request wants a slot:

- **Displacement is explicit.** Capacity doesn't grow because something new
  arrived. "Adding X to Next pushes Y to Later" is written in the roadmap's
  displacement log, never absorbed silently.
- New evidence may re-rank old items — say which and why.
- Not everything gets a slot. "Declined, because…" with reasoning is a legitimate
  and kind outcome; route the reply through `stakeholder-comms` tone.

## Roadmap hygiene

- Every item carries a **why** (one line, citing theme/strategy evidence).
- Dated and statused (`now / next / later / done / declined`) — a roadmap without
  dates is a poster.
- The displacement log is append-only history: what moved, when, why.
- The roadmap is public product truth: written so a community member can read the
  reasoning, not just the list.
