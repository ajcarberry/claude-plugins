---
name: peer-review
description: Use when running a "peer review", "multi-agent review", or review pipeline over any artifact — a diff, flight plan, or document — and when deciding how many reviewers a change needs or filtering review concerns before presenting them.
---

# Peer Review — Risk-Scaled Review Pipeline

Review depth follows the [stakes rubric](../stakes-rubric/SKILL.md), not a fixed
agent count.

## Pipeline

1. **Classify stakes** — low / standard / high per the stakes rubric.

2. **Review**
   - **Low** → no dispatched reviewer, or one lightweight pass inline. Move on.
   - **Standard** → **one strong reviewer** (single agent, capable model). The
     consumer's review dimensions (rules compliance, bugs, design, security, …)
     become sections of this one reviewer's prompt — including the two-stage verdict
     where a plan/spec exists: (a) does the work comply with the plan, (b) is the
     work itself sound.
   - **High** → a **panel** of 2–4 specialist agents, one per dimension, as defined
     by the consumer.

3. **Verify** — reviewers must verify concerns against the codebase before reporting:
   read surrounding files, confirm referenced functions/configs exist. An unverified
   concern the reviewer could have verified is the reviewer's failure.

4. **Filter — the independent-reviewer test.** For each concern: *would a different
   qualified reviewer, given the same artifact and the same project rules,
   independently flag this?* If not, drop it. No scoring agents, no numeric
   thresholds — this one question does the work.

5. **Classify** — surviving concerns are **blocking** (would cause incorrect
   behavior, data loss, a security issue, or violates an explicit project rule) or
   **nit** (everything else worth a mention, prefixed "Nit:").

## Generic False Positives (drop on sight)

- Pre-existing issues in unchanged code or artifacts
- Stylistic preferences not codified in project rules
- Issues a linter, typechecker, or validation gate already catches
- Speculative concerns that couldn't be verified against source
- Correct content worded differently than the reviewer prefers
- Scope the artifact intentionally defers or the brief didn't ask for

## Consumer Responsibilities

Each command or skill using this pipeline defines:

- **Review dimensions** — what the reviewer(s) cover (sections for the single
  reviewer; one agent each on a high-stakes panel)
- **Artifact format** — what reviewers receive (diff, plan, document, context)
- **Domain-specific false positives** — appended to the generic list
- **Resolution logic** — what happens on blocking concerns (ask user, fix, stop)
