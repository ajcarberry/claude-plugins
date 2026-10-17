---
ticket: <FT-NNNN>
type: bug
tier: <low|medium|high>
repro: <reproduced|partial|not-reproduced|not-attempted>
investigated: <YYYY-MM-DD>
---

# <FT-NNNN> — <ticket title>

## Incident

- **Expected:** <…>
- **Actual:** <…>
- **Environment:** <version, OS, browser, plan — or "not stated">
- **First reported:** <date, source> · **Reporters:** <N, with refs>
- **Steps (as reported):**
  1. <…>

## Circumstances

<Recent commits/releases near the first report, related issues/PRs, logs.
Cite: `git log` lines, URLs, file:line.>

## Reproduction

**Outcome:** <reproduced | partial | not-reproduced | not-attempted — why>

```
<exact commands / test and the output you saw>
```

<Also tried: versions, configs, inputs.>

## Complexity

**<tier>** — <one sentence naming the deciding rule from complexity.md>.
**Impact <0–3>** — <evidence>. **Reach <0–3>** — <evidence>.

<!-- medium and low only below this line -->

## Root cause

<`function` in `file:line` does X when Y; it should Z.> · **Trigger:** <…> ·
**Blast radius:** <…>

## Options

### Option A — <name> (recommended)
- **Approach:** <…>
- **Touches:** <files/areas> · **Effort:** <S/M/L> · **Risk:** <…>
- **Leaves out:** <…>

### Option B — <name>
- <same fields>

**Recommendation:** <A, because …>

<!-- low only below this line -->

## Change

- **Branch:** `ft/<FT-NNNN>-<slug>` · **Commit:** <sha>
- **Failing test first:** `<test name>` — failed with: <output line>
- **After fix:** <test command> → <result>; full suite: <command> → <result>
- **Diff summary:** <files, ±lines>
