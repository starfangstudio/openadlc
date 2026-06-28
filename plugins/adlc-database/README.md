<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
# adlc-database

The data domain pack. Detect-first across SQL (Postgres / MySQL / SQLite) and NoSQL (Mongo / DynamoDB) and the ORM in use (Prisma / Drizzle / TypeORM / SQLAlchemy / Ecto). `adlc-backend` routes the data-layer depth here; this pack owns the schema, migrations, queries, and access.

## Skills
- `schema-design`: model the data (relational + document), normalization vs denormalization, keys, relationships, constraints, types.
- `migrations`: safe, zero-downtime schema change (expand-contract, additive-first, reversible) via the project's migration tool.
- `query-optimization`: indexing, query plans (EXPLAIN), killing N+1 and full scans, keyset pagination, the slow-query workflow.
- `data-access`: the access layer (ORM / query builder / raw), transactions, connection pooling, parameterized queries only (ties to adlc-security).

## Agents
- `database-architect`: design the data model + access strategy. Read-only, produces a plan.
- `database-reviewer`: review DB changes (schema, migration safety, query perf, injection) before the operator's outbound yes.

## Status
Early. Detect-first skills and agents for the data domain (schema, migrations, query optimization, data access), authored to [the pack format](../../docs/pack-format.md).
