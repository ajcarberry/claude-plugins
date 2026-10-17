# Spiciness — How Much Engineering Attention a Ticket Deserves

Spiciness is computed, not chosen. The investigator scores two factors from
evidence; `ft.py` derives two more from the queue and does the arithmetic. The same
facts always give the same pepper count.

## Factors

| Factor | 0 | 1 | 2 | 3 | Set by |
|---|---|---|---|---|---|
| **impact** (bug) | cosmetic | annoying, workaround exists | a core flow fails, no workaround | data loss, security, outage, money | investigator |
| **impact** (feature) | nice to have | quality-of-life | unblocks a real workflow | blocks adoption or a deal; strategic | investigator |
| **reach** | one user | a few users / one account | a segment (a plan, a platform, a region) | most or all users | investigator |
| **momentum** | 1 reporter | 2–3 distinct reporters | 4+ distinct reporters | — | ft.py (authors + plus-ones across sources) |
| **readiness** | — | low-tier change passed review | — | — | ft.py |

```
score = 2 × impact + reach + momentum + readiness        (0–12)
level = 1 (0–3) · 2 (4–6) · 3 (7–9) · 4 (10–12)
floor: impact 3 → level ≥ 3
bump:  ±1 level, only with a written bump_reason (recorded in history)
```

| Level | Theme | Meaning for the eng team |
|---|---|---|
| 1 | 🌶️ Mild | Read when you have a minute. |
| 2 | 🌶️🌶️ Medium | Worth a look this week. |
| 3 | 🌶️🌶️🌶️ Hot | Plan it into the next sprint or review the PR today. |
| 4 | 🌶️🌶️🌶️🌶️ Inferno | Look now. |

Emoji and labels live in `templates/slack/theme.json` (project override:
`.claude/feedback-triage/theme.json`).

## Scoring discipline

- Score **evidence, not adjectives.** "URGENT!!!" in a report is not impact 3; a
  stack trace showing writes lost is.
- Unknown reach → score what you can show (usually 1) and say so in the
  findings. Never round up to be safe — the floor already protects the
  catastrophic cases.
- Use a bump only for something the formula cannot see: a named enterprise
  customer, a public social-media thread, a regression in the release that
  shipped today. Write the reason as a fact.
- Momentum updates by itself when intake links new duplicates, so a ticket gets
  spicier as more people raise it, and the next report says so.
