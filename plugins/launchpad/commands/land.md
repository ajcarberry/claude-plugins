---
description: Close the mission — merge the PR, archive mission state, remove the worktree and branch
allowed-tools: Bash, Read, Write, Glob, AskUserQuestion
---

# Land — Merge & Cleanup

Runs only after `/orbit` reports GO. Landing is mechanical: merge, archive, clean
up. Deploy/observe belongs to the project's validation definition, not here.

## Workflow

### Step 1: Go-for-Landing Gate

Verify fresh, never from memory:

1. **PR exists** — `gh pr view --json number,url,reviewDecision,mergeable`
2. **CI green** — `gh run list --branch <branch> --limit 1 --json status,conclusion`
3. **Stamp clean** — `.claude/mission/validation-stamp` starts with `clean`
4. **Tree clean** — `git status --porcelain` empty

Any NO → report exactly what's blocking, point back to `/orbit`. **STOP.**

### Step 2: Stakes Gate

Read `stakes:` from `.claude/mission/brief.md`. If `high`, this merge requires an
explicit human decision — show the PR title, diff stat, and target branch, then
AskUserQuestion (header "Merge"):
- "Merge it" — proceed
- "Hold" — stop; nothing happens

Standard/low: a single confirmation inside Step 3's method question is enough.

### Step 3: Merge

Detect the repo's convention: if `gh repo view --json squashMergeAllowed,mergeCommitAllowed,rebaseMergeAllowed`
leaves only one method enabled, use it. Otherwise ask once (default: squash).

```bash
gh pr merge <n> --<method> --delete-branch
```

`--delete-branch` removes the remote and local branch. On failure (conflicts,
branch protection): report exactly what GitHub said, **STOP** — never force.

### Step 4: Archive Mission State

Copy the mission record into the main worktree before touching the worktree:

```bash
MAIN=$(git worktree list --porcelain | head -1 | sed 's/worktree //')
DEST="$MAIN/.claude/missions/$(date +%Y-%m-%d)-<branch-slug>"
mkdir -p "$DEST" && cp -R .claude/mission/ "$DEST"/
```

(`.claude/missions/` in the main worktree is the durable mission-log shelf; it's the
project's call whether to track it in git.)

### Step 5: Cleanup

```bash
git -C "$MAIN" worktree remove <worktree-path>
git -C "$MAIN" pull --ff-only
```

If git refuses because the session is *inside* the worktree being removed, don't
force it — print the two commands for the user to run from the main checkout and
note the session should move there.

### Step 6: Report

```
Landed.
  Merged:   <PR url> → <base> (<method>)
  Archived: .claude/missions/<date>-<slug>/
  Worktree: <removed | remove manually: <commands>>

Mission closed.
```

## Error Handling

| Scenario | Action |
|----------|--------|
| Gate check fails | Report blocker, point to `/orbit`, stop |
| Merge conflict / branch protection | Report GitHub's message, stop — never force |
| Worktree removal refused (cwd inside it) | Print manual commands, don't force |
| `gh` unavailable | Print manual merge + cleanup commands, stop |
