# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Reusable Claude Code plugins that raise the quality and consistency of AI-assisted development projects. The core thesis: agent output quality is proportional to context quality, so these plugins encode proven patterns — research-plan-implement workflows, multi-agent review, structured requirements — as portable, shareable context that any project can adopt.

Two plugins:

- **Launchpad** (`plugins/launchpad/`) — Session lifecycle from workspace setup through PR creation, embodying a research → plan → implement → review workflow. Commands: `/stage`, `/flight-plan`, `/commit`, `/land`.
- **Docs** (`plugins/docs/`) — Autonomous documentation management with multi-agent review. Command: `/docs`.

## Architecture

### Plugin Structure

Each plugin follows this layout:
```
plugins/<name>/
├── .claude-plugin/plugin.json   # Plugin metadata (name, version, description)
├── commands/                    # Slash command specs (YAML frontmatter + markdown)
├── skills/                      # Reusable knowledge modules with SKILL.md + references/
├── agents/                      # Agent definitions (librarian, historian)
├── hooks/                       # Hook definitions (hooks.json + scripts/)
└── README.md
```

The top-level `.claude-plugin/marketplace.json` registers both plugins for discovery.

### Key Design Patterns

**Risk-Scaled Review Pipeline** — Used by `/flight-plan`, `/commit`, and `/land`. Review depth follows the stakes rubric: low stakes get a light inline pass, standard work gets one strong reviewer covering all dimensions, high stakes (auth, payments, migrations, prod infra, destructive ops) get a parallel specialist panel. Concerns are filtered by the independent-reviewer test and classified as blocking or nit. (`/docs` still uses its own inline confidence-scoring pipeline — reconciliation is planned in Phase 6.)

**Requirements Traceability (R/S/V)** — Flight plans use EARS-pattern requirements (REQ-N), implementation steps (S-N), and verification checks (V-N). Every REQ must appear in at least one S and one V.

**Session Context via Hooks** — The `SessionStart` hook (`plugins/launchpad/hooks/`) fires on startup, `/clear`, and compaction. It always injects the flight-rules bootstrap, and when a mission is in progress also loads `.claude/mission-brief.md`, the latest `.claude/specs/*`, `.claude/flight-plan.md`, and `.claude/flight-log.md`, detects branch drift or stale state, and runs background environment initialization.

**Structured Documents** — Mission briefs and flight plans use YAML frontmatter for machine-parseable metadata (task, branch, date, parent).

### Skills

Two kinds — pipeline skills loaded by commands, and **Flight Rules** (discipline skills that auto-invoke during implementation work):
- `documentation-standards` — Diataxis framework, style guide, document templates (ADR, how-to, reference, tutorial)
- `requirements-authoring` — EARS patterns, RFC 2119 priorities (SHALL/SHOULD/MAY), R/S/V traceability — opt-in for high-stakes plans
- `peer-review` — risk-scaled review pipeline, independent-reviewer concern filter
- `stakes-rubric` — shared risk tiers (low/standard/high) that size review depth, gates, and plan format
- `verification-before-completion` — Flight Rule: no completion claim without fresh evidence
- `test-driven-development` — Flight Rule: failing check first (test where a harness exists, observable command where it doesn't); includes test-design + Go references
- `systematic-debugging` — Flight Rule: root cause before remedy, 3-strikes rule
- `browser-verified-web-work` — Flight Rule: web changes verified by loading the page

Iron-Law skills (`verification-before-completion`, `test-driven-development`, `systematic-debugging`) use the full house style — Iron Law, Go/No-Go gate, failure-modes table, red flags — and are validated against the scenarios in `pressure-tests/`. All other skills use a lean format.

## Developing Plugins

This is a plugin development project. Before writing or modifying any plugin component, ensure the right context is loaded:

**Official documentation:**
- [Plugin authoring guide](https://code.claude.com/docs/en/plugins) — canonical reference for plugin structure, commands, agents, skills, hooks, and MCP integration
- [claude-code/plugins](https://github.com/anthropics/claude-code/tree/main/plugins) — source-level examples and specs
- [claude-plugins-official](https://github.com/anthropics/claude-plugins-official) — Anthropic's curated plugin directory

**Official plugins for plugin development** (enable these in `.claude/settings.json`):
- `plugin-dev` — Skills and agents for every plugin component: structure, commands, agents, skills, hooks, MCP, settings. Includes `plugin-validator` and `skill-reviewer` agents.
- `skill-creator` — End-to-end skill creation, evals, and benchmarking
- `claude-md-management` — CLAUDE.md auditing and improvement
- `claude-code-setup` — Codebase analysis and automation recommendations (hooks, subagents, skills, MCP servers)

Use these tools rather than guessing at conventions — they are maintained by Anthropic and reflect current best practices.

## Conventions

- Tool grants enforce separation of concerns — auditors get read-only, writers get read+write, research phases add web access
- Skills auto-invoke on their `description` field — write descriptions as pure trigger conditions (symptoms, keywords, situations), never workflow summaries. Commands may additionally load pipeline skills at fixed workflow points via `Skill:` directives.

## Installation

Add to your project's `.claude/settings.json`:

```json
{
  "extraKnownMarketplaces": {
    "my-plugins": {
      "source": { "source": "github", "repo": "ajcarberry/claude-plugins" }
    }
  },
  "enabledPlugins": {
    "launchpad@my-plugins": true,
    "docs@my-plugins": true
  }
}
```

For local development, use a directory source instead:

```json
{ "source": { "source": "directory", "directory": "/path/to/plugins/launchpad" } }
```
