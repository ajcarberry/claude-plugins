---
description: Autonomous documentation management — detect gaps, write docs, and self-review with confidence scoring
allowed-tools: Bash(git *), Read, Grep, Glob, Write, Edit, Task, AskUserQuestion
argument-hint: "[review <path>]"
---

Manage project documentation autonomously. Detect drift, write or update docs, and self-review for accuracy.

## Determine Mode

Parse arguments to determine mode:
- No arguments → **Autonomous mode** (detect + fix + review)
- `review <path>` → **Focused review mode** (scrutinize specific docs)

---

## Autonomous Mode (no arguments)

### Step 1: Triage

Use a Haiku agent to scan recent changes and doc state:
- Run `git log --oneline -20 --no-merges` to see recent code changes
- Run `git diff --name-only HEAD~10 2>/dev/null || git diff --name-only HEAD~5` to see changed files
- List existing docs and their topics in `docs/`
- Identify which code areas changed (ansible, nomad, terraform, tools, docs)
- Return: list of changed areas and brief summary

### Step 2: Gap Analysis

Use a Sonnet agent (the Librarian) to cross-reference changes against documentation:
- For each changed code area, check if corresponding docs exist and are current
- Identify: undocumented features, stale docs referencing removed code, outdated commands/paths
- Check `docs/README.md` index for completeness
- Return: prioritized list of gaps, each with:
  - What's missing or stale
  - Which doc file to create or update
  - Suggested Diátaxis type (tutorial/guide/reference/ADR)
  - Priority (high/medium/low)

If no gaps found, report "Documentation is current" and stop.

### Step 3: Resolve Gaps

For each gap (in priority order), use a Sonnet agent (the Historian) to write or update:
- Read the appropriate template from `${CLAUDE_PLUGIN_ROOT}/skills/documentation-standards/templates/`
- Read the style guide from `${CLAUDE_PLUGIN_ROOT}/skills/documentation-standards/reference/style-guide.md`
- Gather codebase context (read relevant source files, configs, commands)
- Write the doc following template structure and style guide
- Save to the correct location
- Update `docs/README.md` if adding a new doc

### Step 4: Multi-Agent Review

For each doc written or updated in Step 3, launch 3 parallel Sonnet agents:

1. **Codebase Accuracy Agent**: Read the doc and verify every claim, command, path, and config example against actual source code. Check that code snippets are runnable. Return list of inaccuracies with evidence.

2. **Standards Compliance Agent**: Read the doc and check Diátaxis type adherence (does it serve ONE purpose?), style guide compliance (active voice, concise, no marketing language), correct directory placement, proper structure (title, prerequisites, steps, verification). Return list of violations.

3. **Completeness Agent**: Read the doc and check for missing cross-references to related docs, missing sections expected by the template, broken internal links, missing troubleshooting or next-steps sections. Return list of gaps.

### Step 5: Confidence Scoring

For each issue found in Step 4, use a parallel Haiku agent to score confidence 0-100:

Provide this rubric to each scoring agent verbatim:
- 0: Not confident at all. This is a false positive — the doc is actually correct, or the issue is a style preference not in the style guide.
- 25: Somewhat confident. Might be an issue but cannot verify against source code. If stylistic, not explicitly in the style guide.
- 50: Moderately confident. Verified as a real issue but minor — formatting, slight wording improvement, non-critical missing section.
- 75: Highly confident. Verified against source code that the doc is inaccurate or missing critical content. Directly impacts reader's ability to use the documentation.
- 100: Absolutely certain. Confirmed the doc makes a factually wrong claim, references a removed feature, or contains a broken command that will fail.

### Step 6: Filter & Fix

- Discard all issues scoring below 80
- If no issues remain, proceed to Step 7
- Use a Sonnet agent (the Historian) to fix remaining issues
- If significant fixes were made (more than 3 issues fixed), loop back to Step 4 for one re-review pass (maximum 1 re-review)

### Step 7: Finalize

Report summary:
- Docs created (with paths)
- Docs updated (with paths and what changed)
- Issues found and fixed
- Any issues that need human judgment

---

## Focused Review Mode (`review <path>`)

### Step 1: Scope

Use a Haiku agent to:
- Read the specified doc(s) at the given path (file or directory)
- Identify what the doc claims: commands, paths, configs, features, behavior
- Map each claim to the source code location that could verify it
- Return: list of claims with their verification targets

### Step 2: Multi-Agent Scrutiny

Launch 4 parallel Sonnet agents to examine the doc(s):

1. **Codebase Accuracy Agent**: For every factual claim in the doc, read the actual source code and verify. Check commands work, paths exist, configs are current, behavior described matches implementation. Return issues with evidence (what doc says vs what code shows).

2. **Freshness Agent**: Check `git log` for changes to the source code referenced by this doc since the doc was last modified. Identify any code changes that the doc doesn't reflect. Return list of potentially stale sections with the git commits that changed the underlying code.

3. **Standards Agent**: Check Diátaxis compliance (does it serve ONE purpose and match its type?), style guide adherence, structure quality against the template for its type. Return violations with specific locations.

4. **Completeness Agent**: Check for missing sections expected by the Diátaxis template, broken internal links, missing prerequisites, missing troubleshooting, missing cross-references to related docs, outdated examples. Return gaps.

### Step 3: Confidence Scoring

For each issue from Step 2, use parallel Haiku agents to score 0-100 using the same rubric as autonomous mode.

### Step 4: Filter & Fix

- Discard issues scoring below 80
- Use a Sonnet agent (the Historian) to fix high-confidence issues
- Use a Sonnet agent (the Librarian) to re-verify the fixes are accurate (single verification pass)

### Step 5: Report

Output structured report:
- Issues found (with confidence scores)
- Issues fixed (with what changed)
- Issues requiring human judgment (if any)
- Overall doc health assessment

---

## False Positive Examples (provide to scoring agents)

These should score LOW (below 50):
- Doc style preferences not codified in the project style guide
- Technically correct content worded differently than source comments
- Missing docs for internal implementation details (not user-facing)
- Minor formatting differences from template structure
- Pre-existing issues that predate recent changes

These should score HIGH (75-100):
- Commands in docs that would fail if run
- Paths in docs that don't exist in the codebase
- Config examples that don't match actual config files
- Features documented that have been removed
- Missing docs for user-facing features or commands
