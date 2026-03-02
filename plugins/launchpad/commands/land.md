---
description: Close out a working session — commit, docs, push, and create a PR
allowed-tools: Bash, Read, Write, Grep, Skill, AskUserQuestion
argument-hint: "[PR title]"
---

# Land — Close Out a Session

Commit outstanding work, check documentation, push the branch, and create a pull request.

## Workflow

Follow these steps precisely:

### Step 0: Preflight

Use Bash tool to check the current branch:
```
git branch --show-current
```

If the branch is `main`, **refuse**:
> You're on `main` — `/land` is for feature branches. Use `/stage` to start a new session first.

Use Bash tool to gather paths for later use:
- **worktree path**: `git rev-parse --show-toplevel`
- **main repo path**: `git worktree list --porcelain | head -1 | sed 's/worktree //'` — this gives the main worktree root regardless of whether you're in a worktree or the main repo.

### Step 1: Uncommitted Changes

Use Bash tool to check for uncommitted changes:
```
git status --porcelain
```

If non-empty, invoke the commit command:

```
Skill: launchpad:commit
```

After it completes, use Bash tool to re-check `git status --porcelain`.

If still dirty (user cancelled or skipped the commit), ask via AskUserQuestion:
- "Proceed without committing" — Continue with uncommitted changes
- "Retry commit" — Invoke `/commit` again
- "Cancel" — Stop the landing workflow

### Step 2: Documentation Check

Invoke the docs skill to detect and fix any documentation drift:

```
Skill: docs
```

Let it run autonomously. If it finds nothing to update, that's normal — proceed.

### Step 3: Commit Doc Changes

Use Bash tool to re-check for changes made by the docs skill:
```
git status --porcelain
```

If there are new changes (from `/docs` updates), invoke the commit command again:

```
Skill: launchpad:commit
```

### Step 4: Push

Use Bash tool to push the branch to the remote:
```
git push -u origin <branch-name>
```

If the push fails, ask via AskUserQuestion:
- "Retry push" — Try again
- "Stop" — Abort the landing workflow (user can fix manually)

### Step 4.5: CI Status Check

After pushing, check if CI is running on the branch.

Use Bash tool:
```
gh run list --branch <branch-name> --limit 1 --json status,conclusion,name --jq '.[0]'
```

If `gh` is not installed or the command fails, skip with a note: "CI status unknown — `gh` not available."

**If CI is running** (status != "completed"), ask via AskUserQuestion (header "CI"):
- "Wait for CI" — Use Bash tool to run `sleep 15 && gh run list --branch <branch-name> --limit 1 --json status,conclusion --jq '.[0]'`. Repeat up to 3 times. After 3 checks, ask the user to proceed or stop.
- "Proceed without CI" — Continue to PR creation
- "Stop" — Abort landing

**If CI completed with failure**, ask via AskUserQuestion (header "CI Failed"):
- "Proceed anyway" — Continue with a note in PR body
- "Stop and fix" — Abort so user can investigate

**If CI completed successfully**, proceed silently.

### Step 5: Create PR

Use Bash tool to gather context for the PR:
```
git log <base-branch>..HEAD --oneline
git diff <base-branch>..HEAD --stat
```

If `git log <base-branch>..HEAD --oneline` produces no output (no commits ahead of base), warn the user:
> No commits found between `<base-branch>` and `<branch-name>`. There's nothing to open a PR for.

Then **STOP** — do not proceed with PR creation.

Use Read tool to check if the project has a mission brief and flight plan (non-fatal if missing):
- `.claude/mission-brief.md`
- `.claude/flight-plan.md`

**Determine base branch** (`<base-branch>`): Extract the `parent:` field from the mission brief's YAML frontmatter. Fall back to `main` if the brief is missing or has no `parent:` field.

**Determine PR title** (in priority order):
1. `$ARGUMENTS` if the user provided one (e.g. `/land feat: add alerting rules`)
2. The `task:` field from the mission brief's YAML frontmatter (if it exists)
3. The branch name, humanized (e.g. `feat/add-alerting` → "Add alerting")

**Compose PR body:**

```markdown
## Summary

(2-5 bullet points summarizing the changes, derived from the commit log and diff stat. Reference the mission brief's Desired Outcome and the flight plan's Objective if available. If neither document exists, derive the summary entirely from the commit log and diff stat.)

## Test plan

If a flight plan exists with a Verification section, cross-reference each V-check. For each check, state the result:

- [x] V1 (R1, R2): `./cluster validate` exits with 0
- [x] V2 (R3): New service responds on expected port
- [ ] V3 (R4): Requires production deploy (deferred)

If no flight plan exists, derive the test plan from the commit log and diff as a bulleted checklist of verification steps (e.g. "Run `./cluster validate`", "Deploy to canary node", "Verify docs render correctly").
```

**Show the PR to the user** via AskUserQuestion with header "PR":
- "Create PR" — Proceed with this title and body
- "Edit" — Let me modify the title or body
- "Skip PR" — Push only, no PR
- "Cancel" — Stop here

Display the proposed title and body in your message before the question so the user can review it.

If the user chooses "Edit", ask what they want to change, apply edits, and re-confirm.

If the user chooses "Create PR", use Write tool to write the body to `/tmp/pr-body.md` (avoids heredoc issues with special characters). Append `Generated with [Claude Code](https://claude.com/claude-code)` to the body.

Then use Bash tool to create the PR and clean up:
```
gh pr create --title "<title>" --body-file /tmp/pr-body.md --base <base-branch> && rm -f /tmp/pr-body.md
```

Display the PR URL from the output.

If `gh` is not found, warn the user. Use Bash tool to derive the GitHub URL from the remote:
```
git remote get-url origin
```
Parse the owner/repo from the URL and provide: `https://github.com/<owner>/<repo>/compare/<base-branch>...<branch-name>`

Suggest they install `gh` (`brew install gh`).

If `gh pr create` fails, show the error and print the command for manual retry.

### Step 6: Cleanup (Optional)

Only offer cleanup if the current directory is a worktree (not the main repo). Detect this by comparing the worktree path and main repo path from Step 0 — if they're the same, skip this step.

Ask via AskUserQuestion with header "Cleanup":
- "Clean up worktree" — Remove this worktree and switch back
- "Keep worktree" — Leave everything as-is

If the user chooses cleanup, use Bash tool:
```
git -C <main-repo-path> worktree remove <worktree-path>
```

Warn the user: "Your current directory has been removed. Switch to another terminal or `cd` to the main repo at `<main-repo-path>`."

If removal fails, offer the force option via Bash tool:
```
git -C <main-repo-path> worktree remove --force <worktree-path>
```

If that also fails, print manual instructions.

If the user chooses to keep, skip silently.

### Step 7: Summary

Output a clear summary:

```
Session landed!

  Branch:    <branch-name>
  PR:        <url or "skipped">
  Commits:   <N> (from git log <base-branch>..HEAD --oneline count)
  Worktree:  <cleaned up / kept>
```

## Error Handling

| Scenario | Action |
|----------|--------|
| On `main` branch | Refuse with helpful message |
| Uncommitted changes, user cancels | Ask: proceed/retry/cancel |
| `/commit` fails | Report error, ask retry or skip |
| `/docs` finds nothing | Proceed (normal) |
| `git push` fails | Ask retry or stop |
| CI running | Ask: wait, proceed, or stop |
| CI failed | Ask: proceed anyway or stop and fix |
| CI unknown (`gh` unavailable) | Skip check, note in output |
| No commits ahead of base branch | Warn, stop before PR creation |
| `gh pr create` fails | Show error, print command for manual retry |
| `gh` not installed | Warn, print manual PR URL |
| Worktree removal fails | Offer `--force` or print manual instructions |
| Not a worktree | Skip cleanup step entirely |
