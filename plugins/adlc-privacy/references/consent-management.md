<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
# Consent management: reference detail

Cite this file from `skills/consent-management/SKILL.md`. Do not nest references from here.

---

## iOS ATT: key rules

- Import `AppTrackingTransparency`; call `ATTrackingManager.requestTrackingAuthorization(completionHandler:)` **after** the first meaningful screen (not in `applicationDidFinishLaunching`).
- `NSUserTrackingUsageDescription` in `Info.plist`: name the specific partners ("Used to share with AdMob for ad measurement") -- vague strings cause rejection as of 2025 App Store policy.
- On denial: no IDFA, no probabilistic fingerprinting, no IP-based re-identification. Use `AdAttributionKit` (successor to SKAdNetwork since iOS 17.4 / enforced by iOS 26).
- Set `NSPrivacyTracking` + `NSPrivacyTrackingDomains` in `PrivacyInfo.xcprivacy` consistently with ATT usage.
- Do NOT request ATT if the app does no cross-app/cross-site tracking -- unnecessary prompts have caused rejections.

## Google UMP (Android + iOS)

- Use the [User Messaging Platform SDK](https://developers.google.com/admob/android/privacy). It satisfies the Google EU consent requirement and is a Google-certified CMP.
- Since Jan 16, 2024: EEA/UK traffic without a Google-certified CMP receives only **Limited Ads** (contextual). This is a revenue cliff.
- The UMP SDK loads and displays the IAB TCF 2.x consent form; check `UMPConsentInformation.sharedInstance.consentStatus` before loading any ad SDK.
- IAB TCF version: TCF 2.2 strings are deprecated after Feb 1, 2026. Upgrade to TCF 2.3-compatible CMP if using custom CMPs. UMP SDK handles this automatically when updated.
- Store TCF consent string under `IABTCF_PurposeConsents` in `SharedPreferences` (Android) / `NSUserDefaults` (iOS) per IAB spec -- ad SDKs read this key.
- Tag users under the age of consent with the `TFUA` signal; do not serve personalized ads.

## Consent storage schema (cross-platform)

Store per-session and per-user consent records:

| Key | Type | Example |
|---|---|---|
| `consent_version` | string | `"2026-01-01"` (date of the shown policy) |
| `consent_granted_at` | ISO-8601 | `"2026-01-15T10:22:00Z"` |
| `tcf_string` | string | raw IAB TCF consent string |
| `att_status` | enum | `authorized` / `denied` / `not_determined` / `restricted` |
| `analytics_consent` | bool | separate from ads for granularity |
| `ads_personalized` | bool | false when ATT denied or UMP rejected personalized |

When the user changes consent, write a new record; do not mutate the old one. Audit logs must be available for DSAR (confirm retention period with counsel).

## Dark-pattern prohibition (GDPR + FTC)

Illegal nudges (per EDPB Guidelines 3/2022 on deceptive design patterns):
- Pre-ticked opt-in boxes.
- "Accept" button visually dominant over "Reject" (size, color, contrast asymmetry).
- Hiding the "Reject all" option behind extra clicks while "Accept" is one click.
- Consent bundled with T&C acceptance.
- Repeated prompting after clear denial.

Legal + product note: dark patterns also reduce trust and inflate refund/churn rates. Privacy-positioned apps benefit from a genuinely neutral, symmetrical consent UX.

## COPPA (US, <13)

Final amended rule effective April 22, 2026:
- Verifiable parental consent required before collecting any personal data from users under 13.
- Push-notification opt-in for children requires direct notice + verified parental consent.
- "Directed to children" definition expanded: consider marketing materials, third-party representations, age of users on similar apps.
- For mixed-audience apps: age-gate before account creation; do not use year-of-birth alone (trivially bypassed).
- Confirm current compliance posture with US counsel; this is an engineering flag, not legal advice.

## CCPA/CPRA (California)

- "Do Not Sell or Share My Personal Information" link/flow required if the app shares data for cross-context behavioral advertising.
- Opt-out must be honored within 15 business days; downstream vendors must be notified (confirm SLAs with legal).
- Global Privacy Control (GPC) signal: honor if technically feasible on web surfaces.

## SDK gating pattern (Android example)

```kotlin
// Only initialize after consent is confirmed
val consentStatus = UMPConsentInformation.getInstance(context).consentStatus
if (consentStatus == ConsentStatus.OBTAINED) {
    MobileAds.initialize(context)
    // AttributionUA.start(context) -- gate attribution SDK similarly
} else {
    // Show UMP form; on completion, re-check and gate
}
```

iOS equivalent: check `UMPConsentInformation.sharedInstance.consentStatus == .obtained` before calling `GADMobileAds.sharedInstance().start`.

## References (official sources)

- Apple ATT: https://developer.apple.com/documentation/apptrackingtransparency
- Apple user privacy and data use: https://developer.apple.com/app-store/user-privacy-and-data-use/
- Google UMP Android: https://developers.google.com/admob/android/privacy
- Google UMP iOS: https://developers.google.com/admob/ios/privacy
- Google EU consent requirement: https://support.google.com/admob/answer/13554116
- IAB TCF: https://iabeurope.eu/transparency-consent-framework/
- EDPB dark patterns guidelines 3/2022: https://edpb.europa.eu/our-work-tools/documents/public-consultations/2022/guidelines-032022-dark-patterns-social-media_en
- FTC COPPA amended rule (Gibson Dunn): https://www.gibsondunn.com/ftc-updates-to-coppa-rule-impose-new-compliance-obligations-for-online-services-that-collect-data-from-children/
- AdAttributionKit: https://developer.apple.com/documentation/adattributionkit
