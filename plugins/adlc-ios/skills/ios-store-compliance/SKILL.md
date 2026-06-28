---
name: ios-store-compliance
description: >-
  This skill should be used when the user asks to "get the app ready for App Store",
  "submit to App Store Connect", "prepare the iOS app for review", "fill out App
  Privacy details", "add a Privacy Manifest", "declare required-reason APIs",
  "fix PrivacyInfo.xcprivacy", "set up ATT prompt", "add App Tracking Transparency",
  "fix privacy nutrition labels", "check entitlements before submission",
  "configure export compliance", "upload to TestFlight", "prep a beta build",
  "we got an App Store rejection", or "audit third-party SDK privacy manifests".
  Covers Privacy Manifest (PrivacyInfo.xcprivacy + required-reason API declarations),
  third-party SDK manifests, App Privacy nutrition labels in App Store Connect, ATT
  prompt, entitlements audit, encryption/export compliance, TestFlight beta, and
  App Store Review Guideline hot spots. Produces a pass/fail readiness checklist
  with exact files and fields to fix.
version: 0.1.0
---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# iOS App Store compliance

Four gates: correct **Privacy Manifest**, accurate **App Privacy nutrition labels**, valid
**ATT prompt** before any cross-app tracking, and clean **entitlements + metadata**. A
miss on any one blocks or rejects submission.

## Detect first

Never assume. Run these commands from the repo root before proposing any change. Mark
anything you cannot determine `unknown`; never invent a privacy answer to clear a form.

```bash
# Privacy Manifest present?
find . -name "PrivacyInfo.xcprivacy" -not -path "*/DerivedData/*"

# Entitlements in use
find . -name "*.entitlements" -not -path "*/DerivedData/*"

# Info.plist keys that affect review
/usr/libexec/PlistBuddy -c "Print" <path>/Info.plist 2>/dev/null | \
  grep -E "NSUsage|ITSApp|UIBackgroundModes|NSPrivacy"

# ATT call sites
grep -rn "requestTrackingAuthorization\|advertisingIdentifier\|ATTrackingManager" \
  --include="*.swift" . | head -20

# Export compliance declaration
grep -n "ITSAppUsesNonExemptEncryption" */Info.plist */*.plist 2>/dev/null
```

SDK manifest detection and tracking-domain grep: [references/ios-store-compliance-detail.md](references/ios-store-compliance-detail.md).

## Gate 1: Privacy Manifest (PrivacyInfo.xcprivacy)

Every app target and each SDK (XCFramework or Swift package) must include a
`PrivacyInfo.xcprivacy` at its root. Required since May 1, 2024.

**Step 1.1 -- Audit or create the manifest.** Four top-level keys:

- `NSPrivacyTracking` (Bool): `true` only for cross-app/cross-site tracking; requires `NSPrivacyTrackingDomains`.
- `NSPrivacyTrackingDomains` ([String]): domains contacted for tracking; system blocks on ATT denial.
- `NSPrivacyCollectedDataTypes` ([Dict]): mirrors the nutrition labels (Gate 2).
- `NSPrivacyAccessedAPITypes` ([Dict]): one entry per required-reason API used by the app or its dependencies.

**Step 1.2 -- Declare required-reason APIs.** Run Product > Privacy Report (Xcode 15+)
for the auto-detected list. Add one `<dict>` to `NSPrivacyAccessedAPITypes` per flagged
API. Use only Apple's approved code strings; custom strings cause ITMS-91055 on upload.

```xml
<!-- UserDefaults -- most common; CA92.1 = app functionality -->
<dict>
  <key>NSPrivacyAccessedAPIType</key>
  <string>NSPrivacyAccessedAPICategoryUserDefaults</string>
  <key>NSPrivacyAccessedAPITypeReasons</key>
  <array><string>CA92.1</string></array>
</dict>
```

Other categories (FileTimestamp, SystemBootTime, DiskSpace, ActiveKeyboards) and the full reason-code table: [references/ios-store-compliance-detail.md](references/ios-store-compliance-detail.md).

**Step 1.3 -- Audit SDK manifests.** Any SDK listed in Privacy Report without a manifest
must be updated or replaced. Do not write SDK reasons into the app manifest; they must
live in the SDK's own `PrivacyInfo.xcprivacy`.

## Gate 2: App Privacy nutrition labels

Declared in App Store Connect > App > App Privacy. Must cover first-party code AND every
third-party SDK. Build from evidence: review merged `NSPrivacyCollectedDataTypes` across
all manifests, trace every off-device network call, answer three dimensions per data type
(Used to track you / Linked to you / Not linked to you), and set a privacy policy URL
(required to submit). When a field is genuinely `unknown`, mark it and ask first -- a
false "no collection" answer is a Guideline 5.1.1 violation. Full data-type table:
[references/ios-store-compliance-detail.md](references/ios-store-compliance-detail.md).

## Gate 3: App Tracking Transparency (ATT)

Required before accessing IDFA or any cross-app/cross-site tracking (iOS 14.5+).

- Call `ATTrackingManager.requestTrackingAuthorization` after the first meaningful screen, not in `applicationDidFinishLaunching`.
- Set `NSUserTrackingUsageDescription` in `Info.plist`; vague strings cause rejection.
- Set `NSPrivacyTracking = true` and list tracking domains in `NSPrivacyTrackingDomains`.
- On denial: no IDFA, no probabilistic fingerprinting, no IP re-ID; use SKAdNetwork only.

No IDFA or cross-app tracking: set `NSPrivacyTracking = false`, omit
`NSPrivacyTrackingDomains`, skip the ATT prompt. Unnecessary prompts cause rejections.

## Gate 4: Entitlements, metadata, and export compliance

**Entitlements audit.** For each key in `<Target>.entitlements`: confirm the capability
is enabled in the App ID on developer.apple.com and that the app actually uses it.
Remove unused entitlements. Apple rejects capabilities not exercised in the build
(HealthKit, NetworkExtension, UIBackgroundModes in particular). Full high-scrutiny list:
[references/ios-store-compliance-detail.md](references/ios-store-compliance-detail.md).

**Encryption / export compliance.** Add this key to `Info.plist` to avoid the per-build
manual answer in App Store Connect and unblock TestFlight immediately:

```xml
<key>ITSAppUsesNonExemptEncryption</key>
<false/>
```

Use `<false/>` when the app uses only OS-standard HTTPS/TLS, standard keychain, or
`CryptoKit` for signing/auth. Use `<true/>` plus a U.S. BIS ERN (uploaded in App Store
Connect > App > Compliance) for any custom or additional encryption.

**Metadata.** Screenshots and App Previews must match the actual build and device class. Guideline 2.3 is the most avoidable rejection.

## Readiness checklist (run before any submission)

```
[ ] PrivacyInfo.xcprivacy present at app-target root
[ ] All required-reason APIs declared with approved reason codes (Xcode Privacy Report clean)
[ ] Every third-party SDK has its own manifest (no SDK entries missing in Privacy Report)
[ ] NSPrivacyCollectedDataTypes matches the App Store Connect nutrition labels
[ ] Nutrition labels cover every off-device data point in first-party code and SDKs
[ ] Privacy policy URL set and accessible
[ ] ATT prompt implemented (if IDFA / cross-app tracking used); NSUserTrackingUsageDescription set
[ ] NSPrivacyTracking and NSPrivacyTrackingDomains consistent with ATT usage
[ ] All entitlements active in the App ID; unused entitlements removed
[ ] ITSAppUsesNonExemptEncryption declared in Info.plist (ERN on file if true)
[ ] App builds clean against latest stable Xcode (no private API, no deprecated frameworks)
[ ] Screenshots, previews, and description match the current build
[ ] TestFlight build tested on a device with a fresh account (smoke pass)
```

Mark each item PASS / FAIL / UNKNOWN. Do not declare submission-ready with any FAIL or
UNKNOWN outstanding; resolve or get an explicit decision first.

## Outbound checkpoint

Local work needs no approval. Outbound here (uploading to App Store Connect or TestFlight, saving nutrition labels, submitting for review, publishing a TestFlight link externally): stop, present exactly what would go out, and wait for an explicit "yes" (global consent law).

## References

- [references/ios-store-compliance-detail.md](references/ios-store-compliance-detail.md) -- remaining XML
  samples, full reason-code table, nutrition-label categories, high-scrutiny entitlements,
  review guideline hot spots, SDK tracking-domain grep.
- Apple, Privacy manifest files: https://developer.apple.com/documentation/bundleresources/privacy_manifest_files
- Apple, Describing required-reason APIs: https://developer.apple.com/documentation/bundleresources/describing-use-of-required-reason-api
- Apple, App Privacy Details: https://developer.apple.com/app-store/app-privacy-details/
- Apple, App Tracking Transparency: https://developer.apple.com/documentation/apptrackingtransparency
- Apple, Export compliance: https://developer.apple.com/documentation/security/complying-with-encryption-export-regulations
- Apple, App Store Review Guidelines: https://developer.apple.com/app-store/review/guidelines/
