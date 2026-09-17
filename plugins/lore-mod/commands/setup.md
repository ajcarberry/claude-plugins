---
description: First run in a workspace — write .lore-mod/config.md, read the repo's governance files, snapshot labels, create the work directory skeleton
argument-hint: "<owner/repo> [clone path]"
allowed-tools: Bash, Read, Write, Glob, Grep, AskUserQuestion
---

# /lore-mod:setup

Load `Skill: lore-mod:triage-core`.

1. If `.lore-mod/config.md` exists, read it and stop; say what is configured. Otherwise copy `templates/config.md` to `.lore-mod/config.md` and fill: repository (`$ARGUMENTS`), clone path (clone it if absent), binary cache dir, work dir, maintainer's GitHub handle and display name, community channel link, CLI and server binary names, build command, offline-repository flag if the CLI has one. Ask only for what cannot be derived.
2. Read `GOVERNANCE.md`, `CONTRIBUTING.md`, `MAINTAINERS.md`, `.github/ISSUE_TEMPLATE/*`, `docs/roadmap.md` if present, and `gh api repos/<repo>/labels`. Fill the governance block of the config: who may close, who decides won't-fix, where questions route, Discussions on or off, security path, label list with meanings, roadmap theme slugs.
3. Create the work dir with `PROCESS.md` (from `templates/process.md`), `FOR-ENGINEERING.md` (from `templates/for-engineering.md`), `data/`, `repro/`, `scripts/`. Copy `scripts/fetch-issues.sh`, `scripts/stage-issue.sh`, `scripts/repro-lib.sh` in.
4. Report the config path and anything you could not fill.
