# Docs

Documentation as a first-class capability: one command, one skill, a default style
that defers to the project's own.

## Command

**`/docs`** — autonomous documentation pass:
- No arguments: detect gaps from recent changes → write/update → review → fix →
  report
- `review <path>`: focused panel scrutiny of specific docs against codebase
  accuracy, freshness, standards, and completeness

```bash
/docs
/docs review docs/reference/cli.md
```

## Skill

**`writing-docs`** — the skill `/docs` and launchpad's `/launch` invoke:
- **Override convention:** a project `writing-docs` skill or `docs/STYLE.md`
  supersedes the plugin defaults entirely
- Diátaxis type decision (tutorial / how-to / reference / ADR), one purpose per doc
- Default style guide and quality bar: every command, path, and example verified
  against the actual codebase
- Templates: `templates/{tutorial,how-to,reference,adr}.md`

## Principles

- Model-tiered subagents: cheap models scan, standard models write, reviewers
  verify claims against source before reporting.
- The independent-reviewer test filters review noise; "nothing to update" is a
  normal, correct outcome.
- Docs never claim what the code doesn't do — accuracy issues always carry
  evidence (what the doc says vs. what the code shows).
