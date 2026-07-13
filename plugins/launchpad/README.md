# Launchpad

The dev lifecycle: five phases, one mission-state directory, deterministic
enforcement via hooks. Launchpad orchestrates; reusable knowledge lives in the
companion plugins (`tpm`, `docs`, `commit`), each optional with a stated fallback.

## Lifecycle

```
IDEA → /stage → /mission-plan* → /launch → /orbit → /land
       worktree   spec + work     implement  validate,  merge,
       + brief    packets         (packets   self-review, archive,
       + stakes                   or express) PR, iterate  cleanup

* optional — skip it and /launch works straight from the brief (the express lane)
```

- **`/stage`** — branch + worktree + `.claude/mission/brief.md` (task, base,
  stakes tier) in ~15 seconds. Background baseline test run.
- **`/mission-plan`** — for complex work: spec via the TPM `spec-authoring` skill,
  decomposed into work packets for orchestration. Output: `.claude/mission/spec.md`.
- **`/launch`** — implementation only. Spec with packets → fresh subagent per
  packet with model tiering and asymmetric verification; otherwise express mode in
  the main session. Flight rules apply throughout. Checkpoint commits; docs check
  near the end.
- **`/orbit`** — re-enterable. First run: validate → self-review → push → CI → PR.
  Later runs: fetch review feedback, verify before implementing, fix, re-validate,
  push.
- **`/land`** — gate (CI, reviews, clean stamp), merge (`high` stakes requires
  explicit human confirmation), archive mission state, remove worktree.

## Skills

- **`validation`** — what "validated" means. Defers entirely to a project
  `validation` skill or `.claude/validation.md` when present; writes the stamp
  clean only after every check passes.
- **`self-review`** — fresh-context whole-change review before the PR, depth
  scaled by stakes; independent-reviewer filter; blocking vs. nit.
- **Flight rules** (auto-invoke during implementation):
  `verification-before-completion`, `test-driven-development`,
  `systematic-debugging` — Iron-Law format (law, Go/No-Go gate, failure modes).

## Hooks — skills teach, hooks enforce

State: `.claude/mission/validation-stamp` (`dirty` | `clean <timestamp>`).

| Hook | Behavior |
|---|---|
| `SessionStart` | Inject flight-rules bootstrap; during a mission also brief + spec + log, branch-drift and staleness warnings, background `.claude/session-init.sh` |
| `PostToolUse` (Edit/Write/NotebookEdit) | Mark the stamp dirty (edits under `.claude/` exempt) |
| `PreToolUse` (Bash) | Block `git push` / `gh pr create` / `gh pr merge` while the stamp isn't clean. Escape hatch: `LAUNCHPAD_SKIP_GATE=1` |

Hooks make deterministic file checks only — judgment lives in skills.

## References

- `references/mission-state.md` — the `.claude/mission/` schema all commands share
- `references/stakes.md` — the risk rubric and what each tier changes
- `references/orchestration.md` — work-packet format, model tiering, dispatch loop

## Conventions

The override convention: every skill with a default checks for a project-specific
definition first (a same-named project skill or a documented file) and defers to it
entirely. Mission state stays out of git via the repo-local `info/exclude`; landed
missions archive to `.claude/missions/<date>-<branch>/` in the main worktree.
