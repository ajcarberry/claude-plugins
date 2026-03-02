# Claude Plugins

Development workflow plugins for [Claude Code](https://docs.anthropic.com/en/docs/claude-code).

## Plugins

### [docs](plugins/docs/)

Autonomous documentation management with multi-agent review. Detects drift, writes docs, and self-reviews using confidence scoring.

- `/docs` — full autonomous pass: detect gaps, write/update, multi-agent review, fix
- `/docs review <path>` — focused accuracy check against the codebase
- `documentation-standards` skill — Diataxis framework, templates, style guide

### [launchpad](plugins/launchpad/)

Session lifecycle management — workspace setup through PR creation.

- `/stage` — fast workspace setup (worktree + branch + mission brief)
- `/flight-plan` — research, scope, and plan with EARS requirements
- `/commit` — multi-agent review with confidence scoring
- `/land` — commit, docs, push, CI check, and PR creation
- `/write-tests` — behavior-first test patterns

## Installation

Add to your project's `.claude/settings.json`:

```json
{
  "extraKnownMarketplaces": {
    "claude-plugins": {
      "source": {
        "source": "github",
        "repo": "ajcarberry/claude-plugins"
      }
    }
  },
  "enabledPlugins": {
    "docs@claude-plugins": true,
    "launchpad@claude-plugins": true
  }
}
```

For local development, use a directory source instead:

```json
{
  "extraKnownMarketplaces": {
    "claude-plugins": {
      "source": {
        "source": "directory",
        "path": "/absolute/path/to/claude-plugins"
      }
    }
  }
}
```

## License

MIT
