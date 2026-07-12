---
description: Stage intelligently, write the message in the project's convention, and commit — never pushes
allowed-tools: Bash, Read, Glob, Grep, Skill, AskUserQuestion
argument-hint: "[message hint]"
---

# Commit

Load `Skill: commit:commit-conventions` first — it owns atomicity and message
style. This command is the workflow around it.

## Current State

### Working Tree
!`git status --porcelain`!

### Unstaged + Staged Diff (stat)
!`git diff --stat && git diff --cached --stat`!

### Recent Commit Style
!`git log --oneline -15`!

## Workflow

### Step 1: Survey

Nothing staged and nothing modified → report "nothing to commit", **STOP**.

Review the full diff (`git diff` + `git diff --cached`) and untracked files.
Guard rail before anything is staged: flag anything that looks like a secret,
credential, build artifact, or editor droppings — these never get staged silently.

### Step 2: Group

Apply the skill's atomicity rules to propose commit group(s):

- Everything is one coherent change → one commit.
- Unrelated changes present → propose the split (which files/hunks per commit,
  each with a draft subject) and confirm via AskUserQuestion before staging.
- Already-staged changes are respected as the user's grouping — don't unstage;
  if the staged set looks incomplete (code without its test file), mention it.

### Step 3: Message

Determine the convention per the skill's override order (documented → inferred →
default). `$ARGUMENTS` is a content hint, not verbatim text. Draft the message —
subject + body-with-why where the change warrants it.

### Step 4: Confirm and Execute

**Show the message(s) in a code block**, list any flagged strays, then
AskUserQuestion (header "Commit"): commit / edit message / cancel.

On approval, per group: stage exactly that group's files (`git add <paths>`,
`git add -p` where files are mixed), commit with a HEREDOC message, show the hash
and one-line summary. **Never push** — if the user wants that, they'll say so.

## Error Handling

| Scenario | Action |
|----------|--------|
| Nothing to commit | Report, stop |
| Possible secret/artifact in the diff | Flag it, exclude from staging unless the user insists |
| Pre-commit hook fails | Show the output, fix if it's mechanical (formatting), otherwise surface, never `--no-verify` unasked |
| User cancels | Leave staging exactly as found |
