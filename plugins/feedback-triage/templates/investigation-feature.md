---
ticket: <FT-NNNN>
type: feature
tier: <low|medium|high>
investigated: <YYYY-MM-DD>
---

# <FT-NNNN> — <ticket title>

## The job

- **Who:** <role, plan, usage> · **Reporters:** <N, with refs>
- **Trying to:** <the job, in the user's terms>
- **Today they:** <workaround and its cost>
- **Problem statement:** <one sentence, no solution in it>
- **Requested solution:** <as asked — one candidate, not the answer>

## What exists

<Code, flags, docs, roadmap/spec entries, related issues/PRs — each cited.
"Possible today via X" goes here if true.>

## Requirements

**Must**
1. <testable requirement>

**Acceptance criteria**
- Given <…>, when <…>, then <…>

**Edge cases:** <empty/large input, permissions, errors, compat, platforms>
**Non-goals:** <…>
**Open questions:** <only a product owner can answer — or "none">

## Complexity

**<tier>** — <one sentence naming the deciding rule from complexity.md>.

<!-- medium and low only below this line -->

## Options

### Option A — <name> (recommended)
- **Approach:** <…>
- **Touches:** <files/areas> · **Effort:** <S/M/L> · **Risk:** <…>
- **Compat/migration:** <…> · **Leaves out:** <requirements not met>

### Option B — <name>
- <same fields>

**Recommendation:** <A, because …>

<!-- low only below this line -->

## Change

- **Branch:** `triage/<slug>` · **Commit:** <sha>
- **Tests per acceptance criterion:** <test names> → <result>
- **Full suite:** <command> → <result>
- **Diff summary:** <files, ±lines>
