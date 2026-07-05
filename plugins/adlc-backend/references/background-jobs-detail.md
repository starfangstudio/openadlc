<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
Consumed by the `background-jobs` skill. Load on demand; do not load independently.

---

## Apple App Store Server Notifications V2: verification steps

Register an HTTPS endpoint in App Store Connect. On each POST:

1. Parse the JWT `signedPayload`; verify signature against Apple's embedded `x5c` cert chain
   (root pinned at build time; do not fetch the CA at runtime).
2. Validate claims: `iss`, `aud` (bundle ID), `exp`, `environment`.
3. Respond HTTP 200 within 5 seconds (verify first, then enqueue the work).
4. On verification failure, still respond 200 to suppress Apple's retry storm; log internally.
5. Enqueue with `idempotency_key = "apple-assn:{SHA-256 of signedPayload}"`.
6. In the handler, call the Apple App Store Server API to confirm entitlement state; update
   the user's entitlement table; route to receipt-validation logic (adlc-monetization).

Apple retries non-2xx at 1 h, 12 h, 24 h, 48 h, 72 h (5 retries total).

---

## Google Play Real-time Developer Notifications (RTDN): verification steps

Register a Cloud Pub/Sub push subscription pointing to your HTTPS endpoint.

1. Verify the Bearer JWT in the `Authorization` header against Google's OIDC public keys;
   `iss` must be `accounts.google.com`.
2. Base64-decode `message.data` to get the `DeveloperNotification` JSON.
3. Respond HTTP 200 within 10 seconds.
4. Enqueue with `idempotency_key = "google-rtdn:{message.messageId}"`.
5. In the job handler, call `purchases.subscriptionsv2.get` (or `purchases.products.get`) via
   the Google Play Developer API to fetch authoritative state; do not trust the RTDN payload
   alone. Update the user's entitlement table. Route to adlc-monetization for receipt logic.

Full message structure and notification type tables: see
[references/background-jobs.md](background-jobs.md) (Google RTDN section).
