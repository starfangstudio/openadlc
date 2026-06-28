<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
# adlc-backend-cloud

The enterprise / team-scale backend tier. The opt-in scale-up from `adlc-backend`'s solo-scale modular monolith, for when real scale and a team justify the operational cost. Detect-first.

## Boundaries (own little, route the rest)
- `adlc-backend`: the solo-scale modular monolith. Start there; this pack is the deliberate step up, not the default.
- Observability / monitoring / CI-CD authoring -> `adlc-ops`. Security hardening -> `adlc-security`. Data modeling / migrations / query depth -> `adlc-database`.

## Skills
- `containers`: production Dockerfiles (multi-stage, slim, non-root, healthcheck, layer cache), compose for local.
- `orchestration`: Kubernetes (deployments, services, ingress, HPA, resource limits, probes, config / secrets) or a managed orchestrator; pragmatic, not a CNCF zoo.
- `iac`: infrastructure as code (Terraform / Pulumi): state, modules, per-environment, plan / apply discipline, drift.
- `messaging`: async messaging + streaming (queues / Kafka): events, at-least-once + idempotency, ordering, backpressure, dead-letter, the outbox pattern.
- `distributed-data`: data at scale, read replicas, partitioning / sharding, distributed caching, and the consistency trade-offs and failure modes.
- `progressive-delivery`: safe rollout, canary, blue-green, feature flags, health gates, automated rollback.

## Agents
- `backend-cloud-architect`: design the scaled system (compute, data, messaging, delivery). Read-only, produces a plan.
- `backend-cloud-reviewer`: review scale changes (orchestration, IaC, messaging correctness, rollout safety) before any outbound step.

## Status
Stable. Six skills plus reviewer and architect agents, all detect-first with verifiable checks. One known gap: team-scale CI/CD authoring routes to `adlc-ops`.
