---
description: Fast workspace setup — worktree + mission brief in ~15 seconds
allowed-tools: Bash, Read, Write, AskUserQuestion
argument-hint: "[description]"
---

# Stage — Fast Workspace Setup

Create a new branch + worktree and write a minimal mission brief. No research, no env init, no multi-round Q&A.

## Workflow

Follow these steps precisely:

### Step 0: Preconditions

Use Bash tool to verify we're inside a git repository:
```
git rev-parse --is-inside-work-tree
```

If this fails:
> Not inside a git repository. Navigate to your project root and try again.
**STOP.**

### Step 1: Gather Description

If the user provided a description as `$ARGUMENTS` (e.g. `/stage add prometheus alerting`), use that.

Otherwise, ask the user:

> What are we working on?

Use their response as the work description.

### Step 2: Generate, Validate, and Confirm

**Detect current branch** using Bash tool:
```
git branch --show-current
```
This is `<current-branch>` and becomes the default base branch (`<base-branch>`).

**Infer branch type** from intent:

| Intent | Prefix |
|--------|--------|
| New functionality, adding something | `feat/` |
| Fixing a bug, broken behavior | `fix/` |
| Documentation changes | `docs/` |
| Maintenance, dependencies, CI | `chore/` |
| Restructuring without behavior change | `refactor/` |

If unclear, default to `feat/`.

**Generate branch name:**
1. Take the work description
2. Lowercase it
3. Keep only `[a-z0-9-]` — replace spaces, underscores, dots, and any other characters outside this set with hyphens
4. Remove consecutive hyphens and trim leading/trailing hyphens
5. Trim to ~50 chars max (break at a hyphen boundary if possible)
6. Prepend the type prefix

Example: "Add Prometheus alerting rules" → `feat/add-prometheus-alerting-rules`

**Generate worktree path:**
1. Get the **main** worktree root (not the current worktree, if inside one). Use Bash tool:
   ```
   git worktree list --porcelain | head -1 | sed 's/worktree //'
   ```
2. Get the repo basename from that path
3. Take the branch name and replace `/` with `-`
4. Construct: `../<repo-basename>--<transformed-branch>` (sibling of the main worktree)

Example: repo `homelab-monorepo`, branch `feat/add-alerting` → `../homelab-monorepo--feat-add-alerting`

**Validate before showing to user:**

Use Bash tool to fetch so validation sees remote state (non-fatal if it fails):
```
git fetch origin
```

Use Bash tool to check if branch already exists (local or remote):
```
git branch --list "<branch-name>" && git ls-remote --heads origin "<branch-name>"
```

Use Bash tool to check if the worktree directory already exists:
```
test -d "<worktree-path>" && echo "EXISTS" || echo "OK"
```

**Show the proposed setup via AskUserQuestion:**

**Branch:** `<branch-name>`
**Worktree:** `<worktree-path>`
**Base:** `<base-branch>`

Options (if `<current-branch>` is NOT `main`):
- "Looks good" — Proceed with these settings
- "Change branch name" — Let me specify a different name
- "Change base branch" — Switch between `<current-branch>` and `main`
- "Cancel" — Abort session setup

Options (if `<current-branch>` IS `main`):
- "Looks good" — Proceed with these settings
- "Change branch name" — Let me specify a different name
- "Cancel" — Abort session setup

If the user picks "Change base branch", ask with options: `<current-branch>` (default) or `main`. Update `<base-branch>` with their choice and loop back to confirmation.

If the branch already exists, note it in the confirmation message and ask:
- "Reuse existing branch" — Use the existing branch (skip -b flag in worktree add)
- "Pick a different name" — Go back to naming

If the worktree directory already exists, note it and ask:
- "Reuse existing worktree" — Just write the mission brief into the existing worktree
- "Pick a different name" — Go back to naming

If the user wants to change the name, ask for it and loop back to confirmation.

### Step 3: Create Worktree

Use Bash tool to create the worktree (origin was already fetched in Step 2):

```
# If branch is new:
git worktree add -b <branch-name> <worktree-path> <base-branch>

# If reusing existing branch:
git worktree add <worktree-path> <branch-name>
```

If `git worktree add` fails, report the error and stop.

If reusing an existing worktree, skip this step entirely.

### Step 4: Write Mission Brief

Use Bash tool to ensure the `.claude/` directory exists in the worktree (fresh worktrees won't have it):
```
mkdir -p <worktree-path>/.claude
```

Write the completed mission brief to `<worktree-path>/.claude/mission-brief.md` using this template:

```
---
task: <task>
branch: <branch>
date: <date>
parent: <base-branch>
---

# Mission Brief

## Desired Outcome

<desired-outcome>
```

**Field guidance:**
- **task** — the user's description, verbatim
- **branch** — the branch created during staging
- **date** — today's date (YYYY-MM-DD)
- **parent** — `<base-branch>` (the branch selected as the base)
- **Desired Outcome** — 1-3 sentences describing a measurable end state. Restate the user's intent as a completed condition, not an action. If the task reads as an action ("Add Prometheus alerting"), rewrite it as "Prometheus alerting rules are added and deployed." Stay as close to the user's words as possible — do not invent scope, add assumptions, or include implementation details. A terse input ("fix caddy routing") gets a single terse outcome sentence ("Caddy routing is fixed and requests are handled correctly.").

### Step 5: Open VS Code + Summary + STOP

Use Bash tool to open VS Code at the worktree path (non-fatal if it fails). Try each method in order — if the exit code is non-zero, try the next:

1. `open -a "Visual Studio Code" <worktree-path>`
2. `code <worktree-path>`
3. If both fail, print the path for manual open.

Output a clear summary, then **STOP. Do not continue working.**

```
Session staged!

  Branch:    <branch-name>
  Worktree:  <worktree-path>

  Run `/flight-plan` in the new session to research and plan.
  Or just start working — the mission brief will load automatically.
```

**IMPORTANT:** After printing this summary, your work is done. Do not take any further actions.

## Error Handling

| Scenario | Action |
|----------|--------|
| Branch already exists (local or remote) | Ask: reuse or pick different name |
| Worktree dir already exists | Ask: reuse (just write brief) or pick different name |
| `git worktree add` fails | Report error, stop |
| `git fetch origin` fails | Warn, continue with local state |
| VS Code fails to open | Warn, print path for manual open |
| User cancels at confirmation | Stop gracefully |
