<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
# Receipt / transaction validation: StoreKit 2 + Play Billing

Server-side reference for the `iap-integration` skill. Read this when
implementing or reviewing the backend validation leg of a purchase flow.

---

## Rule zero

Never grant entitlement on the client. The purchase token / transaction ID
arrives on the client; the *server* is the only authority that may call Apple
or Google to confirm the purchase is real and unspent, then write the
entitlement to your own database.

---

## StoreKit 2 (iOS / macOS)

### What the client sends to your server

`Transaction.jwsRepresentation`: a JWS-encoded, Apple-signed string the app
receives from `Transaction.updates` or `Transaction.currentEntitlements`.
Also send the `transactionId` for App Store Server API calls.

### Option A: verify JWS in-process (App Store Server Libraries)

Apple provides server libraries (Swift, Node.js, Python, Java) with a
`SignedDataVerifier` class. It decodes and cryptographically verifies the JWS
against Apple's certificate chain without an extra API round-trip. Fastest path;
requires the library in your backend stack.

```
// Node.js (apple-app-store-server-library)
const verifier = new SignedDataVerifier(
  [rootCert],               // Apple root CA bundle (ship with the library)
  environment,              // Environment.PRODUCTION or SANDBOX
  bundleId,
);
const transaction = await verifier.verifyAndDecodeTransaction(jwsRepresentation);
// transaction.transactionId, .productId, .purchaseDate, .type, ...
```

### Option B: App Store Server API (look up by transactionId)

Use when you have a `transactionId` but not the full JWS, or for subscription
status polling.

**Base URL (production):** `https://api.storekit.itunes.apple.com`
**Sandbox URL:** `https://api.storekit-sandbox.itunes.apple.com`

**Auth:** JWT Bearer token, signed with your App Store Connect API private key
(.p8 file). Claims: `iss` = Issuer ID, `aud` = `appstoreconnect-v1`,
`exp` = now + 300s. Algorithm: ES256.

| Endpoint | Purpose |
|---|---|
| `GET /inApps/v1/transactions/{transactionId}` | Verify a single transaction; returns a signed JWS `signedTransactionInfo` |
| `GET /inApps/v1/subscriptions/{originalTransactionId}` | Current subscription status across all groups |
| `GET /inApps/v1/history/{originalTransactionId}` | Full purchase history for a customer |

### Subscription status field to check

`data[].lastTransactions[].status`:
- `1` = Active
- `2` = Expired
- `3` = In Billing Retry
- `4` = In Grace Period
- `5` = Revoked

Grant access only on `1` (and optionally `4` during grace).

### Server Notifications v2 (push, recommended)

Register a URL in App Store Connect (App > General > App Information > App Store
Server Notifications). Apple POSTs a signed `JWSNotificationPayload` for every
subscription lifecycle event (renewal, expiry, refund, revocation) so your
server stays current without polling. Verify each incoming payload with
`SignedDataVerifier` before trusting it.

---

## Google Play Billing (Android)

### What the client sends to your server

`Purchase.purchaseToken`: an opaque string returned after a successful billing
flow or from `queryPurchasesAsync()`. Also send the `productId` (and whether it
is a subscription).

### Backend call: Google Play Developer API

Auth: OAuth 2 service account with the `androidpublisher` scope. The service
account JSON key lives on the server only; never embed it in the APK.

| Endpoint | Use |
|---|---|
| `GET purchases.products.get` | One-time product (consumable / non-consumable) |
| `GET purchases.subscriptionsv2.get` | Subscription (v2 endpoint, supports prepaid) |

**One-time product:**
```
GET https://androidpublisher.googleapis.com/androidpublisher/v3/
    applications/{packageName}/purchases/products/{productId}/tokens/{token}
```
Check: `purchaseState == 0` (purchased, not pending), `consumptionState` for
consumables. Acknowledge with `POST .../token:acknowledge` within 3 days or
Google auto-refunds.

**Subscription (v2):**
```
GET https://androidpublisher.googleapis.com/androidpublisher/v3/
    applications/{packageName}/purchases/subscriptionsv2/tokens/{token}
```
Check: `subscriptionState == SUBSCRIPTION_STATE_ACTIVE` (or `IN_GRACE_PERIOD`).
The `lineItems[].expiryTime` field tells you when the period ends.

### Real-time Developer Notifications (RTDN)

Configure a Pub/Sub topic in Play Console (Monetization > Subscriptions). Google
pushes a base64-encoded `DeveloperNotification` message for every subscription
event (renewed, cancelled, expired, revoked, paused). Verify the Pub/Sub push
subscription signature before processing. This replaces polling for subscriptions
and catches refunds and revocations promptly.

### Acknowledge window

Google requires acknowledgement within **3 days** of purchase or it refunds the
transaction automatically. For consumables: `consumePurchase` acknowledges
implicitly. For non-consumables and subscriptions: `acknowledgePurchase`
explicitly. Never acknowledge before server validation succeeds.

---

## Shared anti-patterns

| Anti-pattern | Fix |
|---|---|
| Client calls Apple/Google and self-reports "purchase valid" | Always relay token to YOUR server; server calls Apple/Google |
| Storing Apple private key (.p8) or Google service account JSON in the app bundle | Keep on server only; rotate if exposed |
| Acknowledge before validation returns | Validate first, grant entitlement, then acknowledge |
| Trusting only `purchaseState == PURCHASED` without server call | Replay attacks reuse tokens; server confirms each token once |
| Polling Apple/Google for subscription status instead of using push | RTDN / Server Notifications v2 for real-time accuracy |

---

## References

- App Store Server API (Apple): https://developer.apple.com/documentation/appstoreserverapi
- App Store Server Libraries (Apple): https://developer.apple.com/documentation/appstoreserverapi/implementing-a-branding-kit-verification-service
- App Store Server Notifications v2: https://developer.apple.com/documentation/appstoreservernotifications
- apple-app-store-server-library (Node/Swift/Python/Java): https://github.com/apple/app-store-server-library-node
- Google Play Developer API - purchases.products.get: https://developers.google.com/android-publisher/api-ref/rest/v3/purchases.products/get
- Google Play Developer API - purchases.subscriptionsv2.get: https://developers.google.com/android-publisher/api-ref/rest/v3/purchases.subscriptionsv2/get
- Real-time Developer Notifications (Google Play): https://developer.android.com/google/play/billing/getting-ready#configure-rtdn
- Play Billing Library integrate (current): https://developer.android.com/google/play/billing/integrate
