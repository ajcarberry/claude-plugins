---
name: documentation-standards
description: This skill should be used when writing documentation, creating tutorials, writing how-to guides, building reference docs, drafting ADRs, applying the style guide, checking documentation quality, or structuring docs according to Diátaxis. Provides the project's documentation framework, templates for each document type (tutorial, how-to, reference, ADR), style guide rules, quality criteria, and file naming conventions.
---

# Documentation Standards

Project documentation follows the Diataxis framework with ADRs for decision records.

## Reference Files

- **[Diataxis Framework](${CLAUDE_PLUGIN_ROOT}/skills/documentation-standards/reference/diataxis-framework.md)** — Document types, decision tree, type characteristics, templates
- **[Style Guide](${CLAUDE_PLUGIN_ROOT}/skills/documentation-standards/reference/style-guide.md)** — Writing rules, formatting, file naming, quality checklist

## Templates

Use the templates in `${CLAUDE_PLUGIN_ROOT}/skills/documentation-standards/templates/` for each type:
- `tutorial.md` — Learning-oriented with verification at each step
- `how-to.md` — Task-oriented with prerequisites and troubleshooting
- `reference.md` — Information-oriented with tables and specifications
- `adr.md` — Decision record with alternatives and consequences

## Agent Pipeline

The librarian agent detects documentation issues; the historian agent resolves them. The librarian owns standards and accountability; the historian owns the craft of writing.

## Documentation Index

All docs are indexed in `docs/README.md`. Update it when adding new documents.

## Role Documentation

Role reference docs live in `docs/reference/roles/`, NOT in role READMEs. Each role has a minimal README pointing to central docs.
