# Commit

The smallest plugin: one command, one skill. Commit quality that works in any
repo — including ones you don't own.

- **`/commit`** — survey the tree, group related changes (splitting unrelated
  ones), write the message in the project's own convention, commit. Flags
  secrets/artifacts before they're staged. Never pushes unasked.
- **`commit-conventions`** (skill) — atomicity rules and the message-style
  override order: documented convention (CONTRIBUTING.md, commitlint) → inferred
  from recent `git log` → conventional-commits default. Invoked standalone by
  launchpad's `/launch` for checkpoint commits.

If this plugin ever needs more than this, it's overcomplicated again.
