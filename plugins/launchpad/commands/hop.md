---
description: Express lane for small tasks — mini-brief, failing check first, light review, commit, optional PR in one command
argument-hint: "[task description]"
allowed-tools: Bash, Read, Write, Edit, Grep, Glob, Task, Skill, AskUserQuestion
---

# Hop — Express Lane

One command for small tasks (1-3 changes): the discipline of the full sequence without
its ceremony. Flight rules still apply — checks fail first, evidence before "done".

## Preconditions

Verify a git repo (`git rev-parse --is-inside-work-tree`); if not, stop with a message.

Take the task from `$ARGUMENTS`, or ask: "What's the hop?"

**Eligibility check** (load `launchpad:stakes-rubric` if unsure):
- **High-stakes** (auth, payments, secrets, migrations, prod infra, destructive ops)
  → refuse: "This touches <X> — high stakes gets the full sequence. Run `/mission` or
  `/stage`." **STOP.**
- Looks like **more than ~3 distinct changes** → recommend `/stage` + `/flight-plan`;
  proceed only if the user insists.

## Workflow

### Step 1: Mini-Brief (inline, not a file)

State in the conversation:
- **Task:** one sentence
- **Changes:** the files you expect to touch (verify they exist)
- **Checks:** 1-3 observable checks that fail now and will pass after — a failing
  test where a harness exists, a command/curl/page-load otherwise
  (`test-driven-development` applies)

### Step 2: Branch

If on `main`/`master`: create a branch (`hop/<slug>` using /stage's naming rules), no
worktree. Otherwise stay on the current branch and say so.

### Step 3: Implement

Run the checks first — watch them fail. Implement the minimal change. Run the checks
again — watch them pass. Web-rendered change? `browser-verified-web-work` applies.

**Escalation rule:** if mid-hop the change grows past ~3 files or reveals hidden
complexity, STOP and say: "This outgrew a hop." Offer to continue anyway or switch to
the full sequence (`/flight-plan` can plan from the current diff).

### Step 4: Light Review

Stage the changes. Self-review the diff against the mini-brief: every changed line
traces to the task; checks cover the changes; no drive-by edits. For anything
non-trivial, dispatch **one** reviewer agent with the diff and the mini-brief
(peer-review skill, standard tier). Fix blocking findings; mention nits.

### Step 5: Commit

Draft a commit message matching project style. Show it, then AskUserQuestion (header
"Commit"): "Commit" / "Edit" / "Cancel". Execute on approval, show the hash.

### Step 6: Optional PR

Ask (header "PR"): "Push + PR" / "Push only" / "Done here". For PRs, derive
title/body from the mini-brief; list the checks and their results as the test plan.

    Hop complete!
      Branch:  <branch>
      Commit:  <hash>
      Checks:  <N>/<N> passing
      PR:      <url | skipped>

## Error Handling

| Scenario | Action |
|----------|--------|
| High-stakes task | Refuse, point to full sequence |
| Scope grows mid-hop | Stop, offer escalation |
| Checks won't pass | `systematic-debugging`; after 3 failed fixes, stop and escalate |
| User cancels commit | Leave changes staged, stop gracefully |
| Push/PR fails | Show error and the manual command |
