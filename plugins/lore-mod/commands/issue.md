---
description: Take one issue end to end — validate on the fixed version, draft the reply from the matching template, adversarially review it, hand the path to the maintainer
argument-hint: "<issue number>"
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, Agent, Skill
---

# /lore-mod:issue

Load `Skill: lore-mod:triage-core`, `Skill: lore-mod:triage-razors`, `Skill: lore-mod:triage-validation`, `Skill: lore-mod:triage-reply`. Read `.lore-mod/config.md` and `<work dir>/PROCESS.md`.

1. Stage the issue: `scripts/stage-issue.sh $ARGUMENTS`. Read the whole thread. Note every contributor with a PR or fix in flight, and every question the reporter asked.
2. Check the live state of every issue and PR referenced in the thread.
3. Decide which agent applies (validator for repro and code history; fact-gatherer for questions) and dispatch it with the brief from `triage-validation`. If a `main` build is needed and none is cached for the current revision, build once first.
4. Quality-check the report per `triage-validation`. Apply the razors.
5. Fill the matching reply template into `repro/<n>/reply-draft.md`. Dispatch `lore-mod:adversarial-reviewer`; apply its fixes.
6. Hand the maintainer: verdict in one line, the evidence that matters, the draft path with `:1`, and the exact mechanics (comment, labels, title, close reason). Post nothing.
