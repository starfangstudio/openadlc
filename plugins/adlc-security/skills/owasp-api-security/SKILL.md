---
name: owasp-api-security
description: >-
  This skill should be used when the user asks to "review an API for security",
  "check API endpoints for vulnerabilities", "audit REST/GraphQL/gRPC security",
  "OWASP API Top 10", "BOLA / IDOR check", "broken object level authorization",
  "mass assignment", "is this endpoint authorized", "API rate limiting / abuse",
  "SSRF in this handler", or before shipping a new or changed API surface. Maps
  findings to the OWASP API Security Top 10 (2023).
version: 0.1.0
---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# OWASP API Security review (Top 10, 2023)

Audit an API surface against the ten OWASP API Security risks. Investigate
locally, report findings ranked by severity, and propose minimal fixes. Do NOT
push, post, or send anything, local read/edit only unless the operator consents.

## When to run
- A new endpoint, route, resolver, or RPC method is added or changed.
- Auth, object access, input parsing, or outbound-fetch code is touched.
- The user explicitly asks for an API security review or names any item below.

## Scope the surface first
Identify the changed/target API surface before reviewing, review the diff or the
named files, not the whole codebase.
```
git diff --name-only            # what changed
git diff                        # the actual change
```
Locate route/handler definitions (e.g. controllers, routers, GraphQL resolvers,
OpenAPI/proto specs). List every endpoint in scope with method + path + auth
requirement before checking anything.

## The checklist: walk all ten, every time
For each endpoint in scope, check every risk. Most real bugs are API1/API3/API5
(authorization), so spend the most effort there.

| ID | Risk | What to verify in the code |
|---|---|---|
| **API1** | Broken Object Level Authorization (BOLA/IDOR) | Every object accessed by an ID from the request (path/query/body) is checked against the *caller's* ownership/permission, not just "is logged in". The most common and severe API bug. |
| **API2** | Broken Authentication | Token validation (signature, expiry, audience, issuer), no auth bypass on any route, no credentials/keys in URLs, secure password/JWT handling, brute-force protection on login & token endpoints. |
| **API3** | Broken Object Property Level Authorization | No mass assignment (request body can't set fields like `role`, `isAdmin`, `ownerId`); responses don't over-expose properties. Bind to explicit allow-lists / DTOs, not the whole model. |
| **API4** | Unrestricted Resource Consumption | Rate limits, pagination caps, max payload/body size, query depth/complexity limits (GraphQL), timeouts, no unbounded loops/allocations driven by user input. |
| **API5** | Broken Function Level Authorization | Admin/privileged functions enforce role checks server-side; non-admin users can't reach admin routes by guessing paths or changing HTTP method. Default-deny. |
| **API6** | Unrestricted Access to Sensitive Business Flows | Flows that cost the business if automated (signup, purchase, posting, OTP) have abuse protection: CAPTCHA, device/flow limits, anomaly detection. |
| **API7** | Server-Side Request Forgery (SSRF) | Any URL/host taken from input and fetched is validated against an allow-list; block internal IP ranges, redirects, and non-HTTP schemes. |
| **API8** | Security Misconfiguration | TLS enforced, CORS not `*` with credentials, security headers present, verbose errors/stack traces off in prod, unused HTTP methods/debug endpoints disabled, default creds removed. |
| **API9** | Improper Inventory Management | No undocumented/old API versions or `/debug`,`/internal`,`/v1` left exposed; non-prod hosts not internet-reachable; spec matches reality. |
| **API10** | Unsafe Consumption of APIs | Data from third-party/upstream APIs is validated like user input; TLS verified; upstream redirects not blindly followed; timeouts and error handling on the call. |

## Report format
Output findings in this exact structure (no file writes, return as the message):
```
## API security review: <surface>
Endpoints reviewed: <N>

### Findings (by severity)
[CRITICAL] API1 Broken Object Level Authorization, GET /orders/:id
  file:line, <one-line problem>
  Fix: <smallest change that closes it>

[MEDIUM] API4 Unrestricted Resource Consumption, POST /search
  ...

### Clear
APIn, APIn ..., checked, no issue found.
```
Severity: CRITICAL = unauthenticated/cross-tenant data access or RCE-class;
HIGH = authz gap requiring some access; MEDIUM = abuse/DoS/info-leak;
LOW = hardening. Cite `file:line` for every finding. If a risk can't be assessed
from the code in scope, mark it `unknown` and say what's needed, never invent.

## Fix → verify loop
Propose the minimal fix (prefer deleting/tightening over adding). After any edit,
verify with a check that returns pass/fail, a unit test asserting a non-owner gets
403, a build, or a request that should now be rejected. If it can't be verified,
don't claim it's fixed.

## Outbound needs the operator's explicit yes

Local work needs no approval. Outbound here (filing an issue, opening a PR, posting the report to any tracker/chat, running an external scanner that transmits code): stop, present exactly what would go out, and wait for an explicit "yes" (global consent law).

## References
- OWASP API Security Top 10: 2023 (authoritative list): https://owasp.org/API-Security/editions/2023/en/0x11-t10/
- OWASP API Security Project home: https://owasp.org/www-project-api-security/
