# Docs Plugin

Autonomous documentation management for the homelab monorepo.

## Components

### Agents

**Librarian** — Owns project documentation. Detects drift, enforces standards, delegates writing to the Historian. Triggers proactively after significant code changes.

**Historian** — Technical writer. Creates and updates documentation following Diátaxis framework. Concise, accurate, clear. Triggers when docs need writing or updating.

### Command

**`/docs`** — Autonomous documentation workflow:
- No arguments: detect gaps → write/update → review → fix → finalize
- `review <path>`: focused panel scrutiny of specific docs against codebase accuracy

### Skill

**documentation-standards** — Diátaxis framework reference, templates, style guide, and quality criteria. Auto-activates when working with documentation.

## Usage

```bash
# Full autonomous pass — detect and fix all documentation issues
/docs

# Review specific doc(s) for accuracy
/docs review docs/reference/cli.md
/docs review docs/guides/
```

## How It Works

The `/docs` command uses risk-scaled review (same pattern as launchpad's peer-review skill):

1. **Triage** — Scan recent git changes
2. **Gap analysis** — Librarian identifies what's missing or stale
3. **Resolve** — Historian writes or updates docs
4. **Review** — One reviewer covering accuracy, standards, and completeness (parallel reviewers for 3+ docs; a panel in `review <path>` mode)
5. **Filter** — The independent-reviewer test drops anything another qualified reviewer wouldn't flag
6. **Fix** — Historian addresses surviving issues
7. **Finalize** — Report what was created/updated

## Documentation Structure

See [Diataxis framework reference](skills/documentation-standards/reference/diataxis-framework.md) for document types, decision tree, and type characteristics.
