---
name: triage-validation
description: Repro discipline for validating a reported fix or behaviour: session setup, build-once rule, environment isolation, what the validator agent must report, and the quality checks the orchestrator runs on the report. Load when any issue is a resolved or invalid candidate.
---

# Triage validation

## Session setup, once

- Pull the clone named in `.lore-mod/config.md`. Snapshot open issues with `scripts/fetch-issues.sh`.
- Tagged release binaries go under the cache dir, one folder per tag. Download on first need; keep them.
- If any candidate fix is untagged, build `main` **once**, before dispatching agents, with the build command from the config; copy the binaries into `<cache>/main/` and write the short revision to `<cache>/main/REV`. Never compile per issue. The target directory persists, so the next session's rebuild is incremental.
- Reporter kits and large downloads go under `<cache>/kits/<issue>/`, never inside the work directory. Leave a `KIT_LOCATION.txt` pointer in `repro/<n>/`.

## Dispatch

Stage the issue (`scripts/stage-issue.sh <n>` writes `repro/<n>/issue.md` with body and all comments). Dispatch `lore-mod:issue-validator` with: the issue file, clone path, binary paths, the scope rule, the read-only rule, the reference reply layout, and the report format. Offline repositories (`lore repository create --offline`) need no server and do not collide; when a server is needed, only one validation at a time uses the ports.

## Environment rules the validator must follow

- Fresh `HOME` and `TMPDIR` per run. The CLI keeps user-level state under the OS application-support directory, and a newer client has rewritten state an older client then could not read.
- Start a server as `(cd "$WORK" && exec <server>) &` so `$!` is the real PID; check port ownership after every start. Killing a wrapper subshell orphans the server and the next run talks to a ghost.
- Unique repository name per run. Stop by binary path (`pkill -f "$BIN/<server>"`) and wait for the ports to free.
- Record `<cli> --version` first, every command with output and exit code, and `RUST_BACKTRACE=1` or the equivalent where a crash is expected.
- Log to `repro/<n>/<tag>.log`. Never delete a prior log; copy it aside.

## What the report must contain

Verdict line (RESOLVED / NOT RESOLVED / CANNOT REPRODUCE / DOCUMENTED BEHAVIOUR / EXISTS / BLOCKED); versions and platform; the reporter's exact steps as run and any adaptation; quotable output blocks; fix commit facts (`git log -1`, `git tag --contains`); deviations from the reporter's conditions and threats to the conclusion. For long runs, a "what was run" paragraph a stranger can follow.

## Quality checks you run on every report

- Every cited hash exists and its tags match.
- Every quoted output line is in the log.
- Every referenced issue and PR is checked live.
- Every link resolves and every anchor exists (`/usr/bin/curl -sL <url> | grep 'id="<anchor>"'`; in zsh, split strings with `read -r` or `${a%%|*}`).
- The claim is no broader than the run: a flat-directory proxy does not validate a directory-recursion fix; a 4 GB run does not validate a 600 GB report. Say which part it covers.
