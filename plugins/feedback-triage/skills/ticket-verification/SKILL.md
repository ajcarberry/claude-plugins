---
name: ticket-verification
description: Use when re-checking, fact-checking, or refreshing an already-tracked feedback ticket (FT-NNNN) against its sources — on a /recheck loop or schedule, when asked whether a tracked issue is still open, fixed, or accurately described, or when deciding whether a tracked ticket needs reinvestigation.
---

# Ticket Verification — Keep Tracked Tickets True

Work only on the ticket you were given; change only what evidence shows. New
feedback is intake's job: an untracked report goes in `notes` as a URL, nothing
more.

## Check

1. **Each source:** still exists? open/closed and why? Record in `upstream.states`.
2. **New since the last check** (`verification.last_checked_at`, else
   `created_at`): repro steps, versions, workarounds, "fixed for me", "still broken
   on 2.5", maintainer answers, new +1s/👍.
3. **Fixed?** A merged PR or commit on the base branch that references the issue
   or its error text, or our own `investigation.pr_url` merged. A PR that exists
   but is not merged is not a fix.
4. **Fact-check the ticket:** title still the user problem, summary claims only
   what sources say, type/severity/environment supported.

## Verdicts

| Verdict | When |
|---|---|
| `confirmed` | nothing material changed (silence is not resolution) |
| `corrected` | a field is wrong or stale → `patch` with any of: title, summary, type, severity, environment, labels, component, `plus_ones` (`{ref: [names]}`) |
| `resolved` | fixed on the base branch, or every source closed as completed |
| `needs-reinvestigation` | new info would make the investigation file wrong (repro, cause, tier, recommendation), or a resolved ticket reopened |
| `invalid` | not a bug/feature after all (working as designed and the reporter agreed, spam, wrong product) |

Closed as "not planned"/"won't fix" is a decision, not a fix → `confirmed` with a
note.

## Output

Every verdict lists what was checked; `ft.py` refuses verdicts without evidence.

```json
{"id": "FT-0007", "verdict": "…", "patch": {},
 "upstream": {"states": {"github:acme/app#12": "open"}, "fixed_by": null},
 "notes": "<≤ 2 sentences>", "evidence": ["acme/app#12: open, 2 new comments (2.5 still affected)"]}
```
