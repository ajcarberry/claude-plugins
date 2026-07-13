---
name: commit-conventions
description: Use when committing changes, writing a commit message, deciding what to stage together, or splitting a working tree into multiple commits — including checkpoint commits during implementation work.
---

# Commit Conventions — Atomicity and Message Style

## Atomicity

One commit = one reviewable change that stands alone.

- **Stage related changes together** — the code, its tests, and its docs are one
  change, not three commits.
- **Split unrelated changes** — a bug fix discovered mid-feature is its own
  commit. `git add -p` exists for mixed files.
- A commit should leave the tree in a working state; don't commit a change whose
  test lands two commits later.
- Never `git add -A` blindly: review `git status` for strays (untracked files that
  belong, and ones that definitely don't — secrets, build output, editor files).

## Message style — the override order

The project's convention wins. Determine it in order:

1. **Documented** — CONTRIBUTING.md, a commitlint/commitizen config, or a
   convention named in CLAUDE.md.
2. **Inferred** — `git log --oneline -20`: if a consistent pattern exists
   (conventional commits, gitmoji, plain imperative, ticket prefixes), match it.
3. **Default** — conventional commits: `type: subject` with type ∈ feat, fix,
   refactor, docs, style, perf, test, chore; subject ≤72 chars, imperative mood;
   body explains what and **why** (never how), wrapped at 72.

Inference guardrail: match the pattern of the *human* commits — don't propagate a
convention that only bot commits follow.

## Hard rules

- **Never push unless explicitly asked.** Committing is local; pushing is
  publishing.
- Don't amend or rebase commits that may already be pushed.
- Commit messages describe the change, not the process ("fix review feedback" says
  nothing — say what changed).
- Use a HEREDOC for multi-line messages:
  `git commit -m "$(cat <<'EOF' … EOF)"`.
