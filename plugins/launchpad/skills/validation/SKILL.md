---
name: validation
description: Use when validating a branch or change — before opening a PR, when /orbit runs its validation step, when the user asks "is this ready?", or before claiming work is ready to ship or merge.
---

# Validation — What "Validated" Means

## Override convention (check first)

The project defines validation, not this skill. Before running the default, look
for, in order:

1. A project skill named `validation` (`.claude/skills/validation/`)
2. `.claude/validation.md` in the project root

If either exists, **defer to it entirely** — it replaces the default definition
below (it may reference this skill's stamp mechanics). If neither exists and the
project clearly has recurring validation needs, suggest creating
`.claude/validation.md` once — don't nag.

## Default definition

A change is validated when all of these pass, fresh, in the current worktree:

1. **Build** — the project builds/compiles (skip if nothing to build).
2. **Tests** — the project's test command passes. Discover it in order: command
   named in CLAUDE.md → Makefile `test` target → package.json `scripts.test` →
   `go test ./...` if go.mod → `pytest` if pytest config. First match only.
3. **Lint/typecheck** — if the project defines them.
4. **Exercised end-to-end** — the changed behavior was actually driven and observed
   (run the command, load the page, hit the endpoint), not just covered by tests.
   Evidence matched to the surface touched — a specialist skill (browser
   verification, plan-before-apply) answers this better when installed; use it.

**When `stakes: high`** (from `.claude/mission/brief.md`): additionally exercise the
risky surface directly (the auth flow, the migration on a copy of real data), and
back up before anything destructive.

## The stamp

Only after **every** check passes, write the stamp:

```bash
mkdir -p .claude/mission && echo "clean $(date -u +%Y-%m-%dT%H:%M:%SZ)" > .claude/mission/validation-stamp
```

Never write `clean` early, partially, or "because it's about to pass" — the
PreToolUse gate trusts this file. On any failure, leave the stamp dirty, fix at
root cause (`systematic-debugging`), and re-run from the top.

## Evidence rules

Results must come from commands run *now*, in this worktree — not from memory, an
earlier session, or a subagent's claim (`verification-before-completion`). Log the
run and outcome to `.claude/mission/log.md` when a mission is active.
