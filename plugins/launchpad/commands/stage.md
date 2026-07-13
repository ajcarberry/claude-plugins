---
description: Stage a mission — clean worktree, branch, and mission state in ~15 seconds
allowed-tools: Bash, Read, Write, AskUserQuestion
argument-hint: "[description]"
---

# Stage — Mission Workspace Setup

Create a branch + worktree and write the mission brief (including a stakes call).
No research, no env init, no multi-round Q&A.

## Workflow

### Step 0: Preconditions

`git rev-parse --is-inside-work-tree`. If it fails:
> Not inside a git repository. Navigate to your project root and try again.
**STOP.**

### Step 1: Gather Description

Use `$ARGUMENTS` if provided (e.g. `/stage add prometheus alerting`); otherwise ask:
> What are we working on?

### Step 2: Generate, Validate, and Confirm

**Detect current branch** (`git branch --show-current`) — becomes the default
`<base-branch>`.

**Infer branch type** from intent: `feat/` (new functionality), `fix/` (bug),
`docs/`, `chore/` (maintenance/deps/CI), `refactor/`. Unclear → `feat/`.

**Generate branch name:** lowercase the description; keep only `[a-z0-9-]`
(everything else → hyphen); collapse/trim hyphens; ~50 chars max (break at a
hyphen); prepend the prefix.
Example: "Add Prometheus alerting rules" → `feat/add-prometheus-alerting-rules`

**Generate worktree path:** main worktree root =
`git worktree list --porcelain | head -1 | sed 's/worktree //'`. Path =
`../<repo-basename>--<branch-with-slashes-as-hyphens>` (sibling of the main
worktree).

**Classify stakes** per the [stakes reference](../references/stakes.md): anything on
the high list is `high` regardless of size; between low and standard choose `low`.
One line of judgment, no discussion.

**Validate before showing:** `git fetch origin` (non-fatal); check branch existence
(`git branch --list "<name>" && git ls-remote --heads origin "<name>"`); check
worktree dir (`test -d`).

**Confirm via AskUserQuestion**, showing branch, worktree, base, and stakes:
- "Looks good" — proceed
- "Change branch name" — ask, loop back
- "Change base branch" — only if current branch isn't `main`: choose between
  `<current-branch>` and `main`, loop back
- "Change stakes" — ask low/standard/high, loop back
- "Cancel" — abort

If the branch already exists: ask reuse (skip `-b`) or rename. If the worktree dir
already exists: ask reuse (just write mission state) or rename.

### Step 3: Create Worktree

```bash
# New branch:
git worktree add -b <branch-name> <worktree-path> <base-branch>
# Reusing existing branch:
git worktree add <worktree-path> <branch-name>
```

On failure, report the error and stop. Skip entirely if reusing an existing worktree.

### Step 4: Write Mission State

Create the state dir and keep it out of git (repo-local exclude, shared by all
worktrees — never touch the project's .gitignore):

```bash
mkdir -p <worktree-path>/.claude/mission
EXCLUDE="$(git rev-parse --git-common-dir)/info/exclude"
grep -qx '.claude/mission/' "$EXCLUDE" 2>/dev/null || echo '.claude/mission/' >> "$EXCLUDE"
```

Write `<worktree-path>/.claude/mission/brief.md` per the
[mission-state schema](../references/mission-state.md):

```markdown
---
task: <description, verbatim>
branch: <branch-name>
parent: <base-branch>
date: <YYYY-MM-DD>
stakes: <low|standard|high>
---

# Mission Brief

## Desired Outcome

<1–3 sentences: the user's intent restated as a completed, measurable condition —
"Add Prometheus alerting" → "Prometheus alerting rules are added and deployed."
Terse input gets a terse outcome. Do not invent scope or implementation details.>
```

### Step 4.5: Baseline Check (background, non-blocking)

Detect the project's test command (CLAUDE.md-named command → Makefile `test` →
package.json `scripts.test` → `go test ./...` if go.mod → `pytest` if configured;
first match only). If found, run it in the new worktree with Bash
`run_in_background` — don't wait. A failing baseline means the branch started
broken; the mission should know before claiming failures as its own. No test
command → skip silently.

### Step 5: Open Editor + Summary + STOP

Open VS Code at the worktree (non-fatal): `open -a "Visual Studio Code" <path>`,
then `code <path>`, else print the path.

```
Mission staged!

  Branch:    <branch-name>
  Worktree:  <worktree-path>
  Stakes:    <stakes>
  Baseline:  <running in background | no test command found>

  Complex work? Run /mission-plan in the new session to write the spec.
  Otherwise run /launch (or just start working — the brief loads automatically).
```

**IMPORTANT:** After printing this summary, your work is done. Take no further
actions.

## Error Handling

| Scenario | Action |
|----------|--------|
| Branch exists (local or remote) | Ask: reuse or rename |
| Worktree dir exists | Ask: reuse (write state only) or rename |
| `git worktree add` fails | Report error, stop |
| `git fetch origin` fails | Warn, continue with local state |
| Editor fails to open | Warn, print path |
| User cancels | Stop gracefully |
