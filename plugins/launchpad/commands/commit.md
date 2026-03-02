---
description: Review staged changes with parallel agents and confidence scoring, then commit if approved
allowed-tools: Bash, Read, Glob, Grep, Task, Skill, AskUserQuestion
---

# Commit — Review & Commit

Review staged changes using the peer-review pipeline, run project validation, and commit if approved.

## Current State

### Staged Changes
!`git diff --cached --stat`!

### Detailed Diff
!`git diff --cached`!

### Recent Commit Style
!`git log --oneline -10`!

### Working Tree Status
!`git status --porcelain`!

## Workflow

### Step 1: Eligibility

If the staged diff is empty (no output from `git diff --cached`):
> Nothing staged. Use `git add` to stage changes first.
**STOP.**

If the staged changes are trivially small (only whitespace or comment changes), skip to Step 5 — no review needed.

### Step 2: Context Discovery

Use a Haiku agent to discover what this project needs for review:
- Read `CLAUDE.md` (if it exists) to understand project structure, conventions, and validation commands
- Scan `.claude/rules/` for any rule files relevant to the changed file types
- Identify affected project areas from the staged diff
- Determine which validation commands the project defines (look in CLAUDE.md, Makefile, package.json scripts, pyproject.toml, etc.)
- Return: list of affected areas, applicable rules summary, and specific validation commands to run (if any)

### Step 3: Validation Gate

If Step 2 identified project-defined validation commands, run them.

**If any validation fails → STOP.** Report exactly what failed and what needs fixing. Do not proceed.

If no validation commands were discovered, skip this step — proceed directly to review.

### Step 4: Peer Review

Load the `launchpad:peer-review` skill using the Skill tool, then execute its pipeline with these parameters:

**Agent count and focus areas:** 4 parallel Sonnet agents.

| Agent | Focus |
|-------|-------|
| #1 — Rules Compliance | Audit changes against CLAUDE.md and any project rule files (`.claude/rules/`) discovered in Step 2. Only flag violations that are clearly relevant to the actual changes being reviewed — project rules guide code generation, so not every rule applies during review. |
| #2 — Bug & Regression Detection | Scan the staged diff for functional bugs. Focus on impactful issues: logic errors, incorrect conditions, missing error handling that will cause failures. Read surrounding files (handlers, related task files, referenced modules) to verify concerns and catch regressions against established patterns. |
| #3 — Architecture & Design | Verify changes fit existing patterns, live in the correct location, and respect project conventions discovered in Step 2. Flag over-engineering or unnecessary complexity. |
| #4 — Security | Check for hardcoded secrets, improper file permissions, injection vulnerabilities, sensitive data in logs, credential exposure. Security concerns are always blocking. |

**Artifact format:** Each agent receives the full staged diff (`git diff --cached`), the affected areas and rules summary from Step 2, and CLAUDE.md (if it exists). Agents have full repository access and must read surrounding files (handlers, related modules, referenced configs) to verify any concern before reporting it.

**Domain-specific false positives** (append to the peer-review skill's generic list):
- Pre-existing issues on lines not modified in this diff
- Issues that validation (Step 3) would already catch — linter errors, syntax problems, type errors
- General code quality suggestions not required by project rules
- Functionality changes that are clearly intentional (the core purpose of the diff)
- Issues flagged by project rules but explicitly silenced in the code

**The false positive test:** Would a different qualified reviewer, given this same diff and these same project rules, independently flag the same issue? If not, it's likely a false positive.

**Resolution logic:**
- **Blocking concerns** → report each with `file:line` reference and confidence score. Prefix non-blocking items with "Nit:". **DO NOT** proceed to Step 5. **DO NOT** propose a commit message.
- **Only nits** → list nits briefly in the review summary, proceed to Step 5.
- **Clean** (no concerns survive filtering) → proceed to Step 5.

### Step 5: Commit Message

Only reach this step if no blocking issues remain.

Draft a commit message that matches the project's existing style (from `git log --oneline`). If no clear convention exists, use conventional commits:
- Type prefix: feat, fix, refactor, docs, style, perf, test, chore
- Subject ≤72 chars, imperative mood
- Body: what and WHY, wrapped at 72 chars
- Footer: `Co-Authored-By: Claude <noreply@anthropic.com>`

**Output the complete commit message in a code block** before asking for approval.

If there were non-blocking nits, list them after the message.

Mention any untracked files from `git status` that might have been forgotten.

Use AskUserQuestion (header "Commit") with options:
- "Commit" — Proceed with this message
- "Edit" — Provide a revised message
- "Cancel" — Abort without committing

**IMPORTANT:** The commit message MUST be displayed as text output BEFORE calling AskUserQuestion.

### Step 6: Execute

If user approves, execute using HEREDOC format:

```bash
git commit -m "$(cat <<'EOF'
<message here>
EOF
)"
```

Show the commit hash and a one-line summary.

## Error Handling

| Scenario | Action |
|----------|--------|
| Nothing staged | Report, suggest `git add`, stop |
| Validation fails | Report failures, stop |
| No CLAUDE.md found | Proceed without project rules context |
| Agent dispatch fails | Log which agent failed, continue with remaining |
| All agents timeout | Skip review, warn user, proceed to commit message |
| User cancels | Stop gracefully |
