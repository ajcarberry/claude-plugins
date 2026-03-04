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

**Multi-Agent Review Pipeline** — Used by `/flight-plan`, `/commit`, `/land`, and `/docs`. Parallel specialist agents review along different dimensions, each producing confidence-scored concerns. Only concerns scoring 80+ survive filtering. Concerns are classified as blocking or non-blocking.

**Requirements Traceability (R/S/V)** — Flight plans use EARS-pattern requirements (REQ-N), implementation steps (S-N), and verification checks (V-N). Every REQ must appear in at least one S and one V.

**Session Context via Hooks** — The `SessionStart` hook (`plugins/launchpad/hooks/`) loads `.claude/mission-brief.md` and `.claude/flight-plan.md` into session context, detects branch drift or stale state, and runs background environment initialization.

**Structured Documents** — Mission briefs and flight plans use YAML frontmatter for machine-parseable metadata (task, branch, date, parent).

### Skills

Skills encapsulate domain knowledge as reference material:
- `documentation-standards` — Diataxis framework, style guide, document templates (ADR, how-to, reference, tutorial)
- `requirements-authoring` — EARS patterns, RFC 2119 priorities (SHALL/SHOULD/MAY), R/S/V traceability
- `peer-review` — Review pipeline structure, confidence scoring rubric
- `write-tests` — Three-layer testing strategy, table-driven tests, Go-specific patterns

### Confidence Scoring

Scale: 0 (false positive) → 25 → 50 → 75 → 100 (certain). Threshold for action: **80+**.

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
- Assume that skills do not auto-load; indicate explicit commands to pull them in at specific workflow points via `Skill:` directives

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
