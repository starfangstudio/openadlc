---
name: api-design
description: >-
  Designs a pragmatic REST contract for a solo-scale mobile backend: resource/verb modeling,
  RFC 9457 error envelope, URL versioning, cursor pagination, idempotency keys, and an
  OpenAPI 3.1 spec as the source of truth. Use when the user asks to "design the API",
  "add a REST endpoint", "add idempotency keys", "handle pagination", or
  "generate a client from the spec".
version: 0.1.0
---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# api-design

Design a pragmatic, solo-scale API contract for a mobile backend. OpenAPI 3.1 spec is the
source of truth; the implementation conforms to it, not the reverse.

## Step 1: Detect first -- never impose

Inspect what already exists before designing anything:

```bash
# Existing routes
grep -rn "routing\|route\|get(\|post(\|put(\|delete(" src/ \
  --include="*.kt" --include="*.ts" --include="*.go" | head -20

# Existing spec, error shapes, idempotency, versioning signals
find . -name "openapi.yaml" -o -name "openapi.json" -o -name "swagger.yaml" | head -5
grep -rn "Problem\|ErrorResponse\|ApiError" src/ | head -10
grep -rn "Idempotency-Key\|idempotencyKey" src/ | head -5
grep -rn '"/v[0-9]' src/ | head -5
```

Record: protocol (REST / gRPC / tRPC / PostgREST), existing error shape, whether an OpenAPI
spec exists, idempotency and versioning status. Mark unknowns `unknown`; ask before
restructuring an existing contract.

## Step 2: REST vs RPC -- choose by fit

Default to REST for mobile clients. Use RPC (tRPC, gRPC) only when you control both ends in
a typed monorepo (tRPC) or need binary streaming with tight latency (gRPC). Do not introduce
gRPC for a Kotlin/JVM or Supabase backend with standard mobile clients.

## Step 3: Resource and verb modeling

See [references/api-conventions.md](references/api-conventions.md) (Resource + verb modeling).

- Plural nouns, max 3 URI levels: `GET /v1/leaderboards/{id}/scores`.
- Custom non-CRUD actions: colon-suffix on the resource noun: `POST /v1/sessions/{id}:validate-replay`.
- Never embed verbs in noun segments.
- Version prefix from day one: `/v1/`. Additive changes stay in the same version; breaking
  changes get a new version with a `Sunset` header on the old path.

## Step 4: Error envelope (RFC 9457)

Adopt RFC 9457 Problem Details for all error responses (`application/problem+json`). See
[references/api-conventions.md](references/api-conventions.md) (Error envelope section) for the exact
JSON shape, field rules, validation-failure format, and the hard rule: never return 200 for
errors; include `traceId` in `extensions`; keep `type` URIs permanently stable.

## Step 5: Idempotency keys

Required on every POST with money or irreversible side-effects: IAP receipt validation, score
submission, match outcome recording, currency grants. Header: `Idempotency-Key: <UUIDv4>`.

See [references/api-conventions.md](references/api-conventions.md) (Idempotency keys) for the full
server behaviour spec. Critical rule: validation failures (400/422) are not stored; the
client may retry with the same key after fixing the body.

Storage: Redis / Upstash / short-TTL Postgres table keyed on `sha256(userId + key)`, retained >= 24 hours.

## Step 6: Pagination and optimistic concurrency

**Pagination:** cursor (keyset) default for leaderboards and feeds; offset only for small
bounded admin lists (<10k rows). See [references/api-conventions.md](references/api-conventions.md)
(Pagination) for the response envelope.

**Optimistic concurrency:** `ETag` + `If-Match` for resources two clients might mutate
concurrently (profile, config, save state). Return 412 on mismatch; client re-fetches and
re-submits. Append-only resources need only idempotency keys, not ETags.

## Step 7: OpenAPI 3.1 as the contract

Write or update `openapi.yaml` spec-first. Every response schema must be fully defined; no
inline `{}`. Every mutating endpoint requiring an idempotency key declares it in `parameters`.
Auth (`securitySchemes`) is declared in the spec but wired by the `auth-identity` skill.

Generate clients after any spec change:

```bash
# Validate spec
npx @stoplight/spectral-cli lint openapi.yaml --ruleset @stoplight/spectral-oas

# TypeScript client (React Native)
npx @openapitools/openapi-generator-cli generate \
  -i openapi.yaml -g typescript-fetch -o clients/ts

# Kotlin client (Android)
npx @openapitools/openapi-generator-cli generate \
  -i openapi.yaml -g kotlin -o clients/kotlin
```

## Step 8: Verify (pass/fail)

```bash
# Spec must lint clean
npx @stoplight/spectral-cli lint openapi.yaml --ruleset @stoplight/spectral-oas

# At least one generated client must compile
cd clients/ts && npm install && npx tsc --noEmit
```

Do not mark done without clean lint and a compiling generated client.

## Scope boundaries

- Auth headers / JWT validation: `auth-identity` skill.
- SQL injection, authz enforcement, rate-limiting: `adlc-security`.
- IAP client-side purchase flow: `adlc-monetization` (this skill covers server-side receipt
  validation endpoints and their idempotency handling only).
- Deploy, TLS, gateway: `adlc-ops`.

## Outbound checkpoint

Local work needs no approval. Outbound here (third-party write API such as store receipt validation, deploying to a remote environment, schema changes to a shared or production database): stop, present exactly what would go out, and wait for the operator's explicit "yes" before it leaves the machine.

## References

- [references/api-conventions.md](references/api-conventions.md) -- error envelope, versioning,
  idempotency, pagination, optimistic concurrency, resource modeling.
- RFC 9457 Problem Details for HTTP APIs -- https://www.rfc-editor.org/rfc/rfc9457
- REST API Design 2026 Engineering Reference --
  https://www.digitalapplied.com/blog/rest-api-design-2026-engineering-reference-best-practices
- OpenAPI 3.1 Specification -- https://spec.openapis.org/oas/v3.1.0
- OpenAPI Generator -- https://openapi-generator.tech
- Stoplight Spectral linter -- https://docs.stoplight.io/docs/spectral
