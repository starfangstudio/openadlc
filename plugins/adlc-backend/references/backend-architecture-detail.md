<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
Consumed by the `backend-architecture` skill. Load on demand; do not load independently.

## Standard domain modules

| Module | Responsibility |
|---|---|
| `accounts` | users, sessions, device tokens, auth |
| `catalog` | game/app listings, feature flags, versioning |
| `leaderboards` | score records, ranked queries, tie-breaking |
| `payments` | IAP server receipt validation, store server-notifications |
| `liveops` | events, schedules, remote config |
| `simulation` | authoritative sim re-validation (server replays seeded inputs) |

Add only the modules the product actually needs. Start with `accounts`; add others on demand.

## Layering contract

```
transport   HTTP/gRPC routing, auth middleware, request parsing, rate-limit
   |
service     business rules, domain events, orchestration (one per module)
   |
data        DB queries, cache reads, outbox writes (private to the module)
   |
infra       DB pool, migration runner, cache client, job scheduler (shared)
```

Dependencies flow strictly downward. Transport never calls data directly.

## Stack selection guide (greenfield)

Canonical stack selection guide (decision tree plus Ktor module structure) lives in
[references/modular-monolith.md](modular-monolith.md). Kept in one place to avoid drift.

## Cross-cutting deferrals

| Concern | Defer to |
|---|---|
| Deploy, infra, observability, CI | `adlc-ops` plugin |
| Security hardening (injection, secrets, authz) | `adlc-security` plugin |
| Privacy / PII / retention / erasure | `adlc-privacy` plugin |
| IAP CLIENT-side integration | `adlc-monetization` plugin (server receipt validation stays here) |
| Deterministic sim contracts | `adlc-unity` plugin, `unity-deterministic-sim` skill |
