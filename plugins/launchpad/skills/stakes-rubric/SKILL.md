---
name: stakes-rubric
description: Use when deciding how much review, planning, or confirmation ceremony a change needs — choosing review depth or agent count, deciding whether a plan needs full requirements treatment, or whether an action needs explicit confirmation before proceeding.
---

# Stakes Rubric — Ceremony Scales with Risk

One shared rubric so every launchpad command sizes its process the same way. Ceremony
follows **stakes**, never habit.

## Tiers

| Tier | Typical changes | Review | Gates | Plan format |
|---|---|---|---|---|
| **Low** | Content, docs, comments, cosmetic UI, formatting | None, or one lightweight pass | Auto-proceed | Small format (changes + checks) |
| **Standard** | Typical feature work, bug fixes, refactors | One strong reviewer | Confirm before commit/PR | Plain plan with V-checks |
| **High** | Auth, payments, secrets, schema/data migrations, prod infra, destructive or irreversible ops, very large diffs | Full specialist panel | Hard gates; typed confirmation for destructive steps | Plain plan + optional EARS requirements |

## Classification Rules

- Anything on the **high list is high** — no judgment call, regardless of diff size.
  A one-line auth change is high stakes.
- Between low and standard, **choose low**. Under-ceremony on a blog post costs
  nothing; over-ceremony costs the user tokens and patience.
- Stakes can rise mid-task (a "cosmetic" change turns out to touch the login form).
  Re-classify and say so.
- Mixed diffs take the tier of their riskiest part.

## What the Tier Controls

- **Review depth** — see `peer-review`: none/light → single reviewer → panel.
- **Confirmation gates** — auto-proceed → ask once → hard gate with typed
  confirmation for destructive actions.
- **Plan format** — small task format → plain plan → plain plan with optional EARS
  (see `requirements-authoring`).
- **Model tiering** — mechanical work on cheap models; strongest model reserved for
  high-stakes review and architecture.
