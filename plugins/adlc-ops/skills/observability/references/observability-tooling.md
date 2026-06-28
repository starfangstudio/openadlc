<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
# Observability tooling reference (solo-scale)

Loaded on demand from the `observability` skill. Covers managed backend options,
OpenTelemetry wire-up, uptime tooling, and SLO/error-budget mechanics.

---

## Managed telemetry backends (pick one, do not self-host)

| Backend | Free tier | OTLP native | Notes |
|---|---|---|---|
| Grafana Cloud | 50 GB logs, 10k series, 14-day retention | Yes (via Alloy) | Full stack: metrics + logs + traces; Alloy replaces OTel Collector |
| Honeycomb | 20M events/month | Yes | OTel-native; best for trace-first debugging |
| Axiom | 0.5 TB/month ingest, 30-day retention | Yes | Strong for logs + traces; simple pricing |
| Dash0 | Free tier available | Yes (OTel-first) | OTel-native by design; built by OTel contributors |

**Recommendation for solo dev:** Grafana Cloud free tier covers a launched mobile backend
comfortably. Honeycomb if traces are the primary debugging tool. Both accept OTLP; swap
with zero app-code change.

---

## OpenTelemetry SDK wire-up (backend service)

Install the SDK for your language. Auto-instrumentation covers HTTP, DB, and queue calls
without code changes; manual spans cover business logic.

### Node.js (example)

```bash
npm install @opentelemetry/sdk-node \
  @opentelemetry/auto-instrumentations-node \
  @opentelemetry/exporter-trace-otlp-http
```

```js
// otel.js -- load before anything else (node --require ./otel.js server.js)
const { NodeSDK } = require('@opentelemetry/sdk-node');
const { getNodeAutoInstrumentations } = require('@opentelemetry/auto-instrumentations-node');
const { OTLPTraceExporter } = require('@opentelemetry/exporter-trace-otlp-http');

const sdk = new NodeSDK({
  traceExporter: new OTLPTraceExporter({
    url: process.env.OTEL_EXPORTER_OTLP_ENDPOINT,  // set per backend
  }),
  instrumentations: [getNodeAutoInstrumentations()],
});
sdk.start();
```

Set env vars at deploy time (Railway / Fly / Cloud Run secret):
```
OTEL_EXPORTER_OTLP_ENDPOINT=https://<backend-ingest-url>
OTEL_EXPORTER_OTLP_HEADERS=Authorization=Bearer <token>
OTEL_SERVICE_NAME=my-api
OTEL_RESOURCE_ATTRIBUTES=deployment.environment=production
```

For other languages, see https://opentelemetry.io/docs/getting-started/dev/

---

## Health endpoint convention

```
GET /health
200 OK  { "status": "ok", "version": "1.2.3", "db": "ok" }
503     { "status": "degraded", "db": "timeout" }
```

The check MUST probe real dependencies (DB ping, cache ping). A 200 that bypasses
dependencies is a false green; the uptime monitor will not catch a DB outage.

---

## Uptime monitoring options (external, free tiers)

| Tool | Free monitors | Check interval | Status page | Notes |
|---|---|---|---|---|
| UptimeRobot | 50 | 5 min | 1 (free) | Personal use free; paid from $7/mo for commercial |
| BetterStack (Uptime) | 10 | 3 min | 1 | Clean status pages; incident management built in |
| Freshping | 50 | 1 min | 1 | Free tier; 1-minute checks are good |
| ReliableUptime | 15 | 1 min | 1 | Free; HTTP/Ping/TCP/DNS + SSL |

**Pick one.** Configure it to hit `/health` every 1-3 min. Point alerts to a channel
you actually read (email, Slack, Telegram). The status page URL goes in the product's
support docs so users can self-serve during an outage.

---

## SLO and error budget (practical minimum)

### Define "up" before launch

Write this down (a comment in code or a `SLO.md` at the repo root):

```
SLI:  success_rate = successful_requests / total_requests  (5xx excluded from numerator)
SLO:  99.5% over a rolling 28-day window
Error budget: 0.5% = ~3.6 hours downtime/month acceptable
```

Adjust SLO to what the product actually needs. 99.5% is realistic for a managed-PaaS
solo deploy; 99.9% requires incident response under 1.5 min and is rarely worth the cost.

### Track the budget

Most managed backends (Grafana Cloud, Honeycomb, Datadog) have built-in SLO widgets.
In Grafana Cloud: Observability > SLOs > New SLO, point at your success-rate metric.

Alert when **error budget burn rate** exceeds 2x over 1 hour (fast burn) or 1x over
6 hours (slow burn). Do NOT alert on raw error count -- that's noise.

### When budget is exhausted

Stop shipping features. Fix reliability first. Resume when budget recovers. This is the
entire error-budget policy for a solo dev.

---

## Alert hygiene rules

- Alert on user-impacting symptoms (5xx rate, p99 latency > SLO threshold, health check
  failing), NOT on CPU or memory directly.
- Every alert must have a runbook link or inline note: what to check, what to do.
- Default: one alert channel (email or chat). Add PagerDuty/phone call only if revenue
  depends on <5-minute MTTR.
- Silence noisy alerts immediately; a silenced alert is evidence the SLO is wrong or
  the metric is wrong -- fix the root cause.
