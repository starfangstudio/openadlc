<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
# Modular Monolith Reference

Deep-dive companion to the `backend-architecture` skill. Load on demand; do not duplicate in the skill body.

---

## Module seams

Each domain module is a self-contained package/namespace with three layers:

```
<module>/
  api/          # public interfaces, DTOs, domain events (what other modules may import)
  service/      # business logic; depends on api + data only
  data/         # repository impls, DB queries; never imported by another module's service
```

Rules:
- Only the `api` sub-package is importable by other modules. Enforce with package-private or explicit Kotlin `internal` visibility.
- No module accesses another module's `data` layer directly. It goes through the owning module's `api`.
- Each module owns its own DB tables. No cross-module joins in queries; project data at the service layer instead.
- Cross-module calls within the same process are direct function calls. Do NOT add a message bus just to decouple -- use domain events only when the coupling is genuinely cyclic.

### Module map for ADLC backend

| Module | Owns | Public API exports |
|---|---|---|
| `accounts` | users, sessions, device tokens | `AccountService`, `AccountId` |
| `catalog` | game/app catalogue, feature flags | `CatalogService`, `ProductId` |
| `leaderboards` | score records, ranked queries | `LeaderboardService`, `ScoreEntry` |
| `payments` | IAP receipts, store notifications | `PaymentService`, `PurchaseRecord` |
| `liveops` | events, schedules, remote config | `LiveopsService`, `EventConfig` |
| `simulation` | server-side sim re-validation | `SimValidator`, `ReplayResult` |

The `simulation` module is read-only from other modules' perspective: callers submit a replay bundle and receive a `ReplayResult`. Implementation ties to the Unity deterministic-sim contracts (see `adlc-unity` plugin, `unity-deterministic-sim` skill).

---

## When to split a module into a separate service

Split ONLY when a measurable, real reason has arrived. Work through the checklist in order; stop at the first "yes" that meets the stated threshold.

| # | Signal | Threshold |
|---|---|---|
| 1 | Independent scaling | One module consumes 10x the CPU/RAM of the rest and a single VM cannot keep up |
| 2 | Independent deploy cadence | Different team or external constraint requires its own release pipeline |
| 3 | Polyglot persistence | Module genuinely needs a different DB engine (e.g., pure graph DB) that cannot be added as a schema to the shared instance |
| 4 | Hard SLA isolation | One module's latency spike must not affect another module's response time |
| 5 | Security/compliance boundary | Regulations require network-level isolation (e.g., PCI in-scope data) |

For a solo developer on a modular monolith serving under ~100K DAU, none of these thresholds are likely to trip. If you feel the urge to split, write down the concrete, measured reason first. If you cannot, do not split.

**When splitting, extract the minimum viable service:**
1. Promote the module's `api` package to a shared contract library (or OpenAPI spec).
2. Replace in-process calls with an HTTP or gRPC client behind an interface.
3. Deploy the extracted module independently; remove it from the monolith's compile dependency.
4. Do NOT change the internal design of the extracted module; the seam was already clean.

---

## Layering inside the monolith

```
HTTP/gRPC transport layer     (routing, auth middleware, request parsing, rate-limit)
        |
   Module service layer       (business rules, domain events, orchestration)
        |
   Module data layer          (DB queries, cache reads, outbox writes)
        |
  Shared infrastructure       (DB pool, migration runner, cache client, job scheduler)
```

Dependencies flow strictly downward. The transport layer never calls the data layer directly.

### Outbox for cross-module side effects

When Module A's action must trigger Module B (e.g., a new purchase triggers a leaderboard reset), write a domain event to an `outbox` table inside Module A's transaction. A background worker polls the outbox and calls Module B's `api`. This keeps Module A's transaction atomic and decouples delivery timing without requiring a separate message broker.

Use an outbox only for genuinely async, at-least-once needs. Synchronous in-process call first; add the outbox when you have a real consistency reason.

---

## Stack selection guide

Detect the existing stack first (see skill). If none exists, use this decision tree:

```
Already strong in Kotlin/JVM?
  YES --> Ktor 3.x + Exposed or JOOQ + PostgreSQL
          (Ktor modules map 1:1 to domain modules; DI via built-in plugin or Koin)
  NO  --> Go (net/http + sqlc + pgx) or Node (Fastify + Drizzle)
          if a managed BaaS covers >=80% of needs (auth, DB, storage):
            --> Supabase (Postgres + row-level security + Edge Functions for custom logic)
```

Supabase is the fastest path to v1 for utility apps (sync, accounts). For F2P games needing custom sim validation and leaderboard logic, a Ktor or Go service gives more control.

---

## References

- Milan Jovanovic, "Modular Monolith Architecture" -- https://www.milanjovanovic.tech/blog/modular-monolith-architecture-dotnet
- JetBrains, "Modular Ktor: Building Backends for Scale" -- https://blog.jetbrains.com/kotlin/2025/07/modular-ktor-building-backends-for-scale/
- sachith.co.uk, "Modular Monoliths Done Right" (Jun 2026) -- https://www.sachith.co.uk/modular-monoliths-done-right-scaling-strategies-practical-guide-jun-3-2026/
