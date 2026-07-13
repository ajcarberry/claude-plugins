---
name: writing-docs
description: Use when writing or updating documentation — tutorials, how-to guides, reference docs, ADRs — when checking whether a code change needs doc updates, or when applying a documentation style guide or the Diátaxis framework.
---

# Writing Docs — Types, Style, and the Override Rule

## Override convention (check first)

The project's style supersedes this skill's defaults. Before writing, look for, in
order:

1. A project skill named `writing-docs` (`.claude/skills/writing-docs/`)
2. `docs/STYLE.md` in the project

If either exists, **defer to it entirely** for style and structure — this skill
then only contributes the type decision (below). If neither exists, the defaults
here apply.

## Pick the type first (Diátaxis)

Every doc serves ONE purpose — decision tree, characteristics, and structure in
[reference/diataxis-framework.md](reference/diataxis-framework.md):

- **Tutorial** — learning-oriented, verification at each step
- **How-to** — task-oriented, prerequisites and troubleshooting
- **Reference** — information-oriented, tables and specifications
- **ADR** — a decision with alternatives and consequences

Templates for each in [templates/](templates/). A doc trying to be two types
becomes two docs.

## Default style

Full rules in [reference/style-guide.md](reference/style-guide.md). The
non-negotiables: every command, path, and config example verified against the
actual codebase before it goes in a doc; active voice, no marketing language;
docs indexed in `docs/README.md` when one exists.

## When invoked from a code change (e.g. `/launch`)

Scope to the change: does it alter user-facing behavior, commands, config, or
APIs? If yes, update the affected docs (or flag the gap if the doc doesn't exist).
If no — internal refactors, tests, tooling — "nothing to update" is the correct
outcome; say it and stop. Don't invent documentation work.
