---
name: peer-review
description: This skill should be used when running a "multi-agent review", "peer review", "confidence scoring", or "parallel specialist review" pipeline. Provides the scoring rubric, review pipeline pattern, false positive filtering, and classification rules for reviewing any artifact (flight plans, commits, documents) with parallel agents and confidence-based concern filtering.
---

# Peer Review

## Pipeline

A reusable pattern for parallel specialist review with confidence-based filtering.

1. **Specialist review** — launch N parallel agents, each focused on a distinct review dimension. Each agent receives the artifact(s) under review and returns a list of concerns with reasoning. Agents must verify concerns against the broader codebase — read surrounding files, check that referenced functions/handlers/configs exist, and confirm assumptions before reporting. A concern the agent could have verified but didn't is the agent's failure, not a property of the concern.

2. **Confidence scoring** — for each concern, launch a parallel Haiku agent (via Task tool with `subagent_type: "general-purpose"` and `model: "haiku"`) that scores it using the [scoring rubric](references/scoring-rubric.md).

3. **Filter** — discard concerns scoring below the threshold (default: 80).

4. **Classify** — surviving concerns are either **blocking** (must resolve) or **non-blocking (nit)** (optional). See the [scoring rubric](references/scoring-rubric.md) for classification guidance.

### Consumer Responsibilities

Each skill or command that uses this pipeline defines:

- **Agent count and focus areas** — how many specialists and what each reviews
- **Artifact format** — what the agents receive (diff, plan, document, etc.)
- **Domain-specific false positives** — appended to the generic list from the peer-review skill
- **Resolution logic** — what happens when blocking concerns are found (ask user, auto-fix, stop, etc.)

## Scoring

Read [scoring-rubric.md](references/scoring-rubric.md) and give it to each scoring agent verbatim.

## False Positives

These domain-general patterns typically score 0-50 and should not survive filtering:

- Pre-existing issues in unchanged code or artifacts
- Stylistic preferences not codified in project rules
- Issues a linter, typechecker, or validation gate would catch
- Speculative concerns that can't be verified, even after reviewing source
- Technically correct content worded differently than the reviewer prefers

Each consumer of this skill should append **domain-specific** false positive examples relevant to their review context.

## Classification

See the [scoring rubric](references/scoring-rubric.md) for how surviving concerns are classified as blocking or non-blocking (nit).
