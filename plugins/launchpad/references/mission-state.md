# Mission State — `.claude/mission/` Schema

One directory holds all mission state. Every launchpad command and hook reads and
writes this schema; nothing else is authoritative. The directory lives in the
worktree and is kept out of git via the repo's `info/exclude` (written by `/stage`)
— mission state never lands in a PR.

```
.claude/mission/
├── brief.md            # who/what/why — written by /stage
├── spec.md             # the spec + work packets — written by /mission-plan (optional)
├── log.md              # append-only mission log — shared memory across phases
├── validation-stamp    # "dirty" | "clean <ISO-8601>" — maintained by hooks + validation skill
└── packets/            # per-packet briefs written by /launch (P1.md, P2.md, …)
```

## brief.md

```markdown
---
task: <the user's description, verbatim>
branch: <branch created by /stage>
parent: <base branch>
date: <YYYY-MM-DD>
stakes: low | standard | high
---

# Mission Brief

## Desired Outcome

<1–3 sentences, a measurable end state, not an action. Stay close to the user's
words; do not invent scope.>
```

## spec.md

Format comes from the TPM `spec-authoring` skill (or the project's own template via
the override convention). Whatever the body format, `/mission-plan` appends a
`## Work Packets` section when the work warrants orchestration — packet format in
[orchestration.md](orchestration.md).

## log.md

Append-only. The log — not the conversation — is the source of truth for what
happened; it is what survives compaction and context resets.

```markdown
## <YYYY-MM-DD HH:MM> — <event>
<≤5 lines: what happened, evidence (command + result), what's next>
```

Log at minimum: each packet completed (with evidence), validation runs (pass/fail +
command output summary), self-review verdicts, PR opened, review feedback handled.

## validation-stamp

Single line. `dirty` — an Edit/Write has happened since validation last passed
(written by the PostToolUse hook). `clean <ISO-8601>` — written by the validation
skill, only after all checks pass. Absent = dirty. The PreToolUse gate blocks
push/PR-create/merge while the stamp is not clean.

## Lifecycle

- **`/stage`** creates the directory, writes `brief.md`, adds `.claude/mission/` to
  `$(git rev-parse --git-common-dir)/info/exclude`.
- **`/mission-plan`** adds `spec.md`; may revise `stakes:` in the brief.
- **`/launch`** writes `packets/`, appends to `log.md`.
- **`/orbit`** appends validation/review/PR events to `log.md`.
- **`/land`** archives the directory to the main worktree at
  `.claude/missions/<date>-<branch-slug>/`, then removes the worktree.
