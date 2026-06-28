<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
# data-migrations reference

## Schema sketch

Minimal game backend tables. Write these as the first Flyway migration(s).

```sql
-- accounts (shared across all games). Canonical account/identity model is in
-- auth-identity.md: one Account row, plus one Identity row per social/email link.
CREATE TABLE accounts (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- scores (leaderboard)
CREATE TABLE scores (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id  UUID NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    game_id     TEXT NOT NULL,
    season_id   TEXT NOT NULL,
    score       BIGINT NOT NULL,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- sim_replays (authoritative re-validation; ties to unity-deterministic-sim skill)
CREATE TABLE sim_replays (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id   UUID NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    game_id      TEXT NOT NULL,
    seed         BIGINT NOT NULL,
    inputs       BYTEA NOT NULL,  -- serialized input log
    result       JSONB,           -- server verdict after re-validation
    submitted_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- iap_receipts (server-side validation; client IAP flow is adlc-monetization)
CREATE TABLE iap_receipts (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id     UUID NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    store          TEXT NOT NULL,   -- 'google_play', 'app_store'
    transaction_id TEXT NOT NULL UNIQUE,
    product_id     TEXT NOT NULL,
    raw_payload    JSONB NOT NULL,
    validated_at   TIMESTAMPTZ,
    status         TEXT NOT NULL DEFAULT 'pending',
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

---

## Migration discipline

Use Flyway (Community, free). Versioned SQL files only: `V<n>__<description>.sql`.
No XML/YAML changesets; no hand-editing applied migrations.

### File naming
```
src/main/resources/db/migration/
  V1__create_accounts.sql
  V2__add_display_name_to_accounts.sql
  V3__create_leaderboard_scores.sql
```

- Version numbers are integers, monotonically increasing.
- Description uses `_` (underscores) not spaces; Flyway maps `__` (double-underscore) to the separator between version and description.
- Never rename or edit a file that Flyway has already applied. It checksums every applied script; a mismatch aborts startup.

### Flyway Ktor wiring (Kotlin)
```kotlin
// build.gradle.kts
implementation("org.flywaydb:flyway-core:12.7.0")
implementation("org.flywaydb:flyway-database-postgresql:12.7.0")

// Application.kt (inside Application module fun)
val flyway = Flyway.configure()
    .dataSource(dataSource)
    .locations("classpath:db/migration")
    .baselineOnMigrate(false)   // only true on first-time adoption of an existing DB
    .validateOnMigrate(true)
    .load()
flyway.migrate()
```

Run `flyway.migrate()` at startup, before the server accepts traffic. This is safe because
startup is atomic: if migration fails, the process exits and does not serve.

### Forward-only migrations

Prefer additive changes. Reversible-where-safe means:
- Adding a nullable column: reversible (drop the column in a rollback migration).
- Renaming a column: NOT safe without a two-step expand/contract (add new col, copy data,
  drop old). Write two separate versioned migrations.
- Dropping a column/table: destructive. Back up first; use `IF EXISTS`; get the operator's explicit yes first.

Never write `V4__rollback_V3.sql` that drops what V3 created -- that defeats forward-only.
Write forward-only corrective migrations instead (`V4__drop_unused_index.sql`).

### Zero-downtime DDL on large tables

For tables with millions of rows where a long `ALTER TABLE ... ADD COLUMN` or index build
would lock writes:
- Add column `NOT NULL DEFAULT <literal>` (Postgres 11+ stores the default in catalog, no
  table rewrite).
- Create indexes with `CREATE INDEX CONCURRENTLY` -- runs without a write lock.
  Flyway cannot wrap `CREATE INDEX CONCURRENTLY` in a transaction; use
  `-- flyway:mustNotUseTransaction` at the top of that migration file.

```sql
-- flyway:mustNotUseTransaction
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_scores_user_id ON scores (user_id);
```

---

## Indexing checklist

Run this before and after adding any index. Ask: "which real query does this index serve?"
Never add speculative indexes.

### Decision tree

| Query pattern | Index type | Notes |
|---|---|---|
| Equality on scalar column (`WHERE user_id = $1`) | B-tree (default) | Auto-created on PK/UNIQUE; add manually otherwise |
| Range (`WHERE created_at BETWEEN ...`) | B-tree | Composite: put range column last |
| Full-text search | GIN on `tsvector` column | Slow writes; only add if text search is a real feature |
| JSONB field access (`WHERE data->>'key' = $1`) | B-tree expression or GIN | Prefer expression index on 2-3 keys over full GIN |
| Only a subset of rows queried | Partial index | `CREATE INDEX ... WHERE status = 'active'` |
| Append-only time-series (logs, events) | BRIN | Tiny size; only accurate for naturally ordered data |

### Post-index checks

```sql
-- Confirm index is actually used by the planner
EXPLAIN (ANALYZE, BUFFERS) <your query>;

-- Find unused indexes (after a week of real traffic)
SELECT schemaname, tablename, indexname, idx_scan
FROM pg_stat_user_indexes
WHERE idx_scan = 0
ORDER BY schemaname, tablename;

-- Index bloat watch (run periodically)
SELECT relname, n_dead_tup, n_live_tup,
       round(n_dead_tup::numeric / nullif(n_live_tup,0) * 100, 1) AS dead_pct
FROM pg_stat_user_tables
ORDER BY n_dead_tup DESC
LIMIT 10;
```

Drop indexes with `idx_scan = 0` after confirming with `EXPLAIN ANALYZE` that no query
uses them. Unused indexes slow writes for free.

### Composite index column order

Rule: highest-cardinality equality columns first, range column last.

```sql
-- Leaderboard: lookup by game + season, sort by score
CREATE INDEX idx_scores_game_season_score
    ON scores (game_id, season_id, score DESC);
```

### When to add Redis

Only when a query is:
1. Hot (>50 req/s hitting the same rows), AND
2. The data does not need to be strongly consistent at read time.

Suitable: leaderboard top-N snapshot (refresh every 30 s), session tokens, rate-limit
counters. Not suitable: player inventory, IAP receipts, account data (need strong
consistency).

Cache-aside pattern: read from Redis; on miss, read Postgres and populate Redis with TTL.
Write always goes to Postgres first, then invalidate (not update) the cache key.

### When to add a read replica

Only after profiling shows the primary is CPU-bound on reads. For a solo-scale game backend,
a read replica is premature until you have sustained traffic that saturates the primary.
Use Supabase read replicas (one click) or a managed RDS read replica rather than
hand-managing replication.

---

## References

- Flyway Community 12.7.0: https://flywaydb.org/documentation/
- Flyway + Ktor sample: https://plusmobileapps.com/blog/2024/05/25/Postgres%20database%20with%20Flyway%20in%20a%20Ktor%20project/
- Craig Atkinson -- jOOQ + Flyway + Ktor: https://www.atkinsondev.com/post/database-jooq-flyway-ktor/
- PostgreSQL indexing strategies: https://www.techbuddies.io/2026/03/19/how-to-choose-postgresql-indexing-strategies-b-tree-vs-gin-vs-brin/
- PostgreSQL effective indexes: https://oneuptime.com/blog/post/2026-01-21-postgresql-indexes/view
- pg_stat_user_indexes: https://www.postgresql.org/docs/current/monitoring-stats.html
