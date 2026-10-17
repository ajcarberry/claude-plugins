# Bug Playbook — Reconstruct, Reproduce, Root-Cause

## Reconstruct the incident

Before touching code, write down what happened, from the sources only:

- **Expected vs. actual**, in the reporter's terms.
- **Environment**: version/commit, OS, browser, plan/tier, account type, region.
  Missing? Note it as a gap — don't assume latest.
- **Timeline**: first report date; any later "still happening" or "fixed for me".
- **Steps**: numbered, as stated. Mark steps you inferred.
- **Evidence in hand**: error text, stack traces, screenshots described, logs.

Then look for the circumstances:

- `git log --since=<a week before first report> -- <likely paths>` — a regression
  usually has a recent commit near it. Name the suspect commit if one fits.
- Releases/tags around the first report date.
- Existing issues/PRs mentioning the same error text (`gh search issues "<error>"`
  or the GitHub MCP search). Link what you find.

## Reproduce

Work in the ticket worktree (`worktree.sh create`), never the main checkout.

1. **Smallest faithful repro first**: a unit or integration test that drives the
   failing path with the reporter's inputs. A test is the best repro — it becomes
   the fix's failing check.
2. If no test can reach it, a script or a manual run with exact commands.
3. Record the outcome as one of:
   - `reproduced` — you saw the reported failure. Paste the command and output.
   - `partial` — a related failure, or only under extra conditions you name.
   - `not-reproduced` — list what you tried (version, config, inputs). This is a
     finding, not a failure of the investigation.
   - `not-attempted` — say why (needs prod data, paid service, hardware).
4. Try the reporter's exact version **and** the current base branch: "fixed on
   main already" is a strong finding (recheck will close the ticket when it ships).

## Root cause

Trace back from the failure to the first wrong value or decision. State it as
"`<function>` in `<file>:<line>` does X when Y; it should Z." Distinguish:

- **Root cause** — why it fails.
- **Trigger** — what the user did to hit it.
- **Blast radius** — who else hits it (this sets `reach`).

Not reproduced but the code plainly shows the defect? Say "explained from code,
not reproduced" — that can still support medium.

## Severity → impact

Use the evidence, not the reporter's tone: data loss/corruption, security
exposure, outage, or wrong charges → impact 3; core flow fails with no
workaround → 2; workaround exists → 1; cosmetic → 0.
