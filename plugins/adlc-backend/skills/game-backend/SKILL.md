---
name: game-backend
description: >-
  This skill should be used when the user asks to "add a leaderboard", "add seasonal rankings",
  "set up matchmaking brackets", "bracket players by skill or spend tier", "validate a match
  result server-side", "replay the sim on the server", "detect cheating in match outcomes",
  "grant an IAP entitlement after receipt validation", "handle App Store server notifications",
  "handle Google Play RTDN", "add anti-cheat to the game backend", "prevent score tampering",
  "make the economy server-authoritative", or "wire the game backend to the Unity sim". Covers
  the F2P game-server layer: ranked/seasonal leaderboards with bracket assignment, authoritative
  deterministic-sim re-validation (server replays the client's seeded inputs to reject tampered
  results), IAP entitlement granting after store receipt validation, and server-authoritative
  economy anti-cheat. Defers deploy/ops to adlc-ops, security hardening to adlc-security, the
  IAP client flow to adlc-monetization, and sim determinism rules to adlc-unity
  unity-deterministic-sim.
version: 0.1.0
---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# game-backend

The F2P game-server layer: leaderboards, matchmaking brackets, authoritative sim re-validation,
IAP entitlement granting, and server-authoritative anti-cheat. Solo-scale only; no microservices,
no K8s, no event-sourcing unless the project already uses them.

## Step 1: Detect first -- never impose

Inspect the existing project before touching anything:

```bash
# Backend language / framework
find . -name "build.gradle.kts" -o -name "*.ktor" -o -name "package.json" \
       -o -name "go.mod" | head -5

# Database in use
grep -rEi "supabase|postgres|mysql|sqlite|mongo" . \
     --include="*.kts" --include="*.toml" --include="*.env*" | head -10

# Existing leaderboard / IAP / anti-cheat code
grep -rEn "leaderboard|receipt|purchaseToken|SimWorld" . \
     --include="*.kt" --include="*.go" --include="*.ts" | head -20

# Unity sim assembly (for re-validation)
find . -name "*.dll" -path "*/Simulation*" 2>/dev/null | head -5
```

Mark anything not found `unknown`. Ask before picking a stack. Natural fits: Kotlin/Ktor on a
small VPS, or Supabase (Postgres + Edge Functions). Go and Node are also fine. Do not force a
choice.

## Step 2: Leaderboard + seasonal brackets

The server is the **only** writer to `leaderboard_entries`. RLS or equivalent blocks client
writes. Score is submitted via a validated match result (Step 4), never directly by the client.

Core schema (Postgres/Supabase):

```sql
CREATE TABLE leaderboard_entries (
  id         BIGSERIAL PRIMARY KEY,
  player_id  UUID      NOT NULL REFERENCES players(id),
  season_id  INT       NOT NULL,
  score      BIGINT    NOT NULL DEFAULT 0,
  bracket    SMALLINT  NOT NULL DEFAULT 0,  -- 0=new 1=bronze .. 5=elite
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE UNIQUE INDEX ON leaderboard_entries(player_id, season_id);
CREATE INDEX ON leaderboard_entries(season_id, score DESC);
```

Ranked page query: `SELECT player_id, score, RANK() OVER (PARTITION BY season_id ORDER BY score DESC) FROM leaderboard_entries WHERE season_id = $1 LIMIT 100 OFFSET $2;`

Seasonal rotation: a cron job closes the season, snapshots to `season_archives`, resets scores,
and re-assigns brackets by prior-season rank percentile (P50+=bronze, P25-P50=silver, P10-P25=gold,
P2-P10=platinum, top 2%=elite). Never expose bracket ceiling to clients.

Full bracket tier table and matchmaking queue logic: [references/game-backend.md](references/game-backend.md).

Verify: server-written score appears ranked correctly; direct client write returns 403/RLS deny.

## Step 3: IAP entitlement granting

Never trust a client receipt directly. Server validates with the store API, then grants.

Entitlement flow:
1. Check idempotency key (`store_order_id` already processed? return cached result).
2. Validate with store API (Google: `purchases.products:get`; Apple: App Store Server API `/inApps/v1/lookup/{transactionId}`).
3. Write entitlement row (`player_id`, `product_id`, `store_order_id`, `granted_at`).
4. Apply economy delta in the **same DB transaction** as step 3.
5. Acknowledge the purchase with the store **after** the DB commit.
6. Return entitlement to client.

Subscribe to push events for subscription lifecycle: Google RTDN via Pub/Sub; Apple Server
Notifications V2 webhook. Do not poll.

The IAP client flow (StoreKit 2, Play Billing Library) belongs in `adlc-monetization`.

Full store-specific API calls and JWT verification: [references/game-backend.md](references/game-backend.md).

Verify: sandbox purchase token -> entitlement row written; re-submit -> same row (no duplicate).

## Step 4: Authoritative deterministic sim re-validation

Anti-cheat core. The server replays `{ seed, inputs[], clientResult }` through the sim and
rejects any mismatch.

```
Client                         Server
  |-- POST /match/submit ------->|
  |   { seed, inputs[], result } |
  |                              | 1. Load sim .dll (version-pinned to clientVersion)
  |                              | 2. SimWorld.Tick(seed, inputs) -> serverState
  |                              | 3. serverState != result  -> 409, flag, no score
  |                              | 4. ok -> enqueue score + economy delta write (async)
  |<-- 202 Accepted / 409 -------|
```

Return 202 immediately; apply score async after validation. This prevents blocking the submit
path on sim execution and prevents sim-replay DDoS via queue throttling (hard-reject 503 when
queue is full).

Reject if: outcome mismatch; `seed` already seen this session; `inputs.length` outside
`[minTicks, maxTicks]` for the game mode.

Sim contract: `SimWorld.Tick(uint seed, FixedInput[] inputs) -> SimState`, pure C#, fixed-point
arithmetic, .NET Standard 2.1. Full assembly contract and version-pinning rules:
[references/game-backend-detail.md](references/game-backend-detail.md).

Verify: honest match -> 202 -> score credited. Tampered result -> 409 -> no score. Duplicate
seed -> rejected.

## Step 5: Anti-cheat surface hardening

Must-have at v1:
- All economy deltas (currency, item grants) are server writes triggered by validated server
  events (match result, IAP entitlement). No client-supplied delta is ever applied directly.
- Rate-limit match submissions per player (e.g., 1 per 30 s). Hard-reject over the limit.
- Leaderboard writes gated by RLS (Supabase) or equivalent middleware check.
- Never expose internal score thresholds, bracket ceilings, or sim seed generation logic to
  the client.

Defer injection hardening, secret rotation, authz bugs to `adlc-security`.

## Step 6: Verify

Run every box as a pass/fail test, not "looks right":

```
[ ] Leaderboard: direct client write -> 403/denied
[ ] Leaderboard: server-written score -> appears in ranked query in correct order
[ ] Seasonal rotation: cron fires -> bracket percentiles reassigned correctly
[ ] IAP: sandbox purchase -> entitlement row written; re-submit -> same row (no duplicate)
[ ] Sim re-validation: honest match -> 202 -> score credited async
[ ] Sim re-validation: tampered result -> 409 -> no score
[ ] Sim re-validation: duplicate seed -> rejected
[ ] Rate limit: burst submit -> excess requests return 429
```

## Outbound checkpoint

Local work needs no approval. Outbound here (migration against a remote/production database, deploying to a live environment, live Google Play or Apple App Store APIs with write tokens, publishing any package): stop, present exactly what would go out, and wait for the operator's explicit "yes" before it leaves the machine.

## References

- [references/game-backend.md](references/game-backend.md) -- leaderboard schema, bracket tiers, sim
  replay flow, IAP entitlement flow, anti-cheat surface map, solo-scale infra notes.
- [references/game-backend-detail.md](references/game-backend-detail.md) -- sim assembly contract, full reject
  conditions, async rationale, version-pinning rules, verify checklist.
- Google Play Developer API (purchases.products:get, subscriptions:get, RTDN):
  https://developer.android.com/google/play/billing/backend
- Apple App Store Server API + Server Notifications V2:
  https://developer.apple.com/documentation/appstoreserverapi
  https://developer.apple.com/documentation/appstoreservernotifications
- AccelByte: Server-Authoritative Game Logic to Prevent Cheating:
  https://accelbyte.io/blog/server-authoritative-logic-to-prevent-cheating
- `adlc-unity` `unity-deterministic-sim` -- sim assembly contract (seed, fixed-point, Tick API).
- `adlc-monetization` `f2p-economy-design` -- bracket monetization strategy, IAP client flow.
- `adlc-ops` -- deploy pipeline and observability (deferred).
- `adlc-security` -- injection hardening, secret rotation (deferred).
