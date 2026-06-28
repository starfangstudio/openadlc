<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
Consumed by the `unity-monetization-sdks` skill. Load on demand; do not load independently.

## UGS Core Bootstrap

All UGS services (IAP, Remote Config, Analytics) share one init call. Add it once, not per-service:

```csharp
await UnityServices.InitializeAsync();
// On iOS: gate analytics/ads data collection on ATT prompt result.
```

Package: `com.unity.services.core` (pulled transitively by IAP and Analytics).

## Unity IAP: Catalog and Purchase Flow

Define the catalog in code (preferred for determinism) or via the IAP Catalog asset. Match product IDs to the exact strings registered on Play Console and App Store Connect:

```csharp
var builder = ConfigurationBuilder.Instance(StandardPurchasingModule.Instance());
builder.AddProduct("gems_500", ProductType.Consumable);
builder.AddProduct("starter_pack", ProductType.NonConsumable);
UnityPurchasing.Initialize(this, builder);  // 'this' implements IStoreListener
```

In `ProcessPurchase`: do NOT grant rewards before validation. Return `PurchaseProcessingResult.Pending`; grant and call `ConfirmPendingPurchase` only after your server confirms the receipt.

## Unity IAP: Server-Side Receipt Validation

Client-side trust is exploitable. Relay the raw receipt to your server:

- **Google Play:** send `receipt.Payload` (JSON with `Payload` + `signature`) to your backend; verify against Google Play Developer API (`purchases.products.get` or `purchases.subscriptions.get`).
- **Apple:** use `OrderInfo.Apple.jwsRepresentation` (StoreKit 2) for your server to verify against Apple's App Store Server API. The old `transactionReceipt` endpoint is deprecated by Apple; do not use it for new builds.

Server holds the store credentials (service account key for Google, private key + issuer for Apple). Never embed these credentials in the Unity build.

**Sandbox testing.** Test on a real device with a sandbox Apple ID or a Google Play internal test track account. Confirm `ProcessPurchase` fires and your server returns a valid response before marking done.

Package: `com.unity.purchasing` (4.x+).

## LevelPlay Ad Mediation: Initialization

Initialize once, after UGS core init:

```csharp
IronSource.Agent.init(appKey);           // appKey from LevelPlay dashboard per platform
IronSource.Agent.validateIntegration();  // logs any adapter mismatches; remove before ship
```

## LevelPlay: Rewarded Ad Flow

```csharp
// Load
IronSource.Agent.loadRewardedVideo();

// Check before showing (never show without checking)
if (IronSource.Agent.isRewardedVideoAvailable())
    IronSource.Agent.showRewardedVideo(placementName);

// Grant reward only in the callback, never on ad-close
IronSourceRewardedVideoEvents.onAdRewardedEvent += OnRewarded;
```

## LevelPlay: Interstitial Ad Flow

```csharp
IronSource.Agent.loadInterstitial();

if (IronSource.Agent.isInterstitialReady())
    IronSource.Agent.showInterstitial(placementName);
```

Enforce interstitial frequency caps on the LevelPlay dashboard, not in client code, so they tune without a release.

**ATT (iOS).** On iOS 14.4+, request ATT permission before calling `IronSource.Agent.init`. Gate the init on the ATT result. Policy specifics defer to ios-store-compliance.

Package: `com.unity.services.levelplay` (8.x+).

## Remote Config: Fetch and Use

```csharp
await RemoteConfigService.Instance.FetchConfigsAsync(userAttributes, appAttributes);
var gemPrice = RemoteConfigService.Instance.appConfig.GetInt("gems_500_price", 499);
```

Define keys and defaults on the UGS Dashboard. The local default (`499` above) is the safe fallback when the fetch fails or the device is offline. Never block gameplay on a Remote Config fetch; fetch on session start, then use the cached result.

Package: `com.unity.remote-config` (pulled via UGS).

## Analytics: Event Instrumentation

Instrument the key purchase and ad events; keep event names consistent with the UGS Dashboard schema:

```csharp
// Purchase completed (after server receipt validation confirms it)
AnalyticsService.Instance.RecordEvent(new CustomEvent("iap_purchase_completed")
    { {"product_id", productId}, {"price_usd_cents", priceUsdCents} });

// Rewarded ad completed
AnalyticsService.Instance.RecordEvent(new CustomEvent("rewarded_ad_completed")
    { {"placement", placementName}, {"reward_type", rewardType} });
```

The SDK batches and uploads every 60 seconds. Do not call `AnalyticsService.Instance.Flush()` in hot paths; it blocks the upload queue.

**Privacy.** Analytics sends data to Unity's servers. On iOS, gate data collection on ATT result. On Android (Play Families), if the game targets under-13 content, disable behavioral ad targeting and analytics per Play policy; defer the exact policy steps to android-compliance.
