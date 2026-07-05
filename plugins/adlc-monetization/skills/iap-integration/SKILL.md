---
name: iap-integration
description: >-
  This skill should be used when the user asks to "add in-app purchases", "wire
  up StoreKit 2", "integrate Play Billing", "set up consumables/subscriptions",
  "implement purchase restore", "add non-consumable IAP", "handle pending
  transactions", "validate receipts on the server", "set up server-side receipt
  validation", "implement purchase verification", "test sandbox purchases", or
  "never trust the client for purchases". Covers native iOS (StoreKit 2) and
  Android (Play Billing 8+) purchase flows: product fetch, purchase initiation,
  restore, consumables vs non-consumables vs subscriptions, and the
  non-negotiable rule that entitlement is granted by YOUR server after verifying
  with Apple/Google. Unity SDK wiring defers to adlc-unity
  (unity-monetization-sdks). Store/gacha/ads policy defers to the compliance
  packs.
version: 0.1.0
---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# iap-integration

Native IAP for iOS (StoreKit 2) and Android (Play Billing 8+). The single
inviolable rule: **the client initiates and reports; the server verifies and
grants.** Never trust a client-side purchase result.

## Detect first

```bash
# iOS: StoreKit version in use
grep -rn "SKPaymentQueue\|Transaction.updates\|Product.products" \
  . --include="*.swift" | head -20
# Android: Billing Library version and client setup
grep -rn "billing" . --include="*.toml" --include="*.gradle*" | grep -v "^Binary"
grep -rn "BillingClient\|onPurchasesUpdated" . --include="*.kt" | head -20
```

Record: existing purchase manager, product IDs, billing library version, server
validation endpoint. Mark unknowns as `unknown`.

## Product types

Consumables (gems, energy): spent and re-purchasable; must be consumed after
server validation. Non-consumables (permanent unlocks): one purchase, must
survive reinstall via restore. Subscriptions: auto-renewing; server tracks
expiry via push notifications, never polling.

## iOS: StoreKit 2 (iOS 15+)

Do not use `SKPaymentQueue` for new builds.

```swift
// Fetch
let products = try await Product.products(for: productIDs)

// Purchase
let result = try await product.purchase()
if case .success(let verification) = result,
   case .verified(let tx) = verification {
    await sendToServer(tx.jwsRepresentation)  // server verifies; grants entitlement
    await tx.finish()                         // only after server OK
} else if case .pending = result {
    // show pending UI; never grant; Transaction.updates fires when resolved
}

// Restore (non-consumables + subscriptions)
for await result in Transaction.currentEntitlements {
    guard case .verified(let tx) = result else { continue }
    await sendToServer(tx.jwsRepresentation)
}
```

Start a `Transaction.updates` listener at app launch to catch deferred
purchases and subscription renewals.

## Android: Play Billing 8+

Play Billing 8+ required for new submissions as of August 2026; v9 is current.
Connect via `BillingClient`, query `QueryProductDetailsParams`, launch
`BillingFlowParams`. Handle results:

```kotlin
override fun onPurchasesUpdated(result: BillingResult, purchases: List<Purchase>?) {
    if (result.responseCode == BillingResponseCode.OK && purchases != null) {
        for (purchase in purchases) {
            if (purchase.purchaseState == Purchase.PurchaseState.PURCHASED) {
                // validate server-side first; Google auto-refunds purchases
                // that are not acknowledged within 3 days
                sendToServer(purchase.purchaseToken, purchase.products)
            }
        }
    }
}
```

After your server validates the token, call `BillingClient.acknowledgePurchase` (or `consumeAsync` for consumables); never acknowledge before validation.

On launch: call `queryPurchasesAsync` for both `INAPP` and `SUBS` and process
each purchase through `sendToServer`. Set `setObfuscatedAccountId(hashedUserId)`
on `BillingFlowParams` as a fraud signal.

## Server-side validation

Full flows in [references/receipt-validation.md](../../references/receipt-validation.md). Summary:

- **iOS:** client sends `tx.jwsRepresentation`. Server verifies via Apple's
  App Store Server Libraries (in-process JWS) or `GET
  /inApps/v1/transactions/{transactionId}` (JWT Bearer auth). Grant only after
  `200 OK`.
- **Android:** client sends `purchase.purchaseToken`. Server calls
  `purchases.products.get` (one-time) or `purchases.subscriptionsv2.get`
  (subscription) via the Play Developer API (service-account OAuth 2). Grant
  after `purchaseState == 0` / `SUBSCRIPTION_STATE_ACTIVE`.
- Apple `.p8` key and Google service account JSON live on the server only.
  Never embed either in the binary.
- Subscriptions: register Apple Server Notifications v2 and Google RTDN
  (Pub/Sub) for renewals, cancellations, and revocations without polling.

## Verify (pass/fail)

```
[ ] Sandbox consumable: purchase -> server validates -> reward granted
    -> transaction finished/consumed.
[ ] Sandbox non-consumable: purchase -> server validates -> restore on
    fresh install recovers entitlement.
[ ] Sandbox subscription: purchase -> server validates -> push notification
    (RTDN / Server Notifications v2) received and processed.
[ ] Pending/deferred: .pending or PENDING -> NO entitlement granted ->
    async listener fires later, grants after server OK.
[ ] Network failure: entitlement NOT granted; retried on next launch.
[ ] Receipt replay: resubmitting a consumed token -> server rejects.
```

## Outbound checkpoint

Local work is free. Outbound here (publishing products or prices to App Store Connect or Play Console, deploying the server validation endpoint, or pushing server config like API keys and product IDs to any remote environment): stop, present exactly what would go out, and get the operator's explicit "yes" first (global consent law).

## References

- [references/receipt-validation.md](../../references/receipt-validation.md) (full server flows:
  StoreKit 2 JWS + App Store Server API; Play Developer API + RTDN; anti-patterns)
- StoreKit 2: https://developer.apple.com/documentation/storekit/in-app-purchase
- App Store Server API: https://developer.apple.com/documentation/appstoreserverapi
- App Store Server Notifications v2: https://developer.apple.com/documentation/appstoreservernotifications
- Play Billing Library: https://developer.android.com/google/play/billing/integrate
- Play Billing release notes: https://developer.android.com/google/play/billing/release-notes
- Google Play Developer API: https://developers.google.com/android-publisher/api-ref/rest
- Real-time Developer Notifications: https://developer.android.com/google/play/billing/getting-ready#configure-rtdn
