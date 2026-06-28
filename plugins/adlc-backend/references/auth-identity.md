<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
# auth-identity reference

Supporting detail for the `auth-identity` skill. Do not load unless the skill points here.

---

## Account model

### Guest/device account (F2P baseline)

```
Account
  id          UUID PK
  type        ENUM(device, user)
  device_id   TEXT UNIQUE NULLABLE   -- install-scoped, hashed on server
  linked_at   TIMESTAMPTZ NULLABLE   -- set when elevated to user account
  created_at  TIMESTAMPTZ
  updated_at  TIMESTAMPTZ

Identity                             -- one row per social/email link
  id          UUID PK
  account_id  UUID FK -> Account
  provider    ENUM(apple, google, email)
  provider_sub TEXT                  -- subject/sub from OIDC token or email addr
  email       TEXT NULLABLE          -- nullable; user may hide via Apple relay
  UNIQUE (provider, provider_sub)
```

Flow: device installs -> server creates `Account(type=device)`, returns JWT pair.
On social link: verify OIDC token, INSERT or UPDATE Identity, elevate `type` to `user`.
On conflict (identity already exists on another account): merge or surface choice to user.

### Utility app (no guest phase)

Skip the device account phase. Create an `Account(type=user)` on first social/email login.

---

## Token schema

### Access token (JWT, short-lived)

```
Header: { alg: "ES256" }            -- prefer ECDSA P-256 over RS256 (smaller)

Payload:
  sub   account_id
  type  "device" | "user"
  roles []string                     -- e.g. ["player"] or ["player","admin"]
  jti   UUIDv4                       -- for opt-in revocation checks
  iat   Unix timestamp
  exp   iat + 900 (15 min)
```

Sign with a key loaded from env/secrets manager at startup (never hardcoded).
Verify on every request at the service boundary. Reject if exp passed or jti revoked.

### Refresh token

- Opaque random bytes (32 bytes, base64url), stored server-side as a hash.
- Table: `refresh_tokens(id UUID, account_id UUID, token_hash TEXT, family TEXT, used BOOL, expires_at TIMESTAMPTZ)`
- Family: group all rotations from one auth session under one UUID; revoke the family on reuse detection.
- TTL: 30 days for games (idle player expectation); 7 days for utility apps. Adjust per product.

### Rotation + reuse detection

```
POST /auth/refresh
  1. Hash the incoming token.
  2. Look up by hash. Not found -> 401.
  3. If used=true -> revoke entire family -> 401 (replay detected).
  4. Mark old row used=true.
  5. INSERT new refresh_token (same family, used=false, new expiry).
  6. Issue new access token.
  All steps in one DB transaction.
```

### Revocation

Explicit logout: mark the token family as revoked.
Force-logout (security event): delete all families for the account.
Access tokens: validate `jti` against a Redis SET `revoked_jtis` (TTL = access token TTL).
Avoid the jti check on hot paths if performance matters; short access TTL (15 min) is usually sufficient.

---

## Social login verification

### Sign in with Apple

```
POST /auth/apple
  body: { identityToken: "<JWT from Apple SDK>" }

Server:
  1. Fetch Apple public keys: GET https://appleid.apple.com/auth/keys (cache, refresh on kid miss)
  2. Verify JWT signature, iss == "https://appleid.apple.com", aud == your bundle ID.
  3. Extract sub (stable user identifier), email (may be relay address or null).
  4. Upsert Identity(provider=apple, provider_sub=sub).
```

Libraries: `java-jwt` + manual JWK fetch, or `nimbus-jose-jwt` (JVM).

### Google Sign-In

```
POST /auth/google
  body: { idToken: "<JWT from Google SDK>" }

Server:
  1. Verify via Google tokeninfo endpoint OR local verification with Google certs.
     Prefer local: GET https://www.googleapis.com/oauth2/v3/certs (cache by max-age).
  2. Check aud == your client_id (Android + iOS client IDs).
  3. Extract sub, email.
  4. Upsert Identity(provider=google, provider_sub=sub).
```

Libraries: `google-auth-library-java` (handles key rotation + aud check).

---

## Password handling (email auth only)

Use argon2-jvm (`de.mkammerer:argon2-jvm`). Recommended params (OWASP 2025):
- Variant: Argon2id
- Memory: 64 MB (m=65536)
- Iterations: 3 (t=3)
- Parallelism: 4 (p=4)

Never store plaintext or MD5/SHA1/unsalted hashes. argon2-jvm encodes salt + params in the output string.

```kotlin
val argon2 = Argon2Factory.create(Argon2Factory.Argon2Types.ARGON2id)
val hash = argon2.hash(3, 65536, 4, password.toCharArray())
val valid = argon2.verify(hash, password.toCharArray())
```

Always zeroize the char array after use: `argon2.wipeArray(password.toCharArray())`.

---

## Authorization (role/scope checks)

Check roles/scopes at the service boundary, not inside domain logic.

```kotlin
// Ktor example: install at route level
install(Authentication) { jwt("bearer") { ... } }

fun Route.adminRoute(block: Route.() -> Unit) =
    authenticate("bearer") {
        intercept(ApplicationCallPipeline.Call) {
            val principal = call.principal<JWTPrincipal>()
            val roles = principal?.payload?.getClaim("roles")?.asList(String::class.java)
            if (roles?.contains("admin") != true) {
                call.respond(HttpStatusCode.Forbidden); finish()
            }
        }
        block()
    }
```

Keep roles coarse (player, admin). Fine-grained permissions live in the DB, looked up after token verification.

---

## Defer to adlc-security

The following are OUT OF SCOPE for this skill; adlc-security owns them:

- SQL injection / ORM parameterization
- Secret rotation and secrets-manager wiring
- Rate limiting and brute-force lockout
- TLS configuration
- CORS policy
- Header hardening (HSTS, X-Frame-Options, CSP)
