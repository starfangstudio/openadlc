---
name: data-layer
description: >-
  This skill should be used when the user asks to "set up the database", "design the schema",
  "add a migration", "run a migration", "add an index", "set up Flyway", "choose an ORM",
  "add a cache", "add Redis", "add a read replica", "set up the query layer", "fix a slow
  query", "design the persistence layer", "model the data", "set up transactions", "pick
  an isolation level", or "structure the data layer". Designs and implements the solo-scale
  persistence layer for a Kotlin/Ktor (or Go/Node) backend: PostgreSQL as the default
  relational store, versioned forward-only migrations via Flyway, typed query layer (Exposed
  DSL or jOOQ), correct transaction isolation, and a disciplined opt-in path to Redis or a
  read replica. Explicitly rejects premature sharding, NoSQL, and microservice-per-DB patterns.
version: 0.1.0
---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# data-layer

Design and implement the persistence layer: PostgreSQL, Flyway migrations, a typed query
layer, and disciplined decisions around caching and replicas. Solo-scale first; reject
premature distributed-systems complexity.

**Boundary with `adlc-database`:** the general, detect-first data domain (schema design,
migrations, query optimization, and the data-access layer across any engine and ORM) lives
in `adlc-database`; route general data work there. This skill is the backend's *opinionated
solo-scale stack*: PostgreSQL + Flyway + a typed Kotlin/Ktor query layer, the game-backend
table shapes, and the service-side data integration. On NoSQL the two differ on purpose:
this solo-scale backend rejects NoSQL as a primary store, while `adlc-database` covers NoSQL
when a project genuinely needs it.

## Step 1: Detect first -- never impose

Before designing anything, inspect what already exists:

```bash
# Existing migration files
find . -name "V*.sql" | sort

# ORM / query library in use
grep -rE "exposed|jooq|ktorm|hibernate|r2dbc|slick" build.gradle.kts settings.gradle.kts 2>/dev/null
grep -rE "gorm|sqlx|pgx|database/sql" go.mod 2>/dev/null
grep -rE "prisma|drizzle|pg|knex" package.json 2>/dev/null

# Migration tool
grep -rE "flyway|liquibase" build.gradle.kts 2>/dev/null

# Existing DB DSN / connection config
grep -rE "JDBC_URL|DATABASE_URL|PG_HOST|DB_HOST" .env* src/**/*.{kt,go,ts,env} 2>/dev/null

# Any Redis usage already present
grep -rE "jedis|lettuce|redis4cats|go-redis|ioredis" build.gradle.kts go.mod package.json 2>/dev/null
```

Record what is found. Mark anything not found as `unknown`. Never change an existing
migration tool, ORM, or DB engine without an explicit operator request.

## Step 2: PostgreSQL schema design

PostgreSQL is the default. Use it unless the project already runs on something else.

Principles:
- One schema per application. No multi-tenant schema-per-tenant until there is a real
  need and a measured row count that justifies it.
- Every table has a surrogate PK. For new tables: `id UUID PRIMARY KEY DEFAULT gen_random_uuid()`.
  Use BIGSERIAL only when the insert volume makes UUID fan-out a measurable write issue.
- Add `created_at TIMESTAMPTZ NOT NULL DEFAULT now()` and `updated_at TIMESTAMPTZ NOT NULL
  DEFAULT now()` to every mutable table. Update `updated_at` via a trigger or at the ORM layer.
- Use `TIMESTAMPTZ` (not `TIMESTAMP`) everywhere. Store and compare in UTC.
- Normalize to 3NF for OLTP. Denormalize only for a measured read-hot query path, and
  document the decision.
- JSONB for genuinely schemaless attributes (e.g., IAP receipt payload). Not as a substitute
  for real columns.

For game backend table shapes (accounts, scores, sim_replays, iap_receipts), see
[references/data-migrations.md](../../references/data-migrations.md) (Schema sketch section).

## Step 3: Migrations -- versioned, forward-only

Use Flyway Community (free, latest stable: 12.7.0 as of May 2026).

- All migration files live under `src/main/resources/db/migration/`.
- Name: `V<n>__<description>.sql` -- never edit an applied file.
- Run `flyway.migrate()` at application startup, before accepting traffic.
- `CREATE INDEX CONCURRENTLY` must use `-- flyway:mustNotUseTransaction` at the top of
  that migration file; it cannot run inside a transaction.

Full migration discipline and indexing checklist:
[references/data-migrations.md](../../references/data-migrations.md)

**Migrations against remote/prod DB need the operator's explicit yes first** -- see the Outbound checkpoint section.

## Step 4: Typed query layer -- no string-built SQL

For Kotlin/Ktor, prefer one of:
- **Exposed DSL** (`org.jetbrains.exposed:exposed-core`) -- idiomatic Kotlin, no codegen.
  Good for greenfield. Wrap DB calls in `transaction { }` blocks.
- **jOOQ** -- codegen from schema; most SQL-accurate type safety; better for complex queries.
  Pairs cleanly with Flyway. Use the open-source tier (PostgreSQL is free).

For Go: `pgx/v5` + `sqlc` (codegen from SQL). For Node: Drizzle ORM or Prisma.

Never build SQL strings by hand. Never use `?` positional parameters in raw JDBC strings.
Always use the framework's prepared-statement / bind-parameter API.

### Transactions and isolation

Default isolation for OLTP: `READ COMMITTED` (Postgres default). Use it unless a specific
operation requires stronger guarantees.

Use `REPEATABLE READ` or `SERIALIZABLE` only for:
- Leaderboard rank-claim (prevent two concurrent updates producing the same rank).
- Inventory deduction (prevent double-spend).

Keep transactions short. Do not perform network I/O (HTTP calls, Redis lookups) inside a
DB transaction.

## Step 5: When (and only when) to add Redis or a read replica

**Redis (cache/KV):** add only when a query is hot (sustained >50 req/s on the same rows)
AND eventual consistency is acceptable. Suitable uses: leaderboard top-N snapshot (30 s
TTL), session tokens, rate-limit counters. Always write to Postgres first; cache-aside on
reads; invalidate (not update) the cache key on write.

**Read replica:** add only when the primary is measured to be CPU-bound on reads. For solo
scale this is premature until real traffic proves it. Use a managed replica (Supabase one-
click or RDS read replica); do not hand-manage streaming replication.

**Reject outright:** sharding, NoSQL as a primary store, microservice-per-DB, event-
sourcing/CQRS unless the operator explicitly requests it with a clear justification. These
patterns multiply operational burden with zero benefit at solo scale.

## Outbound checkpoint

Local work needs no approval. Anything outbound (publish, push, post) needs the operator's explicit per-action "yes"; stop, present exactly what would go out, and wait for it before anything leaves the machine.

## References

- [references/data-migrations.md](../../references/data-migrations.md) -- migration discipline, Flyway
  Ktor wiring, forward-only patterns, indexing checklist, Redis and replica decision rules.
- PostgreSQL 17 docs: https://www.postgresql.org/docs/17/
- Flyway Community 12.7.0: https://flywaydb.org/documentation/
- Flyway + Ktor sample: https://plusmobileapps.com/blog/2024/05/25/Postgres%20database%20with%20Flyway%20in%20a%20Ktor%20project/
- jOOQ + Flyway + Ktor: https://www.atkinsondev.com/post/database-jooq-flyway-ktor/
- PostgreSQL indexing strategies (2026): https://www.techbuddies.io/2026/03/19/how-to-choose-postgresql-indexing-strategies-b-tree-vs-gin-vs-brin/
- Flyway vs Liquibase (2026): https://www.bytebase.com/blog/flyway-vs-liquibase/
