---
name: data-access
description: "This skill should be used when building or reviewing the data-access layer, \"write a repository\", \"add a query\", \"where should this DB call live\", \"wrap this in a transaction\", \"set up a connection pool\", \"is this query injection-safe\", \"parameterize this SQL\", \"fix this N+1\", or \"keep persistence out of my domain logic\". Detect-first across ORM (Prisma / Drizzle / TypeORM / SQLAlchemy / Ecto) and query builder vs raw driver: queries stay behind repositories, transactions own their boundary, the pool is shared, every query is parameterized (ties to adlc-security), and related data loads without N+1. Pairs with query-optimization (plans, indexes), schema-design (the model), and migrations (schema change)."
version: 0.1.0
---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# Data access

Own the layer that touches the database. Queries live behind repositories, transactions have one clear boundary, the connection pool is shared, and no value ever reaches SQL by string-building. Match the project's data tooling, not your favorite one.

## Step 1: Detect the access tooling first
Never impose a stack. Read the project before writing a single query:
- **What talks to the DB?** Check `package.json`, `pyproject.toml` / `requirements.txt`, `mix.exs`, or `go.mod` for the dependency. ORM (Prisma, Drizzle, TypeORM, SQLAlchemy, Ecto), query builder (Knex, jOOQ, Kysely), or a raw driver (`pg`, `psycopg`, `database/sql`).
- **How is data reached today?** Open one existing repository or data module. Match its file layout, naming, return types, and error handling.
- **Where does the client live?** Find the single place the client / pool is created (`PrismaClient`, `drizzle(...)`, `create_engine`, `Repo`). You will reuse it, not make a new one.

If the project already has a data-access convention, follow it. A second pattern next to the first is a regression, not a contribution.

## Step 2: Keep persistence behind a repository
Domain logic must not know whether the store is Postgres, Mongo, or a mock. Put every query behind a typed repository (or data module) with intent-named methods.
- **In:** plain arguments or a small typed filter. **Out:** domain types or rows, never a live query object or open cursor.
- `findActiveUsersByTeam(teamId)`, not `query(sql)` called from a service.
- No ORM models, query builders, or raw SQL strings leak above this layer. A service that imports the ORM is the smell to fix (see `software-design`).

One responsibility per repository, usually one aggregate / table group. If it spans two, split it.

## Step 3: Parameterize every query, always (no string-built SQL)
User input reaches the database as a **bound parameter**, never as concatenated or interpolated text. This is the injection boundary and it ties directly to `adlc-security`.
- **ORM query methods** (`findMany`, `where`, `select`) parameterize automatically. Prefer them.
- **Tagged-template raw** binds interpolated values as parameters: Prisma `$queryRaw\`... ${email}\``, Drizzle `sql\`... ${id}\``. Safe because the value becomes a `$1` placeholder, not text.
- **Never** the `Unsafe` / string-concatenation path: Prisma `$queryRawUnsafe(\`... \` + input)`, `db.execute("... " + input)`, f-strings or `%`-format into SQL. These are the vulnerability.
- **Identifiers** (table / column names) cannot be bound. If one must be dynamic, **allowlist** it against a fixed set; never pass user text through.

The rule is absolute: if a value came from outside, it is a parameter. No exceptions for "just an int" or "internal only".

## Step 4: Own the transaction boundary
A transaction wraps one unit of business work and is decided at the use-case layer, not buried per-query.
- Wrap multi-write operations in one transaction so they commit or roll back together: Prisma `$transaction`, Drizzle / TypeORM / Knex `transaction(tx => ...)`, SQLAlchemy `with session.begin():`, Ecto `Repo.transaction`.
- Pass the transaction handle down to the repositories in the unit so every write joins the same transaction. Do not open a second connection mid-transaction.
- Keep transactions short: no network calls or user waits inside one. A held transaction holds a pooled connection.
- Let errors propagate to trigger rollback; do not swallow and continue on a partial write.

## Step 5: Share one connection pool
Create the client / pool **once** per process and reuse it. A new client per request exhausts the database connection limit fast, especially in serverless.
- Instantiate the client / engine at module scope (outside the request handler) so warm invocations reuse it.
- Set a sane pool size for the deployment; do not leave it unbounded.
- Behind a transaction-mode pooler (PgBouncer, Prisma Accelerate), session state does not survive a transaction: prepared statements, `SET`, temp tables, and advisory locks are lost at the boundary. Configure the client for that mode rather than assuming a persistent session.

## Step 6: Load related data without N+1
Fetching a list and then querying once per row is the N+1 trap. Load relations in a set, not in a loop.
- **Prisma:** `include` / `select` the relation in the same call.
- **Drizzle:** the relational `with: { ... }` query.
- **TypeORM:** `relations` on the find, or an explicit join.
- **SQLAlchemy:** `selectinload()` for collections (one `IN` query), `joinedload()` for to-one.
- **Ecto:** `preload` / `Repo.preload`.
- For GraphQL-style fan-out, batch with a DataLoader rather than per-field queries.

If you see a query inside a `for`/`map` over rows, that is the N+1; hoist it (see `query-optimization` for EXPLAIN and indexing).

## Step 7: Verify with a repository test against an ephemeral DB
The failable check is a repository test that runs against a **real, throwaway database**, not a mock.
- Stand up an ephemeral instance: Testcontainers (a fresh `postgres` container per run) for parity, or an in-memory / transactional-rollback fixture for speed (SQLAlchemy savepoint-per-test, Ecto sandbox, SQLite in-memory).
- Apply migrations, write a row through the repository, read it back, assert the round-trip and that relations load in a bounded query count.
- Tear down so each run starts from a known state.

A data-access change with no test against a real DB engine is not done.

## References
- Plans, indexes, EXPLAIN, keyset pagination: `query-optimization`. The model and constraints: `schema-design`. Safe schema change: `migrations`.
- Injection boundary and review: `adlc-security`. Keeping persistence out of the domain: `software-design`.
- Prisma raw queries: https://www.prisma.io/docs/orm/prisma-client/using-raw-sql/raw-queries
- Drizzle `sql` operator: https://orm.drizzle.team/docs/sql
- Prisma connection pooling: https://www.prisma.io/docs/orm/prisma-client/setup-and-configuration/databases-connections/connection-pool
- SQLAlchemy relationship loading: https://docs.sqlalchemy.org/en/20/orm/queryguide/relationships.html
- Testcontainers: https://testcontainers.com
