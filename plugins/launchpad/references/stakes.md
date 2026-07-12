# Stakes — Assess Once, Store as State, Consume Cheaply

Risk is a one-line property of the mission, set by `/stage` (revisable by
`/mission-plan`), stored as `stakes:` in `.claude/mission/brief.md`. Downstream
consumers read the field; nobody re-litigates risk mid-mission.

## Tiers

| Tier | Typical changes |
|---|---|
| **low** | Content, docs, comments, cosmetic UI, formatting |
| **standard** | Typical feature work, bug fixes, refactors |
| **high** | Auth, payments, secrets, schema/data migrations, prod infra, destructive or irreversible ops, very large diffs |

## Classification rules

- Anything on the **high list is high** — no judgment call, regardless of diff size.
  A one-line auth change is high stakes.
- Between low and standard, **choose low**. Under-ceremony on a blog post costs
  nothing; over-ceremony costs tokens and patience.
- Stakes can rise mid-task (a "cosmetic" change turns out to touch the login form).
  Re-classify, update the brief, and say so.
- Mixed changes take the tier of their riskiest part.

## What the field controls

| Consumer | low | standard | high |
|---|---|---|---|
| `validation` skill | default checks | default checks | default checks + exercise the risky surface directly; back up before anything destructive |
| `self-review` skill | quick inline pass | one fresh-context reviewer | + second reviewer with a security/data lens |
| `/land` | merge on GO | merge on GO | explicit human confirmation before merge |
| Model tiering | cheap models fine throughout | per orchestration reference | strongest model for review and architecture |
