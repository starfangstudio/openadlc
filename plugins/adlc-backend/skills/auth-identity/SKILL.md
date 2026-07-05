---
name: auth-identity
description: >-
  This skill should be used when the user asks to "set up accounts", "add authentication",
  "implement login", "add social sign-in", "add Sign in with Apple", "add Google Sign-In",
  "implement guest accounts", "implement device accounts", "link a guest to a real account",
  "set up JWT tokens", "add refresh token rotation", "revoke tokens", "implement logout",
  "add role-based access control", "add authorization checks", "hash passwords",
  "implement email login", "add auth to the backend", "protect an endpoint", or
  "implement the account model". Designs and implements accounts, authentication, and
  authorization for mobile products: guest/device accounts for games with optional social
  upgrade, social sign-in (Sign in with Apple + Google), JWT access + refresh tokens with
  rotation and revocation, password hashing via Argon2id when email auth is needed, and
  role/scope checks at the service boundary. Defers injection/secret hardening to
  adlc-security and deploy/observability to adlc-ops.
version: 0.1.0
---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# auth-identity

Design and implement accounts, authn, and authz for mobile products.

## Step 1: Detect first -- never impose

Inspect the existing project before writing any code:

```bash
# Framework
grep -r "ktor\|spring\|supabase\|firebase" . \
  --include="*.kts" --include="*.gradle" --include="*.toml" -l | head -5
# Existing auth signals
grep -rn "jwt\|argon2\|bcrypt\|oauth\|oidc\|identity\|session" . \
  --include="*.kts" --include="*.sql" --include="*.kt" -l | head -10
# DB migrations
find . -name "*.sql" -path "*/migration*" | sort | tail -10
```

Record: framework, auth lib, existing token tables, existing social wiring. Mark anything
unclear `unknown`; ask before changing existing auth. If using Supabase or Firebase Auth,
confirm delegated features before adding custom code.

## Step 2: Account model

Games: use the guest-first (device account) pattern -- players start without friction,
then optionally link a social identity. Utility apps: skip the guest phase, create a
`user` account on first login.

See [references/auth-identity.md](../../references/auth-identity.md) (Account model section) for the
`Account` + `Identity` table schema and the link/merge flow.

## Step 3: Social sign-in

Implement server-side OIDC token verification. Never trust the client's identity claim.

**Sign in with Apple** -- required when offering any third-party social login on iOS
(App Store guideline 4.8: the equivalent must limit data to name + email and allow
email relay; Sign in with Apple satisfies this natively).

```
POST /auth/apple  { identityToken }
  -> fetch Apple JWKs -> verify JWT (iss, aud) -> upsert Identity -> return token pair
```
**Google Sign-In** -- verify ID token server-side; check `aud` against all registered
client IDs (Android and iOS are separate).

```
POST /auth/google  { idToken }
  -> verify via Google certs (cache by max-age) -> check aud -> upsert Identity -> return token pair
```

Full flows and JVM library choices: [references/auth-identity.md](../../references/auth-identity.md)
(Social login verification section).
## Step 4: Session tokens

Issue a short-lived JWT access token + an opaque refresh token on every auth event.

- Access token: ES256 JWT, 15-min TTL, carries `sub` (account_id), `roles`, `jti`.
- Refresh token: 32 random bytes (base64url), stored server-side as a hash; 30-day TTL
  for games, 7-day for utility apps.

**Rotation:** every `/auth/refresh` call marks the old token used and issues a new one in
one DB transaction. On reuse detection (used token presented again), revoke the whole
family immediately.

**Revocation:** logout revokes the token family; force-logout deletes all families for
the account. Optionally check `jti` against a Redis revoked set for immediate
access-token invalidation on security events.

Full schema and rotation algorithm: [references/auth-identity.md](../../references/auth-identity.md)
(Token schema section).

## Step 5: Password handling (email auth only)

Skip if the product has no email/password login.

Use `de.mkammerer:argon2-jvm`, variant Argon2id, params m=65536 t=3 p=4.
Never use MD5, SHA-1, or unsalted hashes. Never roll a custom scheme.
Zeroize the password char array after hashing/verification.

Kotlin snippet: [references/auth-identity.md](../../references/auth-identity.md) (Password handling).

## Step 6: Authorization -- role/scope checks at the service boundary

Add a middleware/interceptor that verifies the JWT and checks claims before the request
reaches domain logic. Do not scatter `if (user.isAdmin)` checks inside domain code.
Keep roles coarse (`player`, `admin`); fine-grained resource checks query the DB after
token verification and do not go into the JWT.

Ktor example: [references/auth-identity.md](../../references/auth-identity.md) (Authorization).

## Step 7: Defer

- Injection, secrets, rate limiting, TLS, CORS, header hardening: **adlc-security**.
- Deploy, infra, observability: **adlc-ops**.
- IAP receipt validation + store notifications: **iap-server** (adlc-backend).

## Step 8: Verify (pass/fail)

```bash
# 1. Device account creation -> expect token pair
curl -s -X POST http://localhost:8080/auth/device -d '{"deviceId":"test-1"}' | jq .
# 2. Refresh -> expect new token pair
curl -s -X POST http://localhost:8080/auth/refresh -d '{"refreshToken":"<rt>"}' | jq .
# 3. Logout then same refresh -> expect 401
curl -s -X POST http://localhost:8080/auth/logout -H "Authorization: Bearer <at>"
curl -s -X POST http://localhost:8080/auth/refresh -d '{"refreshToken":"<rt>"}' | jq .status
# 4. No token on protected endpoint -> expect 401
curl -s http://localhost:8080/api/me | jq .status
# 5. Reuse already-rotated refresh token -> expect 401 (reuse detection)
```

All five must pass before marking auth done.
## Outbound checkpoint

Local work needs no approval. Outbound here (migration against a remote/production DB, deploying, third-party write API such as Apple token revocation at `https://appleid.apple.com/auth/revoke`, pushing a branch, opening a PR): stop, present exactly what would go out, and wait for the operator's explicit "yes" before it leaves the machine.

## References

- [references/auth-identity.md](../../references/auth-identity.md)
- App Store Guideline 4.8 -- https://developer.apple.com/app-store/review/guidelines/#login-services
- Sign in with Apple -- https://developer.apple.com/sign-in-with-apple/
- Google Sign-In server verify -- https://developers.google.com/identity/sign-in/android/backend-auth
- OWASP ASVS V2 Auth -- https://github.com/OWASP/ASVS/blob/master/4.0/en/0x11-V2-Authentication.md
- OWASP ASVS V3 Sessions -- https://github.com/OWASP/ASVS/blob/master/4.0/en/0x12-V3-Session-management.md
- JWT lifecycle -- https://skycloak.io/blog/jwt-token-lifecycle-management-expiration-refresh-revocation-strategies/
- argon2-jvm -- https://github.com/phxql/argon2-jvm
