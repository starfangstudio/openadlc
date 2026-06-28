---
name: cloud-deploy
description: >-
  This skill should be used when the operator asks to "deploy a backend", "deploy a
  service", "host this API", "get this running in the cloud", "pick a hosting platform",
  "set up a staging environment", "wire up environment variables / secrets", "add a
  managed database", "deploy to Railway", "deploy to Cloud Run", "deploy to Render",
  "deploy to Fly.io", "deploy to Vercel", "use Supabase as a backend", "set up CI/CD
  deploy pipeline", "check my deploy is live", "verify the deployment is healthy", or
  any question about managed PaaS cost or platform choice for a solo-scale product.
  Covers platform selection, container vs buildpack vs serverless, environments, secrets,
  managed databases, cost awareness, and health verification. Explicitly steers away
  from Kubernetes, microservices, and heavy Terraform at solo scale.
version: 0.1.0
---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# Cloud deploy (solo-scale, managed PaaS)

Ship backends on managed platforms. No Kubernetes, no self-hosted databases, no Terraform stacks unless the operator explicitly asks and understands the ops burden. A modular monolith on one managed service is the right answer at this scale.

## Detect first

Inspect what is already in the repo and note what is unknown:

```bash
# Dockerfile or buildpack?
ls Dockerfile docker-compose.yml .dockerignore 2>/dev/null || echo "no Dockerfile"
# Existing platform config
ls railway.json fly.toml render.yaml vercel.json .vercel 2>/dev/null || echo "no platform config found"
# Existing CI that deploys
grep -r "railway\|fly\|render\|cloud.run\|gcloud\|vercel" .github/workflows/ 2>/dev/null | head -20
# Env vars already declared
ls .env .env.example .env.staging .env.production 2>/dev/null
```

Record: existing platform (if any), deploy unit (Dockerfile / buildpack / serverless), env vars declared vs missing. Mark anything not found `unknown`; never assume a platform is configured if no config file is present.

## Pick a platform

See [references/managed-paas-options.md](references/managed-paas-options.md) for the full fit matrix, cost table, and the explicit list of what to reject at solo scale. Short version:

- **Railway**: default for most backends. Usage-based, best DX, managed Postgres in the same project.
- **Render**: managed Postgres with PITR + automated backups matters; slightly more config.
- **Fly.io**: global edge latency is the hard requirement; Docker-native.
- **Google Cloud Run**: intermittent / event-driven workloads, pay-per-request, scales to zero. Best when already in GCP (Firebase, Crashlytics).
- **Vercel**: Next.js front-end + serverless API routes; deploy from Git.
- **Supabase**: auth + Postgres + storage with no server to maintain; pair with Vercel for the front-end.

Never recommend Kubernetes, microservices, or a self-hosted Postgres unless the operator explicitly asks and you explain the ops overhead clearly first.

## Deploy unit

Choose one:

| Signal | Unit |
|---|---|
| `Dockerfile` present | Container: push image or let platform build it |
| No Dockerfile, standard Node/Python/Go/Ruby | Buildpack: platform detects language automatically |
| Next.js / edge functions / static + API | Serverless: Vercel or Cloud Run with `--source` |

For Railway and Render: push to Git, platform builds automatically. For Cloud Run:

```bash
# Build + push container, then deploy
gcloud builds submit --tag gcr.io/<PROJECT>/<SERVICE>:<TAG>
gcloud run deploy <SERVICE> \
  --image gcr.io/<PROJECT>/<SERVICE>:<TAG> \
  --region <REGION> \
  --allow-unauthenticated    # remove if auth required
```

## Environments and secrets

Two environments minimum at launch: `staging` (auto-deploy from `main`) and `production` (promote after health check). Keep them in separate Railway projects / Render services / Cloud Run service names.

Secrets live in the platform's secret store, never in git:

- Railway: project variables (UI or `railway variables set KEY=VALUE`)
- Render: environment groups
- Cloud Run: Secret Manager (`gcloud secrets create ...` then reference in the service)
- Vercel: environment variables per environment in the dashboard or `vercel env add`

Provide an `.env.example` with every key listed but no values, committed to git as the canonical schema.

## Managed database

Use the platform's managed Postgres. Do not self-host on a VPS/Droplet.

- Railway: add a Postgres plugin to the project; `DATABASE_URL` is auto-injected.
- Render: add a Postgres service; copy the internal connection string.
- Supabase: use the Supabase project's connection string (pooled via PgBouncer for serverless).
- Cloud Run: use Cloud SQL with the Cloud SQL Auth Proxy sidecar or the built-in connector.

Run migrations as a one-off command (Railway: `railway run npx prisma migrate deploy`; Cloud Run: a one-shot Job).

## Verify: deploy is reachable and healthy

After every deploy, confirm with a pass/fail check before declaring it done:

```bash
# Smoke-test the health endpoint (replace URL and expected value)
curl -sf https://<SERVICE_URL>/health | grep -q '"status":"ok"' \
  && echo "PASS: service healthy" \
  || { echo "FAIL: health check failed"; exit 1; }

# Check HTTP 200 on the root or a known path
curl -o /dev/null -sw "%{http_code}" https://<SERVICE_URL>/ | grep -q "^200$" \
  && echo "PASS: 200 OK" \
  || echo "FAIL: unexpected status"
```

If the service has no `/health` endpoint, add one. A deploy is not done until the health check passes.

## Cost awareness

Every platform choice has a cost trigger. Flag these before provisioning:

- Railway Hobby: $5 credit/mo; usage above that is billed. A single always-on service + Postgres typically costs $10-15/mo.
- Render Starter: $7/mo per web service + $7/mo per Postgres instance.
- Cloud Run: free tier covers 2M req/mo + 360K vCPU-seconds; beyond that is pay-per-use.
- Supabase Pro: $25/mo; Free pauses inactive projects after 1 week.
- Vercel Pro: $20/mo per seat; Hobby is free for personal projects.

Present projected monthly cost to the operator before provisioning any paid resource.

## Outbound approval

Local work needs no approval. Outbound here (provisioning a paid cloud resource, deploying to a live environment, enabling an SDK that sends data to a third party, or creating/modifying remote infrastructure): stop and ask the operator for an explicit yes. Present exactly what would be created (platform, service, region, estimated cost) and wait for the yes before doing it (global consent law).

## References

- [references/managed-paas-options.md](references/managed-paas-options.md): full platform fit matrix, cost table, what to reject at solo scale
- Railway docs: https://docs.railway.com
- Render docs: https://render.com/docs
- Fly.io docs: https://fly.io/docs
- Google Cloud Run docs: https://cloud.google.com/run/docs
- Vercel docs: https://vercel.com/docs
- Supabase docs: https://supabase.com/docs
