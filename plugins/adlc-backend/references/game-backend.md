<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
# game-backend reference

Detail for the `game-backend` skill. Read on demand; do not load by default.

---

## Leaderboard schema (Postgres / Supabase)

```sql
-- One row per player per season.
CREATE TABLE leaderboard_entries (
  id          BIGSERIAL PRIMARY KEY,
  player_id   UUID        NOT NULL REFERENCES players(id),
  season_id   INT         NOT NULL,
  score       BIGINT      NOT NULL DEFAULT 0,
  bracket     SMALLINT    NOT NULL DEFAULT 0,  -- 0=new, 1=bronze, ..., 5=elite
  updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE UNIQUE INDEX ON leaderboard_entries(player_id, season_id);
CREATE INDEX ON leaderboard_entries(season_id, score DESC);
```

Score writes come **only** from the server (RLS: no client INSERT/UPDATE on this table).
Expose ranked page via:
```sql
SELECT player_id, score, RANK() OVER (PARTITION BY season_id ORDER BY score DESC)
FROM leaderboard_entries WHERE season_id = $1
LIMIT 100 OFFSET $2;
```

Seasonal rotation: a cron job (pg_cron or a backend scheduler) closes the season,
snapshots rankings to `season_archives`, resets entries to score=0 for the new season,
and re-assigns brackets based on prior-season rank percentile.

---

## Bracket assignment

Brackets serve two purposes: fair matchmaking and payer protection (ties to
`adlc-monetization` `f2p-economy-design`).

```
Tier  Percentile (end of season)   Typical use
0     New / unranked               Tutorial bracket
1     P50-P100 (bottom half)       Bronze
2     P25-P50                      Silver
3     P10-P25                      Gold
4     P2-P10                       Platinum
5     P0-P2                        Elite
```

On match creation the server picks opponents from the same `bracket` (+-1 if queue is thin).
Never expose the bracket ceiling or monetization intent to the client.

---

## Authoritative deterministic sim re-validation

This is the anti-cheat core for turn-based / asynchronous deterministic games.

### Contract with the Unity sim (from `unity-deterministic-sim`)
- The sim exposes a pure-C# entry point: `SimWorld.Tick(uint seed, FixedInput[] inputs) -> SimState`.
- All arithmetic is fixed-point; no floats, no `Random`, no frame-time dependency.
- The sim assembly can be compiled as a .NET Standard 2.1 library (no UnityEngine reference).

### Server replay flow

```
Client                         Server
  |-- POST /match/submit ------->|
  |   { seed, inputs[], result } |
  |                              | 1. Load sim .dll (shared NuGet or embedded)
  |                              | 2. SimWorld.Tick(seed, inputs) -> serverState
  |                              | 3. if serverState != result -> reject, flag
  |                              | 4. if ok -> write score, grant economy delta
  |<-- 200 OK / 409 Tampered ----|
```

Keep the sim .dll version-pinned to the client build version. Store the mapping
`clientVersion -> simAssemblyHash` in the DB; use it to load the correct dll at replay time.

### Reject conditions
- `serverState.outcome != clientResult.outcome`
- `serverState.score > clientResult.score + tolerance` (client under-reports: suspicious)
- `inputs.length` outside [minTicks, maxTicks] for the game mode
- `seed` already seen for this player in this session (replay-replay attack)

### Performance guard
Re-validation is async (off the request path on a background queue). Return 202 Accepted
immediately; apply score and economy delta only after validation completes. Throttle
the queue to prevent sim-replay DDoS.

---

## IAP server receipt validation + entitlement grant

Use server-side validation only; never trust the client's receipt.

### Google Play
- Endpoint: `purchases.products:get` or `purchases.subscriptions:get` via
  [Google Play Developer API](https://developer.android.com/google/play/developer-api).
- Validate `purchaseState == 1` (purchased); acknowledge after granting entitlement.
- Subscribe to RTDN (Real-Time Developer Notifications) via Pub/Sub for subscription
  lifecycle events (renewal, cancellation, revocation).

### Apple App Store
- Use [App Store Server API](https://developer.apple.com/documentation/appstoreserverapi)
  (`/inApps/v1/lookup/{transactionId}`); receipts are deprecated.
- Subscribe to [App Store Server Notifications V2](https://developer.apple.com/documentation/appstoreservernotifications)
  webhook for subscription events (SUBSCRIBED, DID_RENEW, EXPIRED, REVOKE).
- Verify the signed JWT payload with Apple's public key (JWKS endpoint).

### Entitlement flow
```
Client -> POST /iap/grant { platform, purchaseToken/transactionId }
Server:
  1. Check idempotency key (token already processed? return cached result)
  2. Validate with store API
  3. Write entitlement record (player_id, product_id, store_order_id, granted_at)
  4. Apply economy delta (currency, unlock) in same DB transaction
  5. Acknowledge purchase with store
  6. Return entitlement to client
```

Do not implement the IAP client-side flow here; that belongs in `adlc-monetization`.

---

## Anti-cheat surface map

| Surface              | Server control                                        |
|----------------------|-------------------------------------------------------|
| Economy deltas       | Server writes only; client sends "action request"     |
| Match outcome        | Sim re-validation (see above); reject tampered result |
| Score submission     | Signed JWT from server after validation; not from client |
| Rate limits          | 1 match submit / 30 s per player; hard reject over    |
| Leaderboard writes   | RLS: no direct client writes to leaderboard table     |

Never trust any numeric value sent by the client that affects economy or ranking.

---

## Solo-scale infra notes

- Target: Supabase (Postgres + Edge Functions) or Ktor on a single small VPS (2 vCPU / 2 GB RAM).
- Do NOT use K8s, microservices, event-sourcing, or CQRS until clearly needed.
- Sim re-validation can run in a background coroutine pool; no separate service required at v1.
- Defer: deploy pipeline and observability to `adlc-ops`; security hardening (injection, secrets) to `adlc-security`.
