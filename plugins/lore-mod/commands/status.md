---
description: Live-state report of every issue and PR the current pass has touched — queried now, not from the log
argument-hint: "[date]"
allowed-tools: Bash, Read, Glob, Grep
---

# /lore-mod:status

Load `Skill: lore-mod:triage-core`. Read `.lore-mod/config.md` and the pass log for `$ARGUMENTS` (default: the latest).

1. Collect every issue and PR number mentioned in the pass log and the verdict list.
2. Query each live: state, state reason, labels, title, last comment author and time.
3. Report a table: closed (by whom and when), commented and awaiting close, drafted and awaiting review, kept with labels, running validations. Flag anything closed or commented on by someone else since the log entry.
4. Update the pass log's status line to match.
