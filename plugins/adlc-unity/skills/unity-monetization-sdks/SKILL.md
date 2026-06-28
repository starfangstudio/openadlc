---
name: unity-monetization-sdks
description: >-
  This skill should be used when the user asks to "wire up IAP", "add in-app purchases",
  "integrate Unity IAP", "set up receipt validation", "add ads to the game", "integrate
  LevelPlay", "add rewarded ads", "add interstitial ads", "set up ironSource mediation",
  "wire Unity Ads", "add Remote Config for live ops", "tune economy via remote config",
  "add analytics events", "track purchase events", "set up monetization SDKs", or
  "configure Unity Gaming Services monetization". Covers Unity IAP purchase flow with
  server-side receipt validation (never client-trusted), LevelPlay (ironSource) ad
  mediation for rewarded and interstitial placements, Remote Config for live-ops economy
  tuning, and UGS Analytics event instrumentation. Economy DESIGN (pricing, balance,
  progression) belongs in the coming adlc-monetization pack; this skill covers SDK wiring
  only. Privacy and store policy (ATT/consent on iOS, Play Families on Android) defers to
  ios-store-compliance and android-compliance packs.
version: 0.1.0
---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# unity-monetization-sdks

Wire the monetization SDK layer in Unity: IAP purchase flow + server-side receipt
validation, LevelPlay ad mediation (rewarded + interstitial), Remote Config for live-ops
tuning, and UGS Analytics events. Economy design defers to the adlc-monetization pack;
store policy defers to ios-store-compliance / android-compliance.

## Step 1: Detect existing SDK state

Never assume package versions or initialization patterns. Read first:

```bash
# Installed UGS packages and versions
cat Packages/manifest.json | grep -E 'purchasing|levelplay|remote-config|analytics|services.core'

# UGS initialization (look for UnityServices.InitializeAsync)
grep -rn "UnityServices.InitializeAsync\|IStoreListener\|IronSource\|RemoteConfigService\|AnalyticsService" \
  Assets/ --include="*.cs" | head -30

# Existing product catalog (if any)
find Assets/ -name "IAPProductCatalog.asset" 2>/dev/null

# Existing ad placements or LevelPlay app keys
grep -rn "IronSourceConstants\|SetAppKey\|appKey" Assets/ --include="*.cs" | head -10
```

Record: which packages are present, initialization entry point, whether `UnityServices`
is already bootstrapped, existing product IDs, and existing placement names. Mark anything
you cannot determine `unknown`; do not invent product IDs or app keys.

## Step 2: Bootstrap UGS core (once, before all services)

All UGS services share one init call; add it once, not per-service. On iOS, gate
analytics and ads data collection on the ATT prompt result.

For the bootstrap code sample, see [references/unity-monetization-sdks-detail.md](references/unity-monetization-sdks-detail.md).

## Step 3: Wire Unity IAP

Define the product catalog in code (preferred for determinism) matching the exact product
IDs registered on Play Console and App Store Connect. Server-side receipt validation is
required, not optional: return `PurchaseProcessingResult.Pending` in `ProcessPurchase`,
relay the raw receipt to your server, and call `ConfirmPendingPurchase` only after the
server confirms. Never embed store credentials (service account key, Apple private key)
in the Unity build.

For catalog setup code, receipt relay patterns (Google Play + Apple StoreKit 2), and
sandbox testing steps, see [references/unity-monetization-sdks-detail.md](references/unity-monetization-sdks-detail.md).

## Step 4: Wire LevelPlay ad mediation

LevelPlay (formerly ironSource) is the mediation layer. Configure everything through
LevelPlay; do not make direct Unity Ads SDK calls. Initialize once after UGS core init
using the per-platform app key from the LevelPlay dashboard. On iOS 14.4+, request ATT
permission before calling init and gate on the result.

Key rules:
- Rewarded: always check `isRewardedVideoAvailable()` before showing; grant reward only
  in the `onAdRewarded` callback, never on ad-close.
- Interstitial: enforce frequency caps on the dashboard, not in client code.

For init, rewarded, and interstitial code samples, see [references/unity-monetization-sdks-detail.md](references/unity-monetization-sdks-detail.md).

## Step 5: Wire Remote Config

Remote Config is the live-ops knob for economy values (prices, reward multipliers,
event schedules). Do not hardcode these in C#. Fetch on session start; use the cached
result. Never block gameplay on a fetch; the local default is the offline fallback.

For the fetch/read code sample and dashboard key setup, see [references/unity-monetization-sdks-detail.md](references/unity-monetization-sdks-detail.md).

## Step 6: Wire Analytics events

Instrument purchase and ad events after server validation confirms them. Keep event names
consistent with the UGS Dashboard schema defined there first. Do not call `Flush()` in
hot paths. On iOS, gate on ATT result; on Android Play Families (under-13), disable
behavioral targeting per android-compliance.

For event instrumentation code samples, see [references/unity-monetization-sdks-detail.md](references/unity-monetization-sdks-detail.md).

## Step 7: Verify (sandbox, pass/fail)

```
[ ] Sandbox IAP: initiate a consumable purchase -> ProcessPurchase fires ->
    server receipt validation returns OK -> reward granted -> ConfirmPendingPurchase called.
[ ] Rewarded ad: load -> isRewardedVideoAvailable() true -> show -> OnRewarded callback fires.
[ ] Interstitial: load -> isInterstitialReady() true -> show -> closes cleanly.
[ ] Remote Config: disconnect device -> launch -> game uses local defaults without crash.
[ ] Analytics: trigger purchase event -> Unity Dashboard Event Browser shows it within ~5 min.
```

Do not mark done without each box passing. "It compiled" is not verification.

## Outbound checkpoint

Local work needs no approval. Outbound here (pushing IAP product configuration to the Play Console or App Store Connect, deploying server-side receipt validation endpoints, publishing Remote Config changes to the UGS Dashboard live to players, or LevelPlay dashboard changes affecting live ad delivery): stop, present exactly what would go out, and ask the operator for an explicit "yes" first.

## References

- Unity IAP receipt validation: https://docs.unity.com/en-us/iap/receipt-validation
- Unity IAP manual (Unity 6): https://docs.unity3d.com/6000.2/Documentation/Manual/UnityIAPPurchaseReceipts.html
- LevelPlay SDK / Unity Ads mediation (Unity): https://docs.unity.com/en-us/grow/levelplay/sdk/unity/networks/guides/unity-ads
- LevelPlay mediation networks (Android): https://docs.unity.com/en-us/grow/levelplay/sdk/android/mediation-networks
- LevelPlay rewarded ads integration: https://developers.is.com/ironsource-mobile/unity/rewarded-video-integration-unity/
- Unity Remote Config get started: https://docs.unity.com/en-us/remote-config/get-started
- Unity Analytics events: https://docs.unity.com/ugs/manual/analytics/manual/events
- Unity Analytics custom event (SDK 5.1+): https://docs.unity.com/en-us/analytics/events/custom-event
- Full SDK code samples and receipt validation detail: [references/unity-monetization-sdks-detail.md](references/unity-monetization-sdks-detail.md)
