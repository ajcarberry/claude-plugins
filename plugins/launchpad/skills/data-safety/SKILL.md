---
name: data-safety
description: Use when writing a database schema migration, altering or dropping tables/columns, running destructive operations on data stores or volumes (DROP, DELETE without WHERE, rm on data dirs, volume removal), or deploying changes that touch persistent state — before executing any of it.
---

# Data Safety

Code mistakes revert with git. Data mistakes don't. Everything touching persistent
state gets a reversal path *before* it runs.

## Migrations

- **Up and down written together.** A migration without a tested rollback is half a
  migration. If down is genuinely impossible (irreversible data transform), that gets
  stated explicitly and approved by the user before applying.
- **Test against a copy first.** Run up → verify schema/data → run down → verify
  restored — on a copy, a scratch DB, or a local container. Never first-run a
  migration against the only copy of the data.
- **Destructive migrations** (dropping columns/tables, type narrowing, mass updates)
  are high-stakes per the stakes rubric: expand-migrate-contract beats drop-in-place
  when the system is live.

## Destructive Operations — the Backup Gate

Before any operation that deletes or overwrites persistent state (DB, volumes, data
directories, object stores):

1. **Snapshot or dump first** — `pg_dump`, volume snapshot, `cp -a`, whatever the
   store supports. Verify the backup exists and is non-empty.
2. **State the blast radius** — what is affected, and what restores it.
3. **Typed confirmation from the user** for irreversible steps. Never auto-proceed.

## Red Flags — STOP

- A migration file with an empty or `raise NotImplementedError` down.
- `DELETE`/`UPDATE` without a `WHERE`, or a `WHERE` you haven't tested with `SELECT`.
- "The backup probably exists" — verify it, freshly (`verification-before-completion`).
- Testing a migration in production because "it's a small one".

## When NOT to Use

Stateless code, config that can be re-applied from git, throwaway local databases.
