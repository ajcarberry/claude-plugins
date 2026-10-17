# Complexity — Assess Once, Gate the Work

Complexity decides how far an investigator goes. It is set once, at the end of
the triage step, and stored as `complexity.tier` with a one-sentence rationale.
Nobody re-litigates it downstream.

| Tier | Investigator stops after | Report says |
|---|---|---|
| **high** | triage + research: what is known, what is not, why it is high | 🧠 Needs eng |
| **medium** | + root-cause (bug) or design (feature) research, **≥ 2 options** with trade-offs and one recommendation | 🧭 Options ready |
| **low** | + branch, implementation, tests, independent review, change request | 🔧 PR ready (🌿 Fix on branch when no PR is opened) |

## Classification rules

Check in order; the first match wins.

1. **High list → high**, regardless of size: auth/permissions, payments/billing,
   security or privacy (incl. user data leaving the device), data migrations or
   deletion, public API/SDK contract changes, infrastructure/deploy config, a new
   hosted service or storage backend, anything that needs a product or
   pricing decision from more than one person.
2. **Cause unknown → high.** A reported problem you could not reproduce *and*
   could not explain from code/logs after the time-box — bug, performance, or a
   "make X faster/better" request alike. Re-framing it as a feature does not
   escape this rule: nobody can build options for a problem nobody can see.
   (Not reproduced but explained from code is fine — classify on the explanation.)
3. **Low only if all hold:**
   - Bug: reproduced, with a failing check you can write. Feature: acceptance
     criteria are unambiguous from the request itself — no open product question.
   - The change stays inside one module, ~1–3 files, roughly ≤ 100 changed lines
     including tests.
   - The existing test harness covers it — no new infra, fixtures service, or
     environment.
   - No behaviour change for users who did not ask for it.
4. **Otherwise medium.**

**Classify the request as asked.** Tier the smallest version that solves the
user's job — not a cheaper scope you would prefer. If that version is on the high
list (a hosted service, data leaving the device, a migration), the ticket is
high; your cheaper alternative goes in the findings as a suggestion.

**Open questions count only if they change what gets built or for whom.** Details
an engineer settles in code review with a conventional default — field names,
flag spelling, JSON shape mirroring existing output — do not block low.

**Between low and medium, choose medium.** A wrong "low" spends reviewer time on a
PR nobody should merge; a wrong "medium" costs one engineer reading two options.
(This is the opposite default to a stakes rubric — here "low" means *act
autonomously*, so it must be earned.)

## Moving a tier

- Research may **raise** a tier (the "one-file fix" touches the auth middleware).
  Raise it, say why in the rationale, and stop at the new tier's boundary.
- Only the change-reviewer **lowers** autonomy: a low-tier change that fails
  review twice becomes medium (`ft.py review --downgrade`), and the attempted diff
  becomes one of the options.
- Never lower a tier to reach the PR step.

## Rationale format

One sentence naming the deciding rule: *"Low: reproduced; fix is a missing null
check in `auth/refresh.ts` with a unit test."* · *"High: touches session tokens
(high list)."* · *"Medium: two valid approaches — client retry or server
grace window."*
