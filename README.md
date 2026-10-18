# Claude Plugins

Development and product workflow plugins for
[Claude Code](https://code.claude.com/docs).

Five plugins, each useful alone. Launchpad is the only one that calls the others —
always optionally, with a stated fallback. feedback-triage is fully self-contained.

## Plugins

### [launchpad](plugins/launchpad/) — dev lifecycle

```
IDEA → /stage → /mission-plan* → /launch → /orbit → /land        (* optional)
```

Worktree + mission brief + stakes tier, spec + work packets, orchestrated or
express implementation, validate → self-review → PR → iterate, merge + cleanup.
Iron-Law flight rules (verification, TDD, systematic debugging) auto-invoke during
implementation; hooks enforce a dirty/clean validation stamp so nothing gets
pushed or merged unvalidated.

### [tpm](plugins/tpm/) — product lifecycle

Signals in, decisions out — built for a TPM/maintainer running an OSS project:

- `/feedback` — Discord/Slack/GitHub signal → ranked themes with evidence; `dig`
  mode investigates flagged themes
- `/triage` — issues/PRs classified against the roadmap; alignment replies drafted
- `/roadmap` — proactive planning or reactive slotting with explicit displacement
- `/spec` — idea → spec; the handoff to launchpad
- `/comms` — community and exec-sponsor updates from the same facts (drafts only)

### [docs](plugins/docs/)

`/docs` (gap detection and repair; focused review mode) + the `writing-docs` skill:
Diátaxis types, a default style guide, and a project override (`docs/STYLE.md`
supersedes).

### [commit](plugins/commit/)

`/commit` + `commit-conventions`: related changes staged together, messages in the
project's own convention (documented → inferred from git log → default), never
pushes unasked.

### [feedback-triage](plugins/feedback-triage/) — feedback to engineering, hands-off

```
/intake → queue → /investigate → /report        (+ /recheck on a loop; /sweep runs all)
```

GitHub issues and Slack channels → a deduplicated, persistent ticket queue (every
place an issue was raised linked to one ticket) → one subagent per ticket, depth
gated by complexity (high: findings · medium: options · low: a reviewed draft PR)
→ a templated, tracker-ready report per ticket (Jira, Linear, GitHub, …) in
ASD-STE100 style, with a proposed fix when one is ready to merge. A stdlib `ft.py` owns the ledger, state machine, lint, and rendering;
hooks block hand-edited queue files, unreviewed PRs, and hand-written reports.

## Global baseline

[`global/`](global/) versions a ~40-line `~/.claude/CLAUDE.md` — surgical changes,
think-before-coding, goal-driven execution — with an installer.

## Installation

Add to your project's `.claude/settings.json`:

```json
{
  "extraKnownMarketplaces": {
    "claude-plugins": {
      "source": { "source": "github", "repo": "ajcarberry/claude-plugins" }
    }
  },
  "enabledPlugins": {
    "launchpad@claude-plugins": true,
    "tpm@claude-plugins": true,
    "docs@claude-plugins": true,
    "commit@claude-plugins": true,
    "feedback-triage@claude-plugins": true
  }
}
```

For local development, use a directory source instead:

```json
{
  "extraKnownMarketplaces": {
    "claude-plugins": {
      "source": { "source": "directory", "path": "/absolute/path/to/claude-plugins" }
    }
  }
}
```

## License

MIT
