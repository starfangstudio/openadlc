<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
# Background Jobs Reference

Deep-dive companion to the `background-jobs` skill. Contains schema examples, backoff math, and webhook verification detail that would bloat the main SKILL.md body.

---

## DB-backed job queue: minimal schema (Postgres)

Suitable for Ktor + Exposed or Supabase + direct SQL. If `pg_boss` or BullMQ is already present, use its native schema instead of this.

```sql
CREATE TYPE job_status AS ENUM ('pending', 'running', 'done', 'failed', 'dead');

CREATE TABLE background_jobs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    idempotency_key TEXT UNIQUE NOT NULL,   -- caller-controlled; dedup insert
    queue           TEXT NOT NULL,
    payload         JSONB NOT NULL DEFAULT '{}',
    status          job_status NOT NULL DEFAULT 'pending',
    attempts        INT NOT NULL DEFAULT 0,
    max_attempts    INT NOT NULL DEFAULT 5,
    run_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    locked_until    TIMESTAMPTZ,
    last_error      TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Worker claims the next available job atomically
-- (FOR UPDATE SKIP LOCKED prevents double-claim)
CREATE INDEX idx_jobs_queue_pending ON background_jobs (queue, run_at)
    WHERE status = 'pending';
```

### Claim query (Kotlin + Exposed / raw SQL)

```sql
UPDATE background_jobs
SET    status = 'running',
       locked_until = now() + interval '5 minutes',
       attempts = attempts + 1,
       updated_at = now()
WHERE  id = (
    SELECT id FROM background_jobs
    WHERE  queue = :queue
      AND  status = 'pending'
      AND  run_at <= now()
    ORDER  BY run_at
    LIMIT  1
    FOR UPDATE SKIP LOCKED
)
RETURNING *;
```

---

## Exponential backoff schedule

```
next_run_at = now() + (base_delay_seconds * 2^(attempts - 1))
```

Recommended defaults: `base_delay_seconds = 60`, `max_attempts = 5`.

| Attempt | Delay |
|---------|-------|
| 1       | 1 min |
| 2       | 2 min |
| 3       | 4 min |
| 4       | 8 min |
| 5 (DLQ) | mark dead |

When `attempts >= max_attempts`, set `status = 'dead'`. Alert on dead-letter growth (route alerting config to adlc-ops).

---

## Idempotency key conventions

| Job type                | Key pattern                                |
|-------------------------|--------------------------------------------|
| Apple ASSN webhook      | `apple-assn:{signedPayload hash SHA-256}`  |
| Google RTDN webhook     | `google-rtdn:{messageId}`                  |
| Liveops calendar event  | `liveops:{eventId}:{scheduledAt ISO8601}`  |
| Sim re-validation       | `sim-revalidate:{matchId}:{replayHash}`    |

Use `INSERT ... ON CONFLICT (idempotency_key) DO NOTHING` to make enqueue idempotent.

---

## Apple ASSN V2 webhook verification steps

1. Parse the incoming POST body as a JWT (`signedPayload` field).
2. Decode the header; extract the `x5c` certificate chain.
3. Verify the chain roots to Apple's CA (embed the expected root; do not fetch it at runtime).
4. Verify the JWT signature with the leaf certificate's public key.
5. Check claims: `iss == "https://appstoreconnect.apple.com"`, `aud == your bundleId`, `exp` not in the past, `environment` matches your expected env (Sandbox vs Production).
6. Respond with HTTP 200 within 5 seconds (queue the work; verify first, enqueue after).
7. If verification fails, return HTTP 200 anyway to prevent Apple from logging a retry storm; log the failure internally.

Apple retries on any non-2xx: at 1 h, 12 h, 24 h, 48 h, 72 h after the previous attempt (5 retries total).

Reference: https://developer.apple.com/documentation/appstoreservernotifications/receiving-app-store-server-notifications

---

## Google RTDN delivery and verification

Google delivers via Cloud Pub/Sub push subscription (HTTP POST to your endpoint). The message body is:

```json
{
  "message": {
    "data": "<base64-encoded DeveloperNotification>",
    "messageId": "136969346945",
    "attributes": {}
  },
  "subscription": "projects/<project>/subscriptions/<sub>"
}
```

Verification:
1. The push endpoint URL is HTTPS and registered in Google Play Console under "Monetization setup > Real-time developer notifications".
2. Google signs the push with a Bearer JWT in the `Authorization` header. Verify it against Google's public OIDC keys (`https://www.googleapis.com/oauth2/v3/certs`); the `iss` claim must be `accounts.google.com` and `email` must match the Pub/Sub service account.
3. Base64-decode `message.data` to get the `DeveloperNotification` JSON.
4. Use `message.messageId` as the idempotency key.
5. Respond HTTP 200 within 10 seconds to acknowledge. Non-200 triggers Pub/Sub retry with exponential backoff up to the subscription's ack deadline.
6. For subscription events, call the Google Play Developer API (`purchases.subscriptionsv2.get`) to fetch authoritative state; do not trust the RTDN payload alone.

Reference: https://developer.android.com/google/play/billing/rtdn-reference

---

## Managed alternatives (skip the schema above)

| Option            | When to use                                             |
|-------------------|---------------------------------------------------------|
| **pg_boss** (npm) | Node/TypeScript backend; wraps Postgres; batteries-included DLQ + cron |
| **BullMQ** (Redis)| If Redis is already present for caching; strong job visibility |
| **Supabase pg_cron** | Supabase project; cron-only (scheduled SQL or Edge Function calls); no general job queue |
| **Inngest**       | Serverless/edge runtime; no self-hosted infra; event-driven step functions |

Do NOT introduce a self-hosted Kafka/RabbitMQ cluster for a solo-scale monolith.

---

## Cron schedule conventions (live-ops calendar)

Scheduled jobs that execute live-ops events (season rotations, limited-time offers) are authored in adlc-monetization (liveops-content). This backend executes them on schedule:

- Store the scheduled fire time in the job's `run_at` column (or equivalent).
- The job handler looks up the live-ops event by ID, applies it (e.g., unlocks content, updates leaderboard config), and marks it done.
- A missed-window guard: if `now() - run_at > tolerance` (e.g., 10 min), log a warning and skip; do not apply a stale event silently.
