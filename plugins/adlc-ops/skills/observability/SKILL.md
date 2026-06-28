---
name: observability
description: >-
  Wires up solo-scale observability: health endpoint, external uptime monitor, status
  page, OpenTelemetry instrumentation to a managed backend, and a minimum-viable SLO.
  Use when asked to "set up monitoring", "add uptime monitoring", "wire up traces or
  metrics", "define an SLO or error budget", or "know when the service is degrading".
version: 0.1.0
---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# Observability (solo-scale)

Know when a launched service is down or degrading before users report it. The goal is
signal that pages on real user impact, not noise. Do NOT build a full observability
platform; use managed services and stay on free/cheap tiers until traffic demands more.

## Detect first

Inspect the repo and running infra before adding anything:

```bash
# Health endpoint?
grep -r "/health" . --include="*.ts" --include="*.js" --include="*.py" \
  --include="*.go" -l 2>/dev/null | head -10

# OpenTelemetry already wired?
grep -r "opentelemetry\|@opentelemetry\|otel" package.json requirements.txt \
  go.mod Gemfile 2>/dev/null | head -10

# Existing uptime monitor config or status page reference?
grep -rli "uptimerobot\|betterstack\|betteruptime\|freshping\|statuspage" . 2>/dev/null

# CI/deploy env vars for telemetry?
grep -rli "OTEL_\|SENTRY_\|DATADOG" .env* *.env docker-compose* fly.toml \
  railway.toml render.yaml 2>/dev/null
```

Record what exists. Mark anything not found `unknown`. Never invent config that is
not present.

## Step 1: Health endpoint

Add a `/health` route that probes real dependencies (DB ping, cache ping):

- Returns `200 { "status": "ok", "version": "x.y.z" }` when all deps respond.
- Returns `503 { "status": "degraded", "db": "timeout" }` on any dep failure.

A 200 that skips dependency checks is a false green. See
[references/observability-tooling.md](references/observability-tooling.md) for the exact shape.

## Step 2: External uptime monitor + status page

Point an external monitor at `/health` (do NOT use a self-hosted checker):

1. Pick a tool: BetterStack (Better Uptime), UptimeRobot, or Freshping (all have
   adequate free tiers for a solo product -- see the reference for the comparison).
2. Set check interval to 1-3 min on the `/health` URL.
3. Enable the built-in status page; put its URL in the product's support docs.
4. Configure one alert channel (email or chat) that you actually read.

Provisioning the external monitor is outbound: get the operator's explicit yes first (see Outbound approval below).

## Step 3: OpenTelemetry instrumentation

Instrument the backend service once; point it at a managed backend. Do NOT self-host
Prometheus/Grafana; the free tiers of Grafana Cloud, Honeycomb, or Axiom are
sufficient for a solo launched product.

Wire-up steps (language-specific commands in the reference):

1. Install the OTel SDK + auto-instrumentation library for the runtime.
2. Load the SDK before your app (env var or entrypoint wrapper).
3. Set `OTEL_EXPORTER_OTLP_ENDPOINT`, `OTEL_EXPORTER_OTLP_HEADERS`,
   `OTEL_SERVICE_NAME`, and `OTEL_RESOURCE_ATTRIBUTES=deployment.environment=production`
   as secrets in the deploy platform (Railway / Fly / Cloud Run / Render / Vercel).
4. Auto-instrumentation covers HTTP, DB, and queue calls; add a manual span only for
   business-critical paths that are not auto-covered.

The three pillars from one SDK:
- **Metrics**: request rate, error rate, latency (p50/p95/p99) -- auto-collected.
- **Logs**: structured log export to the same backend (add OTel log appender or pipe
  stdout to the backend's log drain).
- **Traces**: distributed call graphs -- auto-collected for HTTP/DB/queue.

## Step 4: SLO and error budget (minimum viable)

Before launch, write down "what does up mean" (a `SLO.md` at the repo root or a
comment in the deploy config):

```
SLI:  success_rate = successful_requests / total_requests  (5xx = failure)
SLO:  99.5% over a rolling 28-day window
Error budget: 0.5% = ~3.6 hours downtime/month
```

99.5% is realistic for a managed-PaaS solo deploy. Do NOT target 99.9% unless revenue
depends on sub-1.5-minute incident response -- the ops cost is not worth it.

Track the budget in the managed backend's SLO widget (Grafana Cloud: Observability >
SLOs; Honeycomb: SLOs tab). Alert on burn rate, not raw error count.

## Step 5: Alerting rules

- Alert on `5xx rate > 1%` sustained 5 min OR health check failing 2 consecutive checks.
- Alert on `p99 latency > 2x baseline` sustained 10 min.
- Alert on **error-budget burn rate > 2x** over 1 hour (fast burn).
- Do NOT alert on CPU, memory, or disk directly -- alert on user-impacting symptoms.
- Every alert must carry a runbook note: what to check first, what command to run.
- Silence a noisy alert immediately, then fix what made it noisy.

## Verify

Run this checklist before calling observability "done":

- [ ] `curl -f https://<service>/health` returns `200` from the deploy platform.
- [ ] Uptime monitor shows the check as passing; status page is publicly reachable.
- [ ] A synthetic test fires an alert: temporarily return `503` from `/health`,
  confirm the alert arrives, restore `200`.
- [ ] At least one trace visible in the managed backend UI for a real request.
- [ ] SLO definition written down and budget widget configured.

## Out of scope

Mobile crash monitoring (android-crashlytics / ios-crashlytics skills), test strategy
(adlc-testing), deploy readiness gate (`gate-deployment-readiness`), and privacy/PII
doctrine for telemetry payloads (adlc-privacy).

## Outbound approval

Local work needs no approval. Outbound here (provisioning an external monitoring service, enabling an SDK that sends data to a third-party backend, creating a status page, or setting secrets in the deploy platform): stop and ask the operator for an explicit yes. Present exactly what would go out and wait for the yes before doing it (global consent law).

## References

- [references/observability-tooling.md](references/observability-tooling.md) -- backend comparison,
  OTel SDK wire-up, health endpoint shape, uptime tools, and SLO/error-budget mechanics.
- OpenTelemetry, "Getting started for developers": https://opentelemetry.io/docs/getting-started/dev/
- OpenTelemetry, "What is OpenTelemetry?": https://opentelemetry.io/docs/what-is-opentelemetry/
- Google SRE Book, "Service Level Objectives": https://sre.google/sre-book/service-level-objectives/
- Google SRE Workbook, "Implementing SLOs": https://sre.google/workbook/implementing-slos/
