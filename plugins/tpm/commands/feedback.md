---
description: Aggregate raw community feedback into ranked themes with evidence — or dig into a flagged theme
argument-hint: "[sources/paths] | dig <theme>"
allowed-tools: Bash, Read, Write, Glob, Grep, Task, Skill, WebFetch, ToolSearch, AskUserQuestion
---

# Feedback — Signal to Themes

Load `Skill: tpm:feedback-synthesis` first — it owns the clustering, evidence, and
dig discipline. This command handles intake and output.

## Mode: Dig (`/feedback dig <theme>`)

Read the latest themes doc, find the named theme, and run the skill's dig: search
the full available history for related reports, read connected issues/PRs, read the
relevant code. Append the findings note to the themes doc's "Digs completed"
section, flip the theme's status to `dug`, and state the recommendation (roadmap
item / spec / close as understood). **STOP** — routing the finding is `/roadmap`'s
or `/spec`'s move.

## Mode: Aggregate (default)

### Step 1: Identify Sources

In order, take what's available — never block on a missing source:
- Paths in `$ARGUMENTS` (exports, CSVs, notes)
- Connected MCP tools for Discord/Slack (discover via ToolSearch; skip if absent)
- `gh` for GitHub discussions and recent issues (skip if unavailable)

Big source lists → dispatch parallel reader subagents, one per source, each
returning candidate problems + verbatim quotes + refs (≤20 lines each). Small ones
→ read directly. Tell the user what's being covered and what isn't.

### Step 2: Synthesize

Cluster per the skill: by user problem, quotes preserved, every theme cited and
counted, severity tracked separately from frequency, `needs-dig` flagged per the
skill's test.

### Step 3: Write and Report

Write to `docs/feedback/<YYYY-MM-DD>-themes.md` using the
[feedback-themes template](../templates/feedback-themes.md) (project-declared
location supersedes). Report a compact summary:

```
Feedback synthesized → docs/feedback/<date>-themes.md
  Sources:   <covered> (not covered: <gaps>)
  Themes:    <N> (<M> flagged needs-dig)
  Top three: <name — severity/frequency one-liners>

  Dig a flagged theme:      /feedback dig <theme>
  Route themes to planning: /roadmap
```

## Error Handling

| Scenario | Action |
|----------|--------|
| No sources found at all | Say exactly what was looked for; ask for a path or export |
| Named theme not found (dig) | List available themes, stop |
| MCP/`gh` unavailable | Proceed with remaining sources, note the gap in the doc |
