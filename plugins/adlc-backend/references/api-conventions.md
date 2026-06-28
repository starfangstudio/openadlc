<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
# API Conventions Reference

Companion to the `api-design` skill. Copy-ready patterns; keep this file as the source of truth when the skill cites it.

---

## Error envelope (RFC 9457)

Use RFC 9457 Problem Details for all error responses. Content-Type: `application/problem+json`.

```json
{
  "type": "https://api.example.com/problems/resource-not-found",
  "title": "Resource not found",
  "status": 404,
  "detail": "Game session 'abc123' does not exist or has expired.",
  "instance": "/v1/sessions/abc123",
  "extensions": {
    "traceId": "4bf92f3577b34da6"
  }
}
```

Rules:
- `type` is a stable URI clients can branch on programmatically; never change it once shipped.
- `detail` is developer-facing: say what the client can do to fix it.
- Validation failures return 422 and include all field errors at once in `extensions.errors` (array).
- Never return 200 with an error body. 4xx = client fault, 5xx = server fault.
- `traceId` in `extensions` enables log correlation without leaking internals.

```json
{
  "type": "https://api.example.com/problems/validation-failed",
  "title": "Validation failed",
  "status": 422,
  "detail": "Request body failed schema validation.",
  "instance": "/v1/scores",
  "extensions": {
    "errors": [
      { "field": "score", "message": "must be >= 0" },
      { "field": "sessionId", "message": "required" }
    ]
  }
}
```

---

## Versioning

Strategy: **URL path prefix** (`/v1/`, `/v2/`). Chosen for mobile clients: the version is explicit in every request, no header negotiation, easy to route at the proxy layer.

Rules:
- Start at `/v1/` from day one; retrofitting costs more than the up-front prefix.
- A new version is warranted for breaking changes only (field removals, renamed resources, changed semantics). Additive changes (new optional fields) are non-breaking; ship in the same version.
- Maintain the previous version for one deprecation window (announced via `Deprecation` + `Sunset` response headers) before removal.
- Never silently change behavior under an existing version path.

```
Deprecation: Sat, 01 Jan 2027 00:00:00 GMT
Sunset: Sat, 01 Jul 2027 00:00:00 GMT
Link: <https://docs.example.com/migration/v1-to-v2>; rel="deprecation"
```

---

## Idempotency keys

Required on: POST endpoints that create resources or trigger money/state side-effects (IAP validation, score submission, match outcome recording, virtual currency grants).

Header: `Idempotency-Key: <UUIDv4>` (255 char max).

Server behaviour:
1. On first receipt: execute, store `(key, status, response_body)` keyed on `(userId, key)`.
2. On duplicate (same key + same user): return stored response; do not re-execute.
3. Retain stored results >= 24 hours.
4. Return 409 if the same key arrives with a different request body (caller bug).
5. Validation failures (400/422) are NOT stored. The client may retry with the same key after fixing the body. Document this clearly.

```
POST /v1/iap/validate
Idempotency-Key: 550e8400-e29b-41d4-a716-446655440000
```

Storage: a fast K/V store (Redis, Upstash, or the same Postgres with a short-TTL table) keyed on `sha256(userId + idempotencyKey)`.

---

## Pagination

| Pattern | Use when | Caveat |
|---|---|---|
| Cursor (keyset) | Leaderboards, feeds, large/unbounded sets | No random-page access |
| Offset (`?page=&limit=`) | Admin UIs, small bounded lists (<10k rows) | Avoid `OFFSET` > a few thousand |

Cursor response envelope:
```json
{
  "data": [...],
  "pagination": {
    "nextCursor": "eyJpZCI6MTAwfQ==",
    "hasMore": true
  }
}
```

Cursor is opaque to the client (base64-encoded JSON server-side). Never expose raw DB ids in cursors.

---

## Optimistic concurrency

Use `ETag` + `If-Match` for any resource that two clients (or two retries) might mutate concurrently. Typical targets: user profile, game config, save state.

1. `GET /v1/profiles/me` returns `ETag: "v42"`.
2. Client sends `PUT /v1/profiles/me` with `If-Match: "v42"`.
3. Server checks: if version matches, apply + return new ETag; else return 412.
4. Client on 412: re-fetch, merge, re-submit.

For append-only resources (score submissions, event log) idempotency keys are sufficient; no ETag needed.

---

## Resource + verb modeling

- Collections: plural nouns, max 3 URI levels deep.
  - `GET /v1/leaderboards/{leaderboardId}/scores`
- Custom actions that don't fit CRUD: colon-suffix on the resource.
  - `POST /v1/sessions/{sessionId}:validate-replay`
  - `POST /v1/iap/receipts:validate`
- Never embed verbs in noun segments (`/processScore`, `/doValidate`).
- Query params for filtering/sorting/pagination; never encode them in the path.
