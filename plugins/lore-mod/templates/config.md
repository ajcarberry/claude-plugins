# lore-mod workspace config

Filled by `/lore-mod:setup`. Read by every command. Keep it short and factual.

## Repository
- repo: `<owner>/<repo>`
- clone: `<absolute path to a git clone of main>`
- default branch: `main`
- cache dir: `~/.cache/<repo>-triage` (tags under `<cache>/<tag>/`, main build under `<cache>/main/` with `REV`, kits under `<cache>/kits/<issue>/`)
- work dir: `<absolute path to the triage work directory>`

## Binaries and build
- CLI binary: `<name>`; server binary: `<name>`
- release asset pattern: `<cli>-<tag>-<triple>.tar.gz`
- build command for main: `<cargo/make/... command that produces both binaries>`
- offline repository flag: `<flag or "none">`
- server ports: `<list>`

## People and channels
- maintainer handle: `@<github>`; display name: `<name>`
- steering or triage group: `<names>`
- community channel: `<Discord invite or Discussions link>`, support channel `#<name>`, feature channel `#<name>`, show-and-tell `#<name>`
- security path: `<HackerOne or email>`
- Slack summary audience: `#<channel>`; owner handles: release owner `@<slack>`, build owner `@<slack>`

## Governance (from the repo's files, date read: YYYY-MM-DD)
- who may close: 
- who decides won't-fix on design / on scope: 
- questions route to: 
- Discussions enabled: yes/no
- labels (name: meaning): 
- roadmap theme slugs (from the roadmap page anchors): 
- mirror model (if PRs land via import): 
