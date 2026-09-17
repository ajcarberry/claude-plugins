# oss-triage

Maintainer triage for a public GitHub issue tracker, built from the first Lore OSS triage pass (September 2026). Designed for Claude Code agents: procedures, razors, and quality guards, split into small skills so a session loads only what it needs.

## What it enforces

- **The maintainer holds the send button.** Nothing is posted, closed, labeled, or retitled without an explicit go on the exact draft text.
- **One fresh agent per issue.** The orchestrating session quality-checks reports; it does not evaluate issues itself.
- **Resolved means validated.** The reporter's steps pass on the current release, or on a `main` build when the fix is untagged.
- **Scope is the issue as written.** No code review, no adjacent defects, no spin-off issues.
- **Every draft is adversarially reviewed** before the maintainer sees it, and every summary is live-checked before it is sent.

## Commands

| Command | Use |
|---|---|
| `/oss-triage:setup` | First run in a workspace: write `.oss-triage/config.md`, read the repo's governance files, snapshot labels |
| `/oss-triage:pass` | A full triage pass: snapshot, build once, one agent per issue, verdict list in tiers |
| `/oss-triage:issue <n>` | One issue end to end: validate, draft, review, hand to the maintainer |
| `/oss-triage:reply <n>` | Draft, revise via HITL markers, and post a reply for one issue |
| `/oss-triage:status` | Live-state report of everything the pass touched |
| `/oss-triage:eng-summary` | Build the engineering Slack summary from `FOR-ENGINEERING.md` with a live check per item |

## Skills (loaded by the commands, not all at once)

`triage-core` (hard stops, dispositions, governance), `triage-razors` (roll-ups, mechanism versus need, origin versus vehicle PR, shortcuts), `triage-validation` (repro discipline and agent briefs), `triage-reply` (layouts, voice, review loop, posting), `triage-engineering` (the engineering list and the Slack summary).

## Templates

`templates/` holds the reply layouts, the `FOR-ENGINEERING.md` skeleton, the Slack summary, the pass log, the verdict list, and the workspace config. Commands fill them; they are never posted unfilled.

## Agents

`issue-validator` (Opus), `fact-gatherer`, `adversarial-reviewer`, `live-checker` (Sonnet). Each takes one issue or one draft.

## Workspace layout it expects

```
<work dir>/
  PROCESS.md              local overrides and lessons (wins on conflict)
  FOR-ENGINEERING.md      running list for the dev team
  YYYY-MM-DD-pass.md      one log per pass
  data/<date>/            issue snapshots (fetch-issues.sh)
  repro/<n>/              issue.md, logs, reply-draft.md
  scripts/                repro scripts per issue
```

Repository-specific facts (labels, mirror model, binary cache, build command, community channels) live in `.oss-triage/config.md` in the workspace. `reference/lore-notes.md` is the filled example for EpicGames/lore.
