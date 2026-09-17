---
description: Run a full triage pass — snapshot open issues, build main once if needed, one agent per issue, quality-check, produce the tiered verdict list for the maintainer
argument-hint: "[oldest|newest] [limit N] [label:<name>]"
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, Agent, Skill
---

# /oss-triage:pass

Load `Skill: oss-triage:triage-core`, `Skill: oss-triage:triage-razors`, `Skill: oss-triage:triage-validation`. Read `.oss-triage/config.md` and `<work dir>/PROCESS.md`.

1. **Snapshot.** `scripts/fetch-issues.sh` into `data/<date>/`. Default order oldest first; honour `$ARGUMENTS`.
2. **Governance.** Do the once-per-session governance read from `triage-core` and record it in a new `<date>-pass.md` from `templates/pass-log.md`.
3. **Build once.** If the candidate set may include untagged fixes, build `main` now per `triage-validation`, before any agent is dispatched.
4. **Dispatch, one agent per issue.** Stage each issue with `scripts/stage-issue.sh <n>`. Run `oss-triage:issue-validator` for bug reports and anything with a repro; `oss-triage:fact-gatherer` for questions and feature requests. Serialize agents that need the server ports. Each agent gets the issue file, the clone, the binaries, the scope rule, and the report format.
5. **Quality-check every report** per `triage-validation`: hashes, tags, quoted lines, live state of every referenced issue and PR, links and anchors. Apply the razors to roll-ups and mixed proposals.
6. **Verdict list.** Fill `templates/verdicts.md` into `data/<date>/verdicts.md` in three tiers: mechanical closes (evidence is a commit, a doc, or an empty body), answer-and-close, decisions for maintainers or the steering group. Keeps are grouped by what they need next (close on PR merge, close on release, needs info, volunteers waiting, LEP-shaped, roadmap theme).
7. **Report** to the maintainer: counts, the verdict path with `:1`, the first tier's items with proposed comments, and anything that needs a policy call. Post nothing.
8. Update `FOR-ENGINEERING.md` candidates and the pass log.
