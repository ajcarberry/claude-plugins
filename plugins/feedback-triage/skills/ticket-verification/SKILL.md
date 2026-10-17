---
name: ticket-verification
description: Use when re-checking, fact-checking, or refreshing an already-tracked feedback ticket (FT-NNNN) against its sources — on a /recheck loop or schedule, when asked whether a tracked issue is still open, fixed, or accurately described, or when deciding whether a tracked ticket needs reinvestigation.
---

# Ticket Verification — Keep Tracked Tickets True

Recheck keeps the queue honest between intake runs. It works **only on tickets
that already exist** and it changes **only what the evidence shows**. Finding new
feedback is intake's job, not this one: if you see an untracked report, mention
its URL in `notes` and stop there.

## What to check, per ticket

1. **Every source still exists and its state.** GitHub issue open/closed (and the
   close reason), Slack thread still there. Record each in `upstream.states`.
2. **New information on the sources since the last check:** repro steps, versions,
   workarounds, "fixed for me", "still broken on 2.5", a maintainer answer.
3. **Fixed upstream?** A merged PR or commit that references the issue or its
   error text; a release note naming it; our own `ft/<ID>-*` PR merged.
   Confirm the fix reached the base branch — "a PR exists" is not "resolved".
4. **Fact-check the ticket against the sources:** does the title still state the
   user problem? Does the summary claim anything the sources don't say? Is the
   type right? Are severity/environment supported?

## Verdicts

| Verdict | When | Effect |
|---|---|---|
| `confirmed` | nothing material changed | timestamps the check |
| `corrected` | a ticket field is wrong or outdated | `patch` applied (title, summary, severity, environment, labels, component only) |
| `resolved` | fixed on the base branch, or every source closed as fixed/completed | ticket closes; next digest announces it |
| `needs-reinvestigation` | new info that changes the repro, root cause, tier, or recommendation — or a resolved ticket reopened | ticket returns to the investigation queue |
| `invalid` | sources show it is not a bug/feature (working as designed *and* the reporter agreed, spam, wrong product) | ticket closes |

- A source closed as "not planned" / "won't fix" is **not** `resolved` — it is a
  decision; `confirmed` with a note, so the team sees it.
- Silence is not resolution. No activity for months → `confirmed`.
- When in doubt between `confirmed` and `needs-reinvestigation`, ask: would the
  investigation file give a wrong answer now? Only then reinvestigate.

## Evidence

Every verdict lists what was checked: `["acme/app#12: open, 2 new comments
(v2.5 still affected)", "searched merged PRs for 'refresh token': none"]`. `ft.py`
refuses verdicts without evidence and refuses patches to any other field.

## Verdict JSON

```json
{"id": "FT-0007", "verdict": "confirmed|corrected|resolved|needs-reinvestigation|invalid",
 "patch": {"summary": "..."},
 "upstream": {"states": {"github:acme/app#12": "open"}, "fixed_by": "<url or null>"},
 "notes": "<≤ 2 sentences>", "evidence": ["..."]}
```
