---
name: query-optimization
description: "This skill should be used when a query is slow or about to scale, \"make this query fast\", \"optimize this query\", \"this endpoint is slow\", \"add an index\", \"read the EXPLAIN / query plan\", \"why is this a full table scan\", \"fix the N+1\", \"paginate a large table\", \"speed up ORDER BY / GROUP BY\", or reviewing query performance before ship. Detect-first across Postgres / MySQL / SQLite and the ORM in use (Prisma / Drizzle / TypeORM / SQLAlchemy / Ecto): read the plan, index for the real access pattern, kill N+1 and full scans, switch deep pagination to keyset, and prove it with a before/after measurement. Pairs with schema-design (the model), data-access (the access layer), and migrations (shipping an index safely)."
version: 0.1.0
---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# Query optimization

Make slow queries fast with evidence, not guesses. The order is always the same: measure, read the plan, change one thing, measure again. "It feels faster" is not a result; a number is.

## Step 1: Detect the engine and access layer first
Never impose a tool. Read the project before touching a query:
- **Engine:** Postgres, MySQL / MariaDB, or SQLite. The plan syntax and index features differ (covering-index `INCLUDE` is Postgres / SQLite; MySQL fakes it via a composite index).
- **Access layer:** raw SQL, a query builder, or an ORM (Prisma, Drizzle, TypeORM, SQLAlchemy, Ecto). The N+1 fix and the eager-load API live here (see `data-access`).
- **The real query:** turn on the ORM's SQL logging so you optimize the SQL that actually runs, not the SQL you think runs. ORMs hide joins, extra round-trips, and `SELECT *`.

Find the actual offender before optimizing: the slow-query log (`log_min_duration_statement` in Postgres, the slow query log in MySQL) or `pg_stat_statements` tells you which query to fix. Do not optimize a query nobody runs.

## Step 2: Read the plan, do not guess
Get the real plan with timings and I/O, then read it:
- **Postgres:** `EXPLAIN (ANALYZE, BUFFERS) <query>`. `ANALYZE` runs the query and shows actual rows + time; `BUFFERS` shows blocks read from disk vs cache, which exposes the heaviest node.
- **MySQL 8.0.18+:** `EXPLAIN ANALYZE FORMAT=JSON <query>` for actual timing; plain `EXPLAIN` for the estimated plan and `access_type`.
- **SQLite:** `EXPLAIN QUERY PLAN <query>`.

Read it for these tells:
- **Full scan on a large table returning few rows** (Postgres `Seq Scan`, MySQL `type: ALL`) is the classic missing-index smell. A scan is fine when the query returns most of the table or the table is tiny; do not "fix" those.
- **Estimated rows far from actual rows** means stale statistics. Run `ANALYZE` (Postgres) / `ANALYZE TABLE` (MySQL) so the planner sees reality before you blame the plan.
- **The most expensive node** is where the time and the buffer reads concentrate. Fix that node, not the whole query.

## Step 3: Index for the real access pattern
An index is a contract with one query shape. Build it from the `WHERE`, `JOIN`, and `ORDER BY` you actually run, not from the column you happen to filter on today:
- **Composite column order:** equality columns first, then the range / sort column. An index on `(tenant_id, created_at)` serves `WHERE tenant_id = ? ORDER BY created_at`; the reverse order does not.
- **Selectivity:** index columns that cut the row count hard. A boolean or a low-cardinality flag alone rarely earns an index; lead the composite with the selective column.
- **Covering index (index-only scan):** put the few returned columns in the index so the engine never touches the heap. In Postgres / SQLite use `INCLUDE (...)` for non-key payload columns (keeps the B-tree key small); in MySQL add them as trailing index columns. Confirm with `Index Only Scan` in the plan.
- **Match the sort:** the index column order and direction must match `ORDER BY` exactly, or the engine still sorts.

Every index has a write cost and storage cost. Add the one the plan proves you need, drop unused ones (`pg_stat_user_indexes` shows zero-scan indexes), and ship it as a real migration (`CREATE INDEX CONCURRENTLY` in Postgres to avoid locking, see `migrations`).

## Step 4: Kill N+1 and accidental full scans
- **N+1:** one query for the list, then one more per row, is the most common app-level slowness. Detect it by counting queries per request in the ORM log (a list of 50 firing 51 queries is the signature). Fix by fetching the relation up front: a `JOIN` / eager load (Prisma `include`, SQLAlchemy `joinedload` / `selectinload`, TypeORM `relations`, Ecto `preload`), or a batched `WHERE ... IN (...)` (the DataLoader pattern, the standard fix in GraphQL resolvers). Keep relation access out of loops.
- **Functions on indexed columns:** `WHERE lower(email) = ?` or `WHERE date(created_at) = ?` cannot use a plain index. Use an expression index, a generated column, or rewrite to a sargable range (`created_at >= ? AND created_at < ?`).
- **Leading wildcard `LIKE '%foo'`** scans; use a trigram index (Postgres `pg_trgm`) or full-text search instead.
- **`SELECT *`** blocks index-only scans and ships columns nobody reads. Select the columns you use.

## Step 5: Paginate large sets with keyset, not OFFSET
`OFFSET n` makes the engine read and discard `n` rows, so deep pages degrade to O(n) and slow linearly as users page down (deep offsets can be ~100x slower). For large or infinite-scroll sets, use keyset (seek) pagination: carry the last row's sort key and continue past it.

```sql
-- Page 1
SELECT id, title, created_at FROM posts
ORDER BY created_at DESC, id DESC
LIMIT 20;

-- Next page: pass the last row's (created_at, id) as the cursor
SELECT id, title, created_at FROM posts
WHERE (created_at, id) < ($last_created_at, $last_id)
ORDER BY created_at DESC, id DESC
LIMIT 20;
```

The tuple comparison needs a composite index on the exact sort columns and directions (`(created_at DESC, id DESC)` here); `id` as the tiebreaker keeps the order total and stable. Keyset also stops the skip / duplicate rows that OFFSET shows when data shifts between pages. Keep OFFSET only where the product truly needs jump-to-page-N navigation.

## Step 6: Measure before and after, prove the win
Optimization without a measurement is a guess. Capture the baseline before changing anything and the same number after:
- Re-run `EXPLAIN (ANALYZE, BUFFERS)` and compare actual time, rows, and buffer reads. The scan should become an `Index Scan` / `Index Only Scan` and buffer reads should drop.
- Run the query 3+ times and take the steady-state time so a cold cache does not flatter or punish either side.
- Record both numbers (for example "p95 420ms to 18ms, Seq Scan to Index Only Scan") in the PR so the reviewer (see `database-reviewer`) can check the claim.

## Step 7: Verify (failable check)
The check passes or fails, no judgement call:
- **Plan assertion:** capture `EXPLAIN` for the target query in a test and assert the plan no longer contains `Seq Scan` / `type: ALL` on the offending table (or asserts `Index Only Scan` is present). The test fails if a future change regresses the plan.
- **Or latency threshold:** assert the query runs under a budget on a representative dataset (for example `assert elapsed_ms < 50`). Seed enough rows that the threshold means something; 10 rows always pass.

A query optimization with no before/after number and no failing-without-the-fix check is not done.

## References
- The data model and keys the index sits on: `schema-design`. Shipping an index without locking: `migrations`. The ORM eager-load / batching API and SQL logging: `data-access`. The review before the operator's outbound yes: agent `database-reviewer`.
- Postgres: [Using EXPLAIN](https://www.postgresql.org/docs/current/using-explain.html), [Index-Only Scans and Covering Indexes](https://www.postgresql.org/docs/current/indexes-index-only-scans.html). MySQL: [EXPLAIN Output Format](https://dev.mysql.com/doc/refman/8.0/en/explain-output.html).
- Keyset pagination: [Keyset cursors, not offsets](https://blog.sequinstream.com/keyset-cursors-not-offsets-for-postgres-pagination/). N+1: [Prisma query optimization](https://www.prisma.io/docs/orm/prisma-client/queries/query-optimization-performance).
