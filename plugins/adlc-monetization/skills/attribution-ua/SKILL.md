---
name: attribution-ua
description: >-
  This skill should be used when the user asks to "set up install attribution", "wire an
  MMP", "add AppsFlyer", "add Adjust", "measure UA", "track installs", "set up SKAdNetwork",
  "configure AdAttributionKit", "set up SKAN postbacks", "wire Play Install Referrer",
  "set up Apple Search Ads attribution", "set up AdServices", "measure campaign ROI",
  "how do I attribute installs after ATT", "IDFA is gone how do I measure", or
  "set up privacy-safe attribution". Covers the post-ATT/post-IDFA measurement stack:
  iOS SKAdNetwork 4 + AdAttributionKit postbacks, AdServices (Apple Search Ads), Android
  Play Install Referrer, modeled/aggregated attribution, and the death of fingerprinting.
  Consent and GDPR prompt UX defer to adlc-privacy. Store policy defers to
  ios-store-compliance / android-compliance.
version: 0.1.0
---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# attribution-ua

Measure install attribution and UA in the privacy-first era (post-ATT, post-IDFA).
The core constraint: on iOS you cannot fingerprint and IDFA opt-in averages ~35%.
On Android, Play Install Referrer remains the primary deterministic signal; Google's
Privacy Sandbox was killed in October 2025. Build on what Apple and Google actually
support.

## Detect first

Inspect what is already wired before touching anything:

```bash
# iOS: check for existing MMP pods / SPM packages
grep -rEn "AppsFlyerLib|Adjust|Singular|Branch|AdServices|SKAdNetwork" \
  ios/ --include="*.swift" --include="*.m" --include="*.plist" | head -30

# iOS: SKAdNetwork IDs declared in Info.plist?
grep -A2 "SKAdNetworkItems" ios/*/Info.plist 2>/dev/null | head -20

# iOS: Privacy manifest present?
find ios/ -name "PrivacyInfo.xcprivacy" 2>/dev/null

# Android: MMP dependency + Install Referrer
grep -rEn "appsflyer|adjust|installreferrer|singular|branch" \
  android/ --include="*.gradle" --include="*.kts" --include="*.toml" | head -20
```

Record: which MMP (if any), whether SKAN IDs are declared, whether a
`PrivacyInfo.xcprivacy` manifest exists, and whether Play Install Referrer
is in the Gradle dependency graph. Mark anything you cannot confirm `unknown`.

## iOS attribution stack

**What is alive:**

- **SKAdNetwork 4 / AdAttributionKit (AAK):** no ATT required; Apple signs
  aggregated postbacks directly to ad networks (and optionally to your MMP).
  SKAN 4 delivers up to 3 postbacks with coarse + fine conversion values.
  AAK (iOS 18.4 / iOS 26+) adds overlapping windows, configurable cooldowns,
  and country codes in high-anonymity-tier postbacks.
- **AdServices (Apple Search Ads only):** call `AATokenRequest.generateToken()`
  on first launch, relay the token (valid 24 hrs) to your server, which POSTs
  it to `https://api-adservices.apple.com/api/v1/` to get ASA attribution data.
  No ATT required; no third-party tracking.
- **IDFA (post-ATT):** only available after user opt-in. Use it where available,
  never as the sole signal. Do NOT use it as a fingerprinting fallback.

**What is banned:** Fingerprinting (IP + user-agent + device signal combos) is
banned under App Store Review Guideline 5.1.2; reputable MMPs have dropped it.
Do not wire any SDK that relies on it.

**Wiring:**

1. Declare every ad network's `SKAdNetworkIdentifier` in `Info.plist` under
   `SKAdNetworkItems`. Get the list from your MMP's published network list.
2. Add a `PrivacyInfo.xcprivacy` privacy manifest (required since 2023). Validate
   the merged manifest covers all SDK-declared required-reason APIs.
3. Initialise your MMP SDK before any ad network SDK call. Pass the ATT
   authorisation status into the MMP init so it gates data collection correctly.
   Defer the ATT prompt UX itself to adlc-privacy.
4. Register an SKAN conversion value schema in your MMP dashboard before launch;
   changing it post-launch breaks cohort continuity.

## Android attribution stack

**What is alive:**

- **Play Install Referrer** (`com.android.installreferrer:installreferrer:2.2`):
  returns a signed `installReferrer` string, click timestamp, and install
  timestamp. Call once on first launch; data is valid for 90 days.
- **GAID (Google Advertising ID):** still active; respect the Limited Ad Tracking
  flag. No confirmed deprecation date, but do not build a model that fails if it
  disappears.

Google's Privacy Sandbox for Android (Attribution Reporting API) was deprecated
in October 2025. Do not build on it.

**Wiring:**

1. Add the Install Referrer dependency and read `installReferrer` on first launch
   inside an `InstallReferrerStateListener.onInstallReferrerSetupFinished` callback.
2. Relay the referrer string to your backend (or MMP SDK) immediately; call
   `endConnection()` after to prevent leaks.
3. Pass GAID (retrieved via `AdvertisingIdClient.getAdvertisingIdInfo`) into the
   MMP SDK; the SDK handles the Limited Ad Tracking check.

## MMP selection and modeled attribution

Pick one MMP (AppsFlyer, Adjust, Singular, or Branch); all support SKAN 4 + AAK,
Play Install Referrer, and modeled attribution. Do not run two competing MMPs.
Modeled attribution blends ATT-consented deterministic data, SKAN/AAK postbacks,
and first-party analytics. For channels with low postback volume, use incrementality
testing (geo holdouts / PSA tests) rather than probabilistic guessing.

## Verify: attributed test install

Run this checklist before calling attribution "live":

```
[ ] iOS SKAN: build to TestFlight with SKAN test mode on in MMP dashboard ->
    MMP shows a signed test postback within the configured timer window.
[ ] iOS AdServices: trigger via ASA test campaign -> AdServices token fetched
    on first launch -> relayed to server -> MMP attributes install to ASA.
[ ] Android: install via internal test track with a referrer URL set ->
    Play Install Referrer returns the correct string on first launch ->
    MMP dashboard shows attributed install.
[ ] ATT opt-out path (iOS): install without opting in -> no IDFA sent ->
    SKAN path fires -> MMP shows organic or SKAN-attributed, not "no data".
[ ] Organic install: no referrer -> MMP marks organic, not a conversion error.
```

"It compiled" is not verification. Each box must pass before marking done.

## Outbound checkpoint

Local work is free. Outbound here (enabling a live MMP SDK key that sends install and event data to third-party MMP servers and ad networks, pushing SKAN network lists, or configuring any MMP dashboard endpoint that routes data off-device): stop, present exactly what would go out, and get the operator's explicit "yes" first (global consent law).

## References

- [references/attribution-ua.md](../../references/attribution-ua.md) -- iOS/Android signal matrices,
  SKAN CV schema, MMP notes, full verified-install checklist, official doc URLs.
- SKAdNetwork: https://developer.apple.com/documentation/storekit/skadnetwork
- AdAttributionKit (WWDC 2025): https://www.singular.net/blog/wwdc-2025-aak/
- AdServices framework: https://developer.apple.com/documentation/adservices
- App Tracking Transparency: https://developer.apple.com/documentation/apptrackingtransparency
- Play Install Referrer: https://developer.android.com/google/play/installreferrer/library
- App Store Review Guideline 5.1.2 (fingerprinting ban): https://developer.apple.com/app-store/review/guidelines/#data-collection-and-storage
