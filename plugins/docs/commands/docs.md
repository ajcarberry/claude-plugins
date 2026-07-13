---
description: Autonomous documentation management — detect gaps, write docs, and self-review against the codebase
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
- Identify which project areas changed
- Return: list of changed areas and brief summary

### Step 2: Gap Analysis

Use a Sonnet agent (gap analyst) to cross-reference changes against documentation:
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

For each gap (in priority order), use a Sonnet agent (writer) to write or update:
- **Style override first:** if the project defines its own style (`docs/STYLE.md` or a project `writing-docs` skill), it supersedes the plugin defaults below — the `writing-docs` skill documents the lookup
- Read the appropriate template from `${CLAUDE_PLUGIN_ROOT}/skills/writing-docs/templates/`
- Read the style guide from `${CLAUDE_PLUGIN_ROOT}/skills/writing-docs/reference/style-guide.md`
- Gather codebase context (read relevant source files, configs, commands)
- Write the doc following template structure and style guide
- Save to the correct location
- Update `docs/README.md` if adding a new doc

### Step 4: Review

For 1-2 docs written/updated: **one Sonnet reviewer** covering all three dimensions
below as sections of a single prompt. For 3+ docs: one reviewer per doc, in parallel.

1. **Codebase accuracy** — verify every claim, command, path, and config example against actual source code; code snippets must be runnable. Inaccuracies need evidence.
2. **Standards compliance** — Diátaxis type adherence (ONE purpose), style guide (active voice, concise, no marketing language), correct placement and structure.
3. **Completeness** — missing cross-references, missing template sections, broken internal links, missing troubleshooting/next-steps.

Reviewers must verify concerns against source before reporting them.

### Step 5: Filter & Fix

Filter each issue with the **independent-reviewer test**: would a different qualified
reviewer, given this doc and the style guide, independently flag it? Drop everything
else — see the false-positive list at the bottom of this command.

- If no issues survive, proceed to Step 6
- Use a Sonnet agent (writer) to fix surviving issues
- If more than 3 issues were fixed, loop back to Step 4 for one re-review pass (maximum 1 re-review)

### Step 6: Finalize

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

### Step 2: Scrutiny

This mode is an explicit deep-review request, so use a panel: launch 2 parallel
Sonnet agents (a single doc) or up to 4 (a directory), splitting these dimensions:

1. **Codebase accuracy** — verify every factual claim against source: commands work, paths exist, configs current, described behavior matches implementation. Evidence required (what doc says vs what code shows).
2. **Freshness** — `git log` the source referenced by the doc since the doc's last modification; flag sections the code has outrun, with the commits that changed it.
3. **Standards** — Diátaxis compliance (ONE purpose, matches its type), style guide adherence, structure vs the type's template.
4. **Completeness** — missing template sections, broken internal links, missing prerequisites/troubleshooting/cross-references, outdated examples.

### Step 3: Filter & Fix

- Filter with the independent-reviewer test (see false-positive list below)
- Use a Sonnet agent (writer) to fix surviving issues
- Use a Sonnet agent (verifier) to re-verify the fixes are accurate (single verification pass)

### Step 4: Report

Output structured report:
- Issues found and fixed (with what changed)
- Issues requiring human judgment (if any)
- Overall doc health assessment

---

## False Positive Examples (provide to reviewers)

These do NOT survive the independent-reviewer test:
- Doc style preferences not codified in the project style guide
- Technically correct content worded differently than source comments
- Missing docs for internal implementation details (not user-facing)
- Minor formatting differences from template structure
- Pre-existing issues that predate recent changes

These are real issues — always report:
- Commands in docs that would fail if run
- Paths in docs that don't exist in the codebase
- Config examples that don't match actual config files
- Features documented that have been removed
- Missing docs for user-facing features or commands
