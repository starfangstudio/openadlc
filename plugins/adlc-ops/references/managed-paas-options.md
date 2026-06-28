<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
# Managed PaaS options (solo-scale reference)

Use this table to pick a platform. Pick ONE managed platform per service; do not split across providers until you have a concrete reason.

## Platform fit matrix

| Platform | Best fit | Deployment unit | Free tier | Typical solo cost |
|---|---|---|---|---|
| **Railway** | Default backend: Node/Python/Go/etc. + Postgres, simple DX, usage-based | Buildpack or Dockerfile | $5 credit/mo (Hobby) | $10-15/mo |
| **Render** | Backend that needs managed Postgres with PITR + automated backups | Buildpack or Dockerfile | Web services spin down on free | $7/mo (Starter web) + $7/mo (Postgres) |
| **Fly.io** | Global edge latency matters; full Docker control | Dockerfile (Fly Machines) | Trial only | $5-20/mo |
| **Google Cloud Run** | Intermittent workloads, containers, pay-per-request; 0-to-N autoscale | Container image | 2M req/mo + 360K vCPU-sec free (never expires) | $0-5/mo at low traffic |
| **Vercel** | Edge functions, Next.js front-ends, static sites + serverless API routes | Git push or CLI | Generous Hobby tier | $0 (Hobby) / $20/mo (Pro) |
| **Supabase** | Backend-as-a-Service: Postgres + auth + storage + edge functions, no server to manage | Managed (no deploy step for DB/auth) | Free (2 paused projects) | $25/mo (Pro) |

## When to pick what

- **Default new backend (REST/GraphQL + Postgres):** Railway. `railway up` from a Dockerfile or auto-detected buildpack, managed Postgres in the same project, env vars in the dashboard, preview environments per branch.
- **Need managed Postgres with proper PITR + backups:** Render. Stronger database story than Railway at the cost of slightly more configuration.
- **Ultra-low latency global reads / edge compute:** Fly.io. Requires learning `flyctl` and `fly.toml`; more operational surface.
- **Serverless, infrequent calls, zero cold-idle cost:** Cloud Run. Deploy a container from Artifact Registry; traffic-based autoscale to zero. Best when you already have a GCP footprint (Firebase, Crashlytics).
- **Front-end + API routes in Next.js:** Vercel. The canonical platform for Next.js; deploy from Git, zero config, CDN-backed.
- **Auth + Postgres + file storage without a custom server:** Supabase. Use the client SDK; no server to maintain. Combine with Vercel for the front-end.

## What to reject at solo scale

- **Kubernetes (GKE, EKS, AKS):** cluster overhead, node cost, and ops burden are disproportionate. Not appropriate until you have a dedicated platform team.
- **Microservices:** a modular monolith on one Railway/Cloud Run service handles far more load than a solo op needs. Split only when a bounded service has a genuinely independent scaling curve and you have the observability to run multiple services.
- **Custom Terraform stacks:** managed platforms already provision the infra. Use their UI/CLI to manage resources; save Terraform for the rare case you need multi-cloud or resources no managed platform exposes.
- **Self-hosted databases (EC2/Droplet):** no automated backup, no PITR, no managed failover. Use the platform's managed DB or Supabase.

## Secrets management

Store secrets in the platform's env-var / secret store (Railway variables, Render environment groups, Cloud Run Secret Manager integration). Never commit secrets to git, never embed in the Docker image at build time.

## Environment pattern (two envs minimum at launch)

| Env | Hosting | Purpose |
|---|---|---|
| `staging` | Same platform, separate Railway project / Render service / Cloud Run revision tag | Integration tests, QA, pre-deploy smoke |
| `production` | Same platform, production project / service | Live traffic |

Auto-deploy `main` → staging. Gate promotion to production behind a health check (see the deploy health section in the skill).

## References

- Railway docs: https://docs.railway.com
- Render docs: https://render.com/docs
- Fly.io docs: https://fly.io/docs
- Google Cloud Run: https://cloud.google.com/run/docs
- Vercel docs: https://vercel.com/docs
- Supabase docs: https://supabase.com/docs
