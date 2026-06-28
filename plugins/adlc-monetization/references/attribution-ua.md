<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
# Attribution UA -- technical reference

Companion to `skills/attribution-ua/SKILL.md`. Contains tables and SDK notes
that would push the skill body over 150 lines.

---

## iOS signal matrix

| Signal | Requires ATT opt-in? | Notes |
|---|---|---|
| IDFA | Yes | ~35% opt-in rate (Q2 2025, Adjust); useless at scale |
| SKAdNetwork 4 postback | No | Aggregated; signed by Apple; up to 3 postbacks; coarse/fine CV values |
| AdAttributionKit (AAK) | No | WWDC 2025: overlapping windows, geo in postbacks at high anonymity tier, configurable cooldowns; ships iOS 18.4 / iOS 26 |
| AdServices token | No | Apple Search Ads only; `AATokenRequest.generateToken()`, 24-hr TTL; relay to your server |
| Deterministic (email / SSO match) | Yes (counts as tracking) | Only lawful post-opt-in; do not use as fingerprinting workaround |
| Fingerprinting / probabilistic | **Banned** | App Store Review Guideline 5.1.2; reputable MMPs have dropped it |

## Android signal matrix

| Signal | Status | Notes |
|---|---|---|
| GAID (Google Advertising ID) | Active, no confirmed deprecation | User can reset or opt out; Limited Ad Tracking flag must be respected |
| Play Install Referrer | Active | `com.android.installreferrer:installreferrer:2.2`; returns referrer URL, click time, install time; data valid 90 days post-install; call once |
| Privacy Sandbox Attribution Reporting API | Deprecated Oct 2025 | Google killed the entire Privacy Sandbox initiative; do not build on it |

## SKAdNetwork 4 conversion value (CV) schema

Use a tiered CV schema so postbacks carry useful revenue signal:

- **Fine CV (0-63):** map to event milestones in the first post-install activity window (tutorial, first purchase, D0 LTV bucket).
- **Coarse CV (low/medium/high):** used for postbacks 2 and 3 (later funnel), maps to aggregated LTV tiers.
- Define the schema in your MMP dashboard; lock it before launch, changes break cohort continuity.

## MMP selection notes (2026)

Leading MMPs: AppsFlyer, Adjust, Singular, Branch. All support SKAN 4 + AAK postback handling, Play Install Referrer, and modeled attribution.

- **Modeled attribution:** MMPs blend deterministic data from opted-in users with aggregated SKAN/AAK postbacks and first-party analytics to produce probabilistic cohort estimates. No fingerprinting.
- **Incrementality testing:** the gold standard when postback volume is low; run geo holdouts or PSA tests to validate channel ROI.
- **Privacy manifest (iOS):** as of 2023, required-reason APIs must be declared in `PrivacyInfo.xcprivacy`; all MMP SDKs should ship their own manifest; validate the merged manifest before submission.

## Verified test install checklist

```
[ ] iOS: build to TestFlight with SKAN test mode enabled in MMP dashboard.
    MMP dashboard shows a test postback within the configured timer window.
[ ] iOS (Apple Search Ads): trigger via test campaign -> AdServices token fetched
    on first launch -> relayed to server -> MMP dashboard attributes to ASA.
[ ] Android: install via internal test track with a referrer URL set ->
    Play Install Referrer returns correct referrer string on first launch ->
    MMP dashboard shows attributed install.
[ ] Both: ATT-opted-out install: no IDFA sent, SKAN/Play Referrer path fires.
[ ] Both: organic install (no referrer): MMP marks as organic, not attributed.
```

## Official references

- SKAdNetwork (Apple Developer Documentation): https://developer.apple.com/documentation/storekit/skadnetwork
- AdAttributionKit (WWDC 2025 updates): https://www.singular.net/blog/wwdc-2025-aak/
- AdServices framework: https://developer.apple.com/documentation/adservices
- Apple App Tracking Transparency: https://developer.apple.com/documentation/apptrackingtransparency
- Play Install Referrer library: https://developer.android.com/google/play/installreferrer/library
- Google Privacy Sandbox deprecation (Oct 2025): https://privacysandbox.google.com/overview/android-progress-updates
- Apple App Store Review Guideline 5.1.2 (fingerprinting ban): https://developer.apple.com/app-store/review/guidelines/#data-collection-and-storage
