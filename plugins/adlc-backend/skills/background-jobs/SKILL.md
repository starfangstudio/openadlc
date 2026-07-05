---
name: background-jobs
description: >-
  This skill should be used when the user asks to "add a background job", "set up a job queue",
  "add a cron job", "schedule recurring work", "add retry logic", "add a dead-letter queue",
  "make a job idempotent", "handle Apple App Store Server Notifications", "handle ASSN V2",
  "handle Google Play Real-time Developer Notifications", "handle RTDN", "handle IAP webhooks",
  "process store webhooks", "add exponential backoff to a job", "set up scheduled live-ops
  events", or "run background work on the server". Designs and implements asynchronous and
  scheduled server-side work for a solo-scale modular monolith: DB-backed job queue or managed
  equivalent, idempotent and retryable jobs with exponential backoff and a dead-letter path,
  scheduled/cron work (live-ops calendar execution), and inbound IAP webhook handling (Apple
  ASSN V2 + Google RTDN). Ties to adlc-monetization for live-ops event authoring and receipt
  validation. Defers deploy/alerting to adlc-ops and security hardening to adlc-security.
version: 0.1.0
---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# background-jobs

Asynchronous and scheduled work for a solo-scale modular monolith: job queue, idempotent retries,
dead-letter path, cron scheduling, and inbound IAP webhooks (Apple ASSN V2 + Google RTDN).

## Step 1: Detect first -- never impose

Inspect the project before adding anything:

```bash
# Existing job scheduler / queue
grep -rn "Quartz\|JobScheduler\|BullMQ\|pg-boss\|pg_cron\|Inngest\|ktor.*schedule\|coroutineScope.*delay" \
    . --include="*.kt" --include="*.ts" --include="*.sql" 2>/dev/null | head -10

# Runtime (Ktor, Node, Supabase Edge, etc.)
grep -rl "io.ktor\|ktor-server" . --include="*.gradle*" --include="*.toml" 2>/dev/null | head -3
grep -rl "express\|fastify" . --include="package.json" 2>/dev/null | head -3
grep -rl "supabase" . --include="*.ts" --include="*.kt" 2>/dev/null | head -3

# Existing webhook endpoints
grep -rn "appstoreservernotifications\|ASSN\|rtdn\|pubsub" \
    . --include="*.kt" --include="*.ts" 2>/dev/null | head -10

# Database (Postgres assumed; mark unknown if different)
grep -rn "postgresql\|postgres\|supabase" . --include="*.gradle*" --include="*.toml" \
    --include="*.env*" 2>/dev/null | head -5
```

Record: existing queue/scheduler (name it), runtime, DB. Mark anything unclear `unknown`.
If a queue system is already present, extend it; do not introduce a second one.

## Step 2: Choose or adopt the job queue

**If nothing exists**, add a DB-backed queue (Postgres `background_jobs` table with
`FOR UPDATE SKIP LOCKED`). Schema, claim query, and managed alternatives are in
[references/background-jobs.md](../../references/background-jobs.md) (DB-backed queue schema section).

Decision shortcuts:
- Ktor + Postgres: use the DB-backed queue from the reference.
- Node/TS + Postgres: `pg-boss` is the natural fit; add it rather than hand-rolling.
- Supabase project, cron-only: `pg_cron` via Supabase dashboard; no custom table needed.
- Redis already present: BullMQ is acceptable.
- Do NOT introduce a self-hosted Kafka/RabbitMQ cluster.

## Step 3: Implement idempotency and retries

Every job handler MUST be idempotent: re-running it on retry must produce the same outcome.

Patterns (pick the right one per job type):
- **Natural deduplication**: check "did this effect already happen?" before applying it
  (e.g., `WHERE entitlement_granted = FALSE`).
- **Idempotency key**: store a unique key per job run; `INSERT ... ON CONFLICT DO NOTHING`
  on the side-effect record.

Retry on any unhandled error: exponential backoff, `max_attempts = 5` (default). When
attempts are exhausted, set `status = 'dead'` (dead-letter). See
[references/background-jobs.md](../../references/background-jobs.md) (backoff schedule + key conventions).

Surface failures explicitly. A silent `catch` that swallows the error is Blocking.
Long-running DB work inside a job must NOT hold a transaction open across network I/O.

## Step 4: Inbound IAP webhooks

### Apple App Store Server Notifications V2

Register an HTTPS endpoint in App Store Connect. Verify first, enqueue after, always
respond HTTP 200 (even on failure to suppress Apple's retry storm).

For the full verification steps and retry schedule, see
[references/background-jobs-detail.md](../../references/background-jobs-detail.md) (Apple ASSN V2 section).

### Google Play Real-time Developer Notifications (RTDN)

Register a Cloud Pub/Sub push subscription pointing to your HTTPS endpoint. Verify the
Bearer JWT, decode `message.data`, respond HTTP 200 within 10 seconds, then enqueue.
Do not trust the RTDN payload alone; confirm state via the Google Play Developer API.

For the full verification steps and message structure, see
[references/background-jobs-detail.md](../../references/background-jobs-detail.md) (Google RTDN section).

## Step 5: Scheduled / cron work

Live-ops events (season rotations, limited-time offers) are authored in adlc-monetization
(`liveops-content` skill). This backend executes them on schedule:

- Store the fire time as `run_at` in the job queue (or a pg_cron schedule).
- The handler loads the event by ID, applies the effect, marks done.
- Missed-window guard: if `now() - run_at > tolerance` (e.g., 10 min), log a warning and
  skip; do not apply a stale event silently.

Alerting on dead-letter growth and cron failure goes to adlc-ops; do not implement
observability infrastructure here.

## Step 6: Verify (pass/fail)

Required proof -- do not mark done without all passing:

1. Enqueue a test job; worker runs it; `status = 'done'`.
2. Enqueue same idempotency key again; second insert is a no-op (`ON CONFLICT DO NOTHING`).
3. Force handler to throw on attempt 1; `status` returns to `'pending'` with backoff `run_at`; `attempts = 1`.
4. Exhaust `max_attempts`; `status = 'dead'`.
5. POST a synthetic Apple ASSN V2 JWT with valid signature; confirm job row created and processed.
6. POST a synthetic Google RTDN Pub/Sub message; confirm job row created and processed.

## Outbound checkpoint

Local work needs no approval. Outbound here (registering a webhook URL in App Store Connect or Google Play Console, running a job against a production DB, deploying to a hosted environment, third-party API with write semantics): stop, present exactly what would go out, and wait for the operator's explicit "yes" before it leaves the machine.

## References

- [references/background-jobs.md](../../references/background-jobs.md) -- DB queue schema, claim query,
  backoff schedule, idempotency key conventions, Apple ASSN V2 verification steps, Google
  RTDN message structure, managed-alternative comparison, cron conventions.
- [references/background-jobs-detail.md](../../references/background-jobs-detail.md) -- full Apple ASSN V2
  verification steps and Google RTDN delivery/verification steps (moved from skill body).
- Apple: Receiving App Store Server Notifications --
  https://developer.apple.com/documentation/appstoreservernotifications/receiving-app-store-server-notifications
- Apple: App Store Server Notifications V2 overview --
  https://developer.apple.com/documentation/appstoreservernotifications
- Google: Real-time developer notifications reference --
  https://developer.android.com/google/play/billing/rtdn-reference
- Supabase: pg_cron extension --
  https://supabase.com/docs/guides/database/extensions/pg_cron
