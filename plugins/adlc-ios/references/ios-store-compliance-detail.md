<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
Consumed by the `ios-store-compliance` skill. Load on demand; do not load independently.

## Detection script (run before any compliance work)

```bash
# Privacy Manifest present?
find . -name "PrivacyInfo.xcprivacy" -not -path "*/DerivedData/*"

# Third-party SDK manifests present (SPM packages and XCFrameworks)?
find . \( -name "Package.swift" -o -name "*.xcframework" \) \
  -not -path "*/DerivedData/*" | head -20
find . -name "PrivacyInfo.xcprivacy" -path "*/.build/*" | head -20  # SPM resolved

# Entitlements in use
find . -name "*.entitlements" -not -path "*/DerivedData/*"
cat <AppTarget>.entitlements

# Info.plist keys that affect review
/usr/libexec/PlistBuddy -c "Print" <path>/Info.plist 2>/dev/null | \
  grep -E "NSUsage|ITSApp|ITSEncryption|UIBackgroundModes|NSPrivacy"

# ATT usage site
grep -rn "requestTrackingAuthorization\|ASIdentifierManager\|advertisingIdentifier\|ATTrackingManager" \
  --include="*.swift" . | head -20

# SDK tracking domains (look for known attribution/ad SDKs)
grep -rn "AppLovin\|Facebook\|Meta\|Adjust\|AppsFlyer\|Branch\|Amplitude\|Mixpanel\|Firebase" \
  --include="*.swift" --include="Package.swift" --include="*.podspec" . | head -20

# Export compliance declaration
grep -n "ITSAppUsesNonExemptEncryption" */Info.plist */*.plist 2>/dev/null
```

## Required-reason API XML samples

Add one `<dict>` block per API category to `NSPrivacyAccessedAPITypes` in
`PrivacyInfo.xcprivacy`. Use only Apple-approved reason code strings; custom strings
cause ITMS-91055 on upload.

```xml
<!-- UserDefaults -->
<dict>
  <key>NSPrivacyAccessedAPIType</key>
  <string>NSPrivacyAccessedAPICategoryUserDefaults</string>
  <key>NSPrivacyAccessedAPITypeReasons</key>
  <array><string>CA92.1</string></array>
</dict>

<!-- File timestamp -->
<dict>
  <key>NSPrivacyAccessedAPIType</key>
  <string>NSPrivacyAccessedAPICategoryFileTimestamp</string>
  <key>NSPrivacyAccessedAPITypeReasons</key>
  <array><string>3B52.1</string></array>
</dict>

<!-- System boot time -->
<dict>
  <key>NSPrivacyAccessedAPIType</key>
  <string>NSPrivacyAccessedAPICategorySystemBootTime</string>
  <key>NSPrivacyAccessedAPITypeReasons</key>
  <array><string>35F9.1</string></array>
</dict>

<!-- Disk space -->
<dict>
  <key>NSPrivacyAccessedAPIType</key>
  <string>NSPrivacyAccessedAPICategoryDiskSpace</string>
  <key>NSPrivacyAccessedAPITypeReasons</key>
  <array><string>E174.1</string></array>
</dict>

<!-- Active keyboards -->
<dict>
  <key>NSPrivacyAccessedAPIType</key>
  <string>NSPrivacyAccessedAPICategoryActiveKeyboards</string>
  <key>NSPrivacyAccessedAPITypeReasons</key>
  <array><string>54BD.1</string></array>
</dict>
```

Reference: https://developer.apple.com/documentation/bundleresources/describing-use-of-required-reason-api

## Approved reason codes by category

| Category constant | Common approved codes |
|---|---|
| `NSPrivacyAccessedAPICategoryUserDefaults` | CA92.1 (app functionality), 1C8F.1 (to observe changes), AC6B.1 (read-write the app's own defaults), C56D.1 (access from an app extension) |
| `NSPrivacyAccessedAPICategoryFileTimestamp` | 3B52.1 (file the app created), C617.1 (inside app sandbox only) |
| `NSPrivacyAccessedAPICategorySystemBootTime` | 35F9.1 (measure elapsed time) |
| `NSPrivacyAccessedAPICategoryDiskSpace` | E174.1 (free disk space before write), 85F4.1 (health/medical records), 7D9E.1 (writing large file) |
| `NSPrivacyAccessedAPICategoryActiveKeyboards` | 54BD.1 (display appropriate keyboard), 3EC4.1 (for a custom keyboard extension) |

When in doubt about which code applies, mark it `unknown` and ask. Never invent a code.

## App Privacy nutrition-label categories

Build the `NSPrivacyCollectedDataTypes` entries in the app manifest and the matching
nutrition labels in App Store Connect from this reference. Cover first-party code AND
every third-party SDK.

For each data type, answer three dimensions:
- **Used to track you**: linked to identity across apps/sites (requires `NSPrivacyTracking = true`)
- **Linked to you**: tied to the user's identity within the app
- **Not linked to you**: collected but not associated with identity

Apple's top-level data categories (each has sub-types in App Store Connect):

| Category | Examples |
|---|---|
| Contact Info | Name, email, phone, address, user ID |
| Health & Fitness | Health records, fitness data |
| Financial Info | Credit/debit card, payment info |
| Location | Precise, coarse |
| Sensitive Info | Racial/ethnic origin, sexual orientation, religion, biometric |
| Contacts | Contacts from address book |
| User Content | Emails/texts, photos/videos, audio, gameplay content, customer support |
| Browsing History | Web browsing history |
| Search History | Search history |
| Identifiers | User ID, device ID |
| Purchases | Purchase history |
| Usage Data | Product interaction, advertising data, crash data, performance data, other diagnostics |
| Diagnostics | Crash data, performance data, other diagnostics |
| Other Data | Any type not listed |

A false "no collection" answer is a Guideline 5.1.1 violation.
Privacy policy URL is required before labels can be submitted.

## Encryption / export compliance declaration

Add this key to `Info.plist` to avoid the per-build manual answer in App Store Connect
and to unblock TestFlight immediately:

```xml
<key>ITSAppUsesNonExemptEncryption</key>
<false/>
```

Use `<false/>` when the app uses only:
- OS-standard HTTPS/TLS via `URLSession` or `Network.framework`
- Standard keychain APIs
- `CryptoKit` for signing or authentication (not novel algorithms)
- Apple Pay

Use `<true/>` (plus a valid U.S. BIS ERN on file) for any custom or additional
encryption beyond the list above. The ERN must be uploaded to App Store Connect under
App > Compliance.

Reference: https://developer.apple.com/documentation/security/complying-with-encryption-export-regulations

## Entitlements: high-scrutiny list

Apple may reject or request justification for capabilities not exercised in the build.
Remove any unused entitlement before submission.

| Entitlement key | Review notes |
|---|---|
| `com.apple.developer.healthkit` | Requires HealthKit purpose string; visible in Privacy Report |
| `com.apple.developer.networking.networkextension` | Requires use-case justification in review notes |
| `com.apple.developer.associated-domains` | Domains must resolve and serve `apple-app-site-association` |
| `aps-environment` | Must match push cert environment (dev vs. production) |
| `UIBackgroundModes` values | Justify each value; unused modes cause rejections |

## Review guideline hot spots

| Guideline | Common rejection reason |
|---|---|
| 2.3 | Screenshots/previews don't match the actual build or device class |
| 4.3 | Spam/duplicate of another app without meaningful differentiation |
| 5.1.1 | Inaccurate privacy nutrition labels; missing privacy policy |
| 5.1.2 | ATT not implemented when IDFA or cross-app tracking is used |
| 5.2 | Using private API or undocumented system calls |
| 2.1 | App crashes on launch or during review (test on real device with fresh account) |
