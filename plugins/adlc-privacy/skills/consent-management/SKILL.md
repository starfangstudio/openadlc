---
name: consent-management
description: >-
  Implements and audits user consent flows: iOS ATT, Google UMP for EEA/UK ads,
  web cookie banners, neutral UX (no dark patterns), versioned consent storage,
  and SDK gating so ads/analytics/attribution stay off until consent is granted.
  Use this skill when the user asks to "add a consent flow", "set up ATT prompt",
  "integrate Google UMP", "gate ads on consent", or "block SDKs until consent".
version: 0.1.0
---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# Consent management

Consent is not a banner. It is a contract: the user decides which data uses they
allow, the app stores that decision with its version, and every SDK that touches
personal data stays dark until consent is confirmed. A miss anywhere in this
chain is a GDPR/CCPA violation and a likely App Store / Play rejection.

Engineering guidance only. Flag legal calls with "confirm with counsel for
jurisdiction X." Mark anything you cannot determine from source as `unknown`;
never invent a consent answer.

## Detect first

```bash
# ATT call site + usage description (iOS)
grep -rn "requestTrackingAuthorization\|advertisingIdentifier" --include="*.swift" . | head -20
grep -n "NSUserTrackingUsageDescription" */Info.plist */*.plist 2>/dev/null

# UMP SDK present + any SDK initialized before consent check (Android/iOS)
grep -rn "user-messaging-platform\|ConsentInformation\|MobileAds.initialize\
\|FirebaseApp.configure\|AppsFlyer\|Adjust\|AppLovin\|Amplitude" \
  --include="*.gradle" --include="*.kts" --include="*.kt" --include="*.swift" . | head -30

# Consent state storage
grep -rn "IABTCF_PurposeConsents\|consent_version\|att_status" \
  --include="*.swift" --include="*.kt" . | head -20
```

Mark every SDK init that precedes a consent check as a finding.

## Gate 1: iOS App Tracking Transparency (ATT)

Required before accessing IDFA or any cross-app tracking (iOS 14.5+).

- Call `ATTrackingManager.requestTrackingAuthorization(completionHandler:)` after
  the first meaningful screen, not at cold-start.
- `NSUserTrackingUsageDescription` in `Info.plist`: name specific partners
  ("Used to share with AdMob for ad measurement"). Vague strings cause rejection.
- On denial: no IDFA, no fingerprinting, no IP-based re-ID. Use `AdAttributionKit`
  (successor to SKAdNetwork; confirm iOS 26 behavior with Apple docs).
- Align `NSPrivacyTracking` + `NSPrivacyTrackingDomains` in `PrivacyInfo.xcprivacy`
  with ATT usage (see ios-store-compliance for manifest detail).
- Do NOT request ATT if the app does no cross-app/cross-site tracking.

Store `att_status` in the consent record immediately after the callback.

## Gate 2: Google UMP for EEA/UK ads

Since Jan 16, 2024: EEA/UK traffic without a Google-certified CMP gets only
Limited Ads (contextual). Revenue cliff; fix before shipping ads.

- Integrate UMP SDK on cold start: call `ConsentInformation.requestConsentInfoUpdate`
  then `ConsentForm.loadAndPresentIfRequired` before any `MobileAds.initialize`.
- Gate `MobileAds.initialize` on `consentStatus == OBTAINED`.
- UMP writes `IABTCF_PurposeConsents` to `SharedPreferences` / `NSUserDefaults`
  automatically; do not overwrite it manually.
- Custom CMP: migrate to IAB TCF 2.3 before Feb 1, 2026 (TCF 2.2 deprecated).
- Tag under-age-of-consent users with the TFUA signal; no personalized ads.

## Gate 3: web / WebView consent

Show a cookie consent banner before any non-essential cookie or tracker script.
Pass the IAB TCF string into WebView via `evaluateJavaScript` /
`addJavascriptInterface`. Honor Global Privacy Control (GPC) for California users
where feasible (confirm CCPA scope with counsel).

## Gate 4: neutral consent UX

EDPB Guidelines 3/2022 voids consent obtained via dark patterns. Illegal nudges
are listed in [references/consent-management.md](references/consent-management.md). Hard rule:
Accept and Reject must be identical in visual weight (size, color, tap distance).
A privacy-positioned app gains trust from a genuinely neutral dialog.

## Gate 5: consent storage and versioning

Append-only records. Required fields: `consent_version` (policy date), 
`consent_granted_at` (ISO-8601), `tcf_string`, `att_status`,
`analytics_consent` (bool), `ads_personalized` (bool).
Full schema in [references/consent-management.md](references/consent-management.md).

Bump `consent_version` on any policy or scope change; re-prompt on next launch.
Keep records available for DSAR; confirm retention period with counsel.

## Gate 6: COPPA (US, users under 13)

Amended rule effective April 22, 2026: verifiable parental consent before
collecting any data from under-13 users; push-notification opt-in for children
requires direct notice + parental consent. Age-gate before account creation;
do not rely on year-of-birth alone. Confirm with US counsel; COPPA carries civil
penalties. Also check GDPR Art. 8 if the app is marketed to children in the EU
(age of digital consent varies 13-16 by member state -- confirm with counsel).
Detail in [references/consent-management.md](references/consent-management.md).

## Verify: SDK gating

```
[ ] Ad SDK initialized ONLY after consentStatus == OBTAINED
[ ] Analytics SDK gated on analytics_consent == true
[ ] Attribution SDK gated on ads_personalized == true
[ ] ATT prompt fires before any IDFA access; att_status stored
[ ] UMP form shown before any ad request on EEA/UK cold start
[ ] Consent record written atomically; version matches shown policy
[ ] Accept and Reject identical in visual weight
[ ] COPPA gate active for any under-13 user path
```

Mark each PASS / FAIL / UNKNOWN. Do not ship with any FAIL; resolve or escalate.

## Outbound: get the operator's yes first

Local work is fine to do without asking. Outbound here (submitting a privacy declaration to Play Data safety / App Store App Privacy / cookie consent registration, publishing a privacy policy, responding to a DSAR, enabling an SDK that sends personal data to a third party, pushing to production): stop, present exactly what would go out, and get the operator's explicit "yes" first.

## References

- [references/consent-management.md](references/consent-management.md) -- storage schema,
  dark-pattern list, COPPA/CCPA detail, SDK gating code examples, TCF 2.3 note.
- Apple ATT: https://developer.apple.com/documentation/apptrackingtransparency
- Apple user privacy and data use: https://developer.apple.com/app-store/user-privacy-and-data-use/
- Google UMP Android: https://developers.google.com/admob/android/privacy
- Google UMP iOS: https://developers.google.com/admob/ios/privacy
- Google EU consent requirement: https://support.google.com/admob/answer/13554116
- EDPB dark patterns guidelines 3/2022: https://edpb.europa.eu/our-work-tools/documents/public-consultations/2022/guidelines-032022-dark-patterns-social-media_en
- IAB TCF: https://iabeurope.eu/transparency-consent-framework/
- FTC COPPA amended rule: https://www.gibsondunn.com/ftc-updates-to-coppa-rule-impose-new-compliance-obligations-for-online-services-that-collect-data-from-children/
