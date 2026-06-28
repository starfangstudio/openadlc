---
name: migrations
description: "This skill should be used when changing a database schema, \"write a migration\", \"add a column\", \"rename a column\", \"drop a table\", \"change a column type\", \"make this migration safe\", \"zero-downtime schema change\", \"backfill a column\", \"is this migration reversible\", \"add an index without locking\", or reviewing a migration before it ships. Detect-first across Prisma, Drizzle, Knex, Alembic, Flyway, Rails, and Ecto: apply expand-contract so the schema change is backward compatible, reversible, and never locks production. Pairs with schema-design (the model), query-optimization (indexes), and database-reviewer (the review before the operator's outbound yes)."
version: 0.1.0
---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# Migrations

A schema change ships in small, backward-compatible, reversible steps. Old code and new code must both run against every intermediate state, because during a rolling deploy they do. Never a destructive change in one deploy. Never an irreversible step.

## Step 1: Detect the migration tool first
Never impose a tool. Read the project before writing a migration:
- `package.json`, `requirements.txt` / `pyproject.toml`, `Gemfile`, `mix.exs`, or a `flyway.conf` tell you the tool.
- The existing migrations directory tells you the file format and naming. Match it exactly.

| Tool | Up / down |
|------|-----------|
| Prisma | SQL up file; down via `prisma migrate diff` (see Step 5) |
| Drizzle | forward-only SQL; reverse is a new hand-written migration (no `down` yet) |
| Knex | `exports.up` / `exports.down` in one file |
| Alembic | `upgrade()` / `downgrade()` in one revision |
| Flyway | `V__` forward; `U__` undo (paid edition only, so plan a forward revert) |
| Rails | `change` (auto-reversible) or explicit `up` / `down` |
| Ecto | `change/0` (auto-reversible) or explicit `up/0` / `down/0` |

## Step 2: Classify the change as safe or breaking
- **Safe (additive, one step):** add a nullable column, add a table, add a non-unique index (concurrently), add a constraint as `NOT VALID` then validate later. These keep old code working, so they ship alone.
- **Breaking (needs expand-contract):** rename a column, change a type, drop a column or table, add `NOT NULL` to a populated column, add a unique constraint. A breaking change in one deploy locks the table or breaks the running old code. Split it.

If the change is breaking, it is never one migration. It is the sequence in Step 3.

## Step 3: Expand → backfill → switch → contract
Each phase is a separate deploy. Never collapse two phases into one.
1. **Expand:** add the new column/table alongside the old, nullable, no default backfill. Old code ignores it; new code may write it (dual-write). Reversible: drop the new column.
2. **Backfill:** copy old to new in batches, in its own migration, outside the main transaction (so it does not hold a long lock). Idempotent and re-runnable. Reversible: the data still lives in the old column, so revert is a no-op.
3. **Switch:** deploy code that reads the new column. Only after every running instance reads new do you add `NOT NULL` or a unique constraint. Reversible: point reads back at the old column.
4. **Contract:** drop the old column/table, in a later deploy, once nothing references it. This is the only destructive step, and it ships alone after the switch has been stable.

The rename "user_name → username" is four deploys, not one `ALTER ... RENAME`. The rename breaks old code instantly; expand-contract does not.

## Step 4: Keep each step lock-light
A migration that holds a lock on a hot table is downtime even if it is "reversible".
- **Indexes:** build without an exclusive lock. Postgres `CREATE INDEX CONCURRENTLY` (Rails `algorithm: :concurrently` + `disable_ddl_transaction!`; Ecto `@disable_ddl_transaction true` + `@disable_migration_lock true`; Alembic outside the transaction).
- **Columns:** add nullable with no volatile default (a default forces a full-table rewrite on older engines). Set the default in a separate step.
- **Backfill:** batch with `find_each` / `LIMIT` loops, never one `UPDATE` over the whole table.
- **Constraints:** add `NOT VALID`, then `VALIDATE CONSTRAINT` in a later step so the validation scan does not block writes.

## Step 5: Make every migration reversible (write the down)
Write the `down` when you write the `up`, not at 3am during an incident.
- **Knex / Alembic / Rails / Ecto:** implement the explicit reverse. For auto-reversible helpers (Rails `change`, Ecto `change/0`), give the full column type so the framework can reverse a removal.
- **Prisma:** generate the down SQL with `prisma migrate diff --from-schema-datamodel ./prisma/schema.prisma --to-schema-datasource ./prisma/schema.prisma --script > down.sql` and keep it beside the up migration.
- **Drizzle / Flyway Community:** no built-in down, so the "rollback" is a new forward migration that reverses the change. Write and test that revert migration now.
- **The honest exception:** a `DROP COLUMN` destroys data; its `down` re-adds an empty column, not the data. So contract steps (Step 3.4) are the one place down does not restore state, which is exactly why contract ships last and alone, after a stable switch, with a backup taken first.

## Step 6: Verify on a copy, both directions
Never test a migration first on production. Run it against a copy or a disposable container seeded with representative data:
1. Apply the migration. It succeeds.
2. Roll it back (`migrate down` / `rollback` / `downgrade` / the revert migration). It succeeds and leaves a schema equivalent to the start.
3. Re-apply. It still succeeds (idempotent, no drift).

A migration that applies but cannot roll back cleanly is not done.

## References
- The model and keys: `schema-design`. Indexes and query plans: `query-optimization`. The access layer and transactions: `data-access`. The independent pre-merge review of migration safety: `database-reviewer`.
- Tool docs verified for this skill: [Prisma down migrations](https://www.prisma.io/docs/orm/prisma-migrate/workflows/generating-down-migrations), [Prisma expand-contract](https://www.prisma.io/docs/guides/data-migration), [Drizzle migrations](https://orm.drizzle.team/docs/migrations), [Knex migrations](https://knexjs.org/guide/migrations.html), [Alembic zero-downtime](https://that.guru/blog/zero-downtime-upgrades-with-alembic-and-sqlalchemy/), [Flyway undo migrations](https://documentation.red-gate.com/fd/undo-migrations-273973334.html), [strong_migrations](https://github.com/ankane/strong_migrations), [Ecto.Migration](https://hexdocs.pm/ecto_sql/Ecto.Migration.html).

## The check
Pick the change. Apply it to a copy of the database, then roll it back, then re-apply. If all three succeed and the rolled-back schema matches the starting schema, the migration is reversible and the step is done. If the rollback errors or leaves drift, the migration is not safe to ship.
