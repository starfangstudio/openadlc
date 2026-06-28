---
name: distributed-data
description: "This skill should be used when scaling a backend's data tier past one node, \"add a read replica\", \"split reads and writes\", \"route reads to replicas\", \"shard the database\", \"partition this table\", \"pick a sharding key\", \"add a distributed cache\", \"cache-aside this query\", \"fix a cache stampede\", \"we have replication lag\", \"users see stale data after writing\", \"read-your-writes\", or \"this read returned old data\". Covers the SCALING and topology of data at scale: read replicas and read/write splitting, partitioning and sharding strategy with trade-offs, distributed caching (cache-aside, invalidation, stampede protection), and the consistency models and failure modes (replication lag, split-brain). Data modeling, schema, indexes, and migrations stay in adlc-database; metrics and alerting stay in adlc-ops; encryption and access control stay in adlc-security."
version: 0.1.0
---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# Distributed data

Scaling the data tier is a topology and consistency problem, not a modeling one. Every technique here trades a consistency guarantee for throughput or latency. Name the trade you are making, then add the check that catches it when it breaks.

This skill owns the SCALING. The schema, indexes, query shape, and migrations that ride on top stay in `adlc-database`. Do not redesign tables here; partition and replicate the ones that already exist.

## Step 1: Detect the data tier first
Never impose a topology. Read the project before adding one:
- The datastore and version (Postgres, MySQL, Mongo, DynamoDB, Cassandra, Vitess, CockroachDB, Spanner). Replication and sharding mechanics differ per engine; do not assume Postgres semantics on MySQL.
- The connection layer: a single connection string, a pooler (PgBouncer, ProxySQL), or an ORM (Prisma, SQLAlchemy, Hibernate). Read/write splitting lives here.
- Whether replicas, a cache (Redis, Memcached), or a sharding proxy already exist. Reuse them before adding more.
- The managed-service constraints. RDS, Aurora, Cloud SQL, and PlanetScale each expose replicas and failover differently; the provider's lag metric and failover behavior are the ground truth.

If one primary still has headroom (CPU, IOPS, connections under limit), say so and stop. A replica or shard you do not need is operational cost with no payoff.

## Step 2: Read replicas and read/write splitting
Add replicas to scale reads, never to scale writes. All writes still go to one primary.
- **Route by intent, not by table.** Writes and any read that must reflect them go to the primary; tolerant reads (lists, search, analytics, dashboards) go to replicas. Make routing explicit in code or the pooler, not implicit in the ORM's default.
- **Replication is asynchronous by default**, so a replica trails the primary by the replication lag. A read routed to a lagging replica returns stale data. This is the cost of the throughput, not a bug to "fix" by adding replicas.
- **Read-your-writes is the routing rule that matters most.** A user who just wrote must read from the primary on their next request, or they will not see their own change. Pin that session to the primary for a TTL longer than expected lag (a few seconds), then let it fall back to replicas.
- **Bounded staleness for the rest.** Read from a replica only if its lag is under a threshold; if every replica is behind, fall back to the primary rather than serve a stale answer. Surface the lag metric to `adlc-ops` for the alert; do not build the dashboard here.

## Step 3: Partitioning and sharding strategy
Shard only when one primary plus replicas cannot hold the write volume or dataset. Sharding multiplies operational cost and forecloses cheap cross-shard joins; it is the last lever, not the first.
- **Pick the shard key for even load, not convenience.** The key must spread both data and traffic. A monotonic key (timestamp, autoincrement) concentrates the newest writes on one shard, the hot-shard problem. A high-cardinality, evenly-accessed key (user id, tenant id) spreads load.
- **Hash sharding** spreads evenly and resists hot spots, but kills range scans (adjacent keys land on different shards). **Range sharding** keeps range scans cheap but concentrates load on the active range and forces split/merge to rebalance. **Geo sharding** cuts latency by locality but does not balance load. Name which you are choosing and what it costs.
- **Consistent hashing** so adding or removing a node moves only a small fraction of keys, not the whole keyspace. Plain modulo-N hashing reshuffles almost everything on a resize.
- **Cross-shard queries are the tax.** Joins, aggregates, and transactions spanning shards are slow or impossible. Denormalize so the common query stays single-shard; push the rare fan-out to a separate analytics path. If most queries need to cross shards, the shard key is wrong.

## Step 4: Distributed caching
A cache trades consistency for latency. Decide how stale is acceptable, then pick the pattern.
- **Cache-aside (lazy):** the app reads cache, and on a miss reads the store, writes the cache, and returns. Simplest and most common. The cache holds only what is asked for.
- **Invalidate on write, do not trust TTL alone.** On a write, delete or update the key so the next read repopulates it. TTL is the backstop for what invalidation misses, not the primary mechanism.
- **Stampede protection is mandatory for hot keys.** When a hot key expires, every concurrent request misses and hammers the store at once (the thundering herd / dogpile). Defend with one of: a per-key lock so one request regenerates while others wait, request coalescing so duplicate concurrent loads share one result, probabilistic early expiration (XFetch) so one request refreshes slightly before expiry, and TTL jitter so keys do not all expire on the same tick.
- **Set a memory eviction policy** (for Redis, an `allkeys-lru` / `allkeys-lfu` `maxmemory-policy`) so the cache sheds cold keys instead of OOMing. A cache without an eviction policy is a memory leak with extra steps.

## Step 5: Name the consistency model and its failure modes
Consistency is a spectrum from linearizable down to eventual. Pick the weakest model the feature can tolerate and write it down; weaker is cheaper and faster.
- **Session guarantees usually suffice:** read-your-writes (see your own writes) and monotonic reads (never see time go backward) cover most user-facing flows without paying for global linearizability.
- **Replication lag** is the everyday failure mode: a replica trails the primary, so reads can be stale and can appear to move backward across requests hitting different replicas. Bound it and route around it (Step 2).
- **Split-brain** is the dangerous one: under a network partition two nodes both believe they are primary and accept conflicting writes. Prevent it with quorum (only the majority partition accepts writes) and fencing (the old primary is fenced off before a new one is promoted). A minority partition cannot even know how stale it is, so it must refuse writes, not guess.
- **Quorum tunes the trade:** with N replicas, R + W > N gives strong reads at the cost of latency; smaller R or W is faster but can read stale or lose a write. State the R, W, N you chose and why.

## Step 6: Verify
The failable check is a load-and-consistency test that surfaces the trade you made, not a unit test of cache hits.
- Drive concurrent writes plus replica reads under load and **assert on the staleness window**: either the measured replication lag stays under your bound, or a read-your-writes read after a write returns the new value (route it to the primary and prove it).
- For the cache, fire many concurrent requests at one expired hot key and assert the backing store sees one regeneration, not N (stampede protection holds).
- The test must be able to FAIL: run it once with splitting or stampede protection disabled and confirm it reports the stale read or the herd. A check that cannot go red is not a check.

## References
- Read replicas and read consistency: [Shopify, Read Consistency with Database Replicas](https://shopify.engineering/read-consistency-database-replicas); [Box Tech, How We Learned to Stop Worrying and Read from Replicas](https://medium.com/box-tech-blog/how-we-learned-to-stop-worrying-and-read-from-replicas-58cc43973638).
- Sharding strategies and trade-offs: [Azure Architecture Center, Sharding Pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/sharding); [PlanetScale, Types of Sharding](https://planetscale.com/blog/types-of-sharding); [YugabyteDB, Data Sharding Strategies](https://www.yugabyte.com/blog/four-data-sharding-strategies-we-analyzed-in-building-a-distributed-sql-database/).
- Cache stampede protection: [Cache stampede (Wikipedia)](https://en.wikipedia.org/wiki/Cache_stampede); [Probabilistic Early Expiration / XFetch](https://www.michal-drozd.com/en/blog/cache-stampede-xfetch/).
- Consistency models and split-brain: [Probabilistically Bounded Staleness (Bailis et al.)](http://www.bailis.org/papers/pbs-vldbj2014.pdf); [Quorum-based tunable consistency (R+W>N)](https://www.systemoverflow.com/learn/replication-consistency/consistency-models/quorum-based-tunable-consistency-the-rwn-formula).
- Pack boundaries: schema, indexes, query depth, and migrations -> `adlc-database`. Lag and cache-hit metrics, alerts, dashboards -> `adlc-ops`. Encryption at rest / in transit and data access control -> `adlc-security`. Async event delivery and the outbox -> `messaging` (this pack).
