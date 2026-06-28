<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
Consumed by the `game-backend` skill. Load on demand; do not load independently.

## Sim assembly contract

The sim contract comes from `adlc-unity` `unity-deterministic-sim`:

- `SimWorld.Tick(uint seed, FixedInput[] inputs) -> SimState` -- pure C#, no UnityEngine.
- Compiled as .NET Standard 2.1; embeddable in the backend without Unity.

## Sim re-validation full reject conditions

- `clientResult` differs from the server replay output (tampered result).
- `seed` already seen for this player this session (replay-of-a-replay attack).
- `inputs.length` outside the game mode's `[minTicks, maxTicks]` range.

## Async re-validation rationale

Return 202 immediately; apply score and economy delta only after validation completes. This
prevents the submit path from blocking on sim execution and prevents sim-replay DDoS via queue
throttling. Use a bounded worker queue; hard-reject enqueue when the queue is full (503).

## Sim version pinning

Store `clientVersion -> simAssemblyHash` in the DB. At replay time, load the assembly that
matches the version reported by the client. Reject if the hash is unknown (unrecognized build).

## Verify checklist (pass/fail, not "looks right")

Run all boxes on a test environment before marking any step done.

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
