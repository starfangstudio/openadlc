---
name: schema-design
description: "This skill should be used when modeling data or designing a schema, \"design the database schema\", \"model these entities\", \"should I embed or reference this\", \"normalize this table\", \"what keys and constraints does this need\", \"design the DynamoDB table\", \"pick column types\", \"set up relationships and foreign keys\", or reviewing a data model. Detect-first across Postgres, MySQL, SQLite, Mongo, and DynamoDB: relational modeling (normalization, keys, relationships, constraints, types) and document modeling (embed vs reference, access-pattern-first). Pairs with migrations (the safe change), query-optimization (indexes), and data-access (the access layer)."
version: 0.1.0
---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# Schema design

Model the data for the engine the project actually runs, not the one you know best. A schema is a contract: it outlives the code that reads it, and a bad shape is expensive to undo. Get the keys, relationships, constraints, and types right before any rows land.

## Step 1: Detect the engine and tooling first
Never impose a database. Read the project before writing anything:
- **Engine:** look in `docker-compose.yml`, `.env`, connection strings, and config. Postgres, MySQL, SQLite, MongoDB, or DynamoDB each model differently. Do not guess from the language.
- **Schema tool:** check `package.json`, `requirements.txt`, `mix.exs`, `pom.xml`. Prisma, Drizzle, TypeORM, SQLAlchemy, or Ecto own the schema source. Plain SQL migrations are also common. Match the project's tool; the schema lives where that tool keeps it.
- **Existing shape:** read one or two existing models or migrations. Match naming (snake_case vs camelCase), id strategy (uuid vs bigint vs serial), and timestamp conventions already in use.

If the project is relational, follow Steps 2 to 4. If it is a document or key-value store (Mongo, DynamoDB), follow Step 5. The Step 6 check applies to both.

## Step 2: Model the entities and relationships (relational)
Start from the nouns and the verbs between them.
- **One table per entity.** Name it for the thing it holds. Give every row a stable primary key: a `uuid` or a `bigint` identity, never a natural value that can change (email, slug).
- **Relationships are foreign keys:**
  - **one-to-many:** the foreign key lives on the "many" side (an `order` row carries `customer_id`).
  - **many-to-many:** a join table holds the two foreign keys as a composite primary key (`tag_id`, `post_id`).
  - **one-to-one:** a foreign key plus a `UNIQUE` constraint on it, or a shared primary key.
- Default to **normalized (3NF):** each fact lives in exactly one place, so an update touches one row. Denormalize only when a measured read pattern demands it, and only with a written plan to keep the copy in sync. Normalize first, denormalize on evidence.

## Step 3: Constrain the data so bad rows cannot exist
Push every invariant you can into the schema. The database is the last line that always holds; application checks can be bypassed.
- **`NOT NULL`** on every column that must have a value. Nullable should be a deliberate choice, not a default.
- **`UNIQUE`** on every column or set that must not repeat (a user's email, a `(tenant_id, slug)` pair).
- **`FOREIGN KEY`** on every reference, with an explicit `ON DELETE` rule (`CASCADE`, `RESTRICT`, or `SET NULL`) chosen for the relationship, not left to the default.
- **`CHECK`** for value rules the type cannot express (`price >= 0`, `status IN (...)`, `start_date < end_date`).
- **`PRIMARY KEY`** on every table, always.

A constraint is cheaper than the bug it prevents and far cheaper than the cleanup after bad data lands.

## Step 4: Pick exact types (relational)
The type is the first constraint. Choose the narrowest type that fits the domain.
- **Money and exact decimals:** `NUMERIC` / `DECIMAL` (Postgres treats `DECIMAL` as an alias for `NUMERIC`). Never `float` or `double` for money; binary floats lose cents.
- **Timestamps:** in Postgres use `TIMESTAMPTZ` (it stores UTC and converts on display); plain `TIMESTAMP` drops the zone and breaks across regions. In MySQL use `TIMESTAMP` or `DATETIME` deliberately and store UTC.
- **Identifiers:** `uuid` (or `BIGINT` identity), not `VARCHAR`. A typed id is smaller, indexes better, and rejects garbage.
- **Bounded categories:** a `CHECK ... IN (...)` or a lookup table over a free-text string. Avoid the engine's native `ENUM` if values change often, since altering it is a migration.
- **Text:** `TEXT` in Postgres (no penalty over `VARCHAR(n)` unless a length cap is a real rule). Reach for `VARCHAR(n)` only when the limit is a genuine domain constraint.

## Step 5: Document and key-value modeling (Mongo, DynamoDB)
Here the rules invert: shape the data around how the application reads it, not around normal forms.

**DynamoDB is access-pattern-first, always.** Write down every query the app must serve before designing a single key. Then:
- Design the **partition key (PK)** for high cardinality and even write distribution. A timestamp or sequential counter as PK is the classic mistake; it creates a hot partition. Add a uuid or a shard prefix.
- Use the **sort key (SK)** for ranges and hierarchy within a partition (`begins_with`, `between`). Overload PK/SK so one `Query` returns a whole item collection (single-table design).
- Add a **global secondary index (GSI)** for each access pattern the base table cannot serve. No ad-hoc query exists; if no key serves it, it cannot run efficiently.

**MongoDB: embed vs reference is the core decision.** Ask "what does the app read and write together?"
- **Embed** when the child is always read with the parent, the count is small and bounded, and it updates atomically with the parent (an order's line items, an address on a user).
- **Reference** when the data is queried on its own, can grow unboundedly (comments, events, logs), is shared across many parents, or changes far more often than the parent.
- **Hard ceiling:** a MongoDB document is capped at 16MB. An unbounded embedded array will eventually hit it. If it can grow without limit, reference it.

## Step 6: Verify
The failable check is concrete: **the schema or migration applies cleanly to a real (test or local) database, and a constraint test passes.**
- Apply the schema with the project's tool (`prisma migrate dev`, `drizzle-kit generate` then `drizzle-kit migrate`, the SQLAlchemy/Alembic or Ecto migration command, or the raw SQL migration). It must run without error.
- Then prove one constraint bites: insert a row that violates a `CHECK`, `UNIQUE`, `NOT NULL`, or `FOREIGN KEY` and assert the database rejects it. For DynamoDB, assert each declared access pattern resolves to a `Query` on a defined key or GSI.
- A schema that has never been applied, or whose constraints have never been tested against a bad row, is not done. Hand the safe rollout of the change to `migrations`.

## References
- The safe change: `migrations`. Indexes and query plans: `query-optimization`. The access layer and parameterized queries: `data-access`. Routing from the backend: `adlc-backend`. Parameterization and injection: `adlc-security`.
- DynamoDB partition-key design: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-partition-key-design.html
- MongoDB document size limit and modeling: https://www.mongodb.com/docs/manual/data-modeling/
- PostgreSQL data type guidance: https://wiki.postgresql.org/wiki/Don't_Do_This
