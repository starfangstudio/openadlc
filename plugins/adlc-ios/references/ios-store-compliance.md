<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
# iOS App Store Compliance: Quick Reference

Loaded on-demand by the `ios-store-compliance` skill. Do not inline this into the skill body.

---

## Privacy Manifest (PrivacyInfo.xcprivacy)

A `PrivacyInfo.xcprivacy` property-list file at the root of each target (app and SDK). Mandatory for all new and updated apps since May 1, 2024.

### Top-level keys

| Key | Type | Purpose |
|---|---|---|
| `NSPrivacyTracking` | Bool | `true` if the app or SDK uses data for tracking as defined by ATT |
| `NSPrivacyTrackingDomains` | [String] | Domains used for tracking; blocked if user denies ATT |
| `NSPrivacyCollectedDataTypes` | [Dict] | Data your app/SDK collects (see nutrition labels below) |
| `NSPrivacyAccessedAPITypes` | [Dict] | Required-reason APIs your code calls |

### Required-reason API categories (NSPrivacyAccessedAPITypes)

Each entry: `NSPrivacyAccessedAPIType` (string) + `NSPrivacyAccessedAPITypeReasons` ([string]).
Approved codes only -- Apple rejects custom strings.

| NSPrivacyAccessedAPIType | Approved reason codes (common) | Notes |
|---|---|---|
| `NSPrivacyAccessedAPICategoryUserDefaults` | `CA92.1` (app data only) | UserDefaults, CFPreferences |
| `NSPrivacyAccessedAPICategoryFileTimestamp` | `3B52.1` (user-visible file info within app container); `C617.1` (file from open/save dialog/drag-drop); `0A2A.1` (no path returned) | `FileManager`, `stat`, POSIX file timestamps |
| `NSPrivacyAccessedAPICategorySystemBootTime` | `35F9.1` (measure elapsed time); `8FFB.1` (bug reports only); `3D61.1` (health/fitness research with user consent) | `mach_absolute_time`, `sysctl`, `NSProcessInfo.systemUptime` |
| `NSPrivacyAccessedAPICategoryDiskSpace` | `7D9E.1` (display to user / manage storage / bug reports only) | `NSFileSystemFreeSize`, `VolumeAvailableCapacityForImportantUsage` |
| `NSPrivacyAccessedAPICategoryActiveKeyboard` | `3EC4.1` (custom keyboard); `54BD.1` (apps with text input fields to adjust UI) | `UITextInputMode.activeInputModes` |

For the full canonical list and latest reason codes, always verify against:
https://developer.apple.com/documentation/bundleresources/describing-use-of-required-reason-api

### Third-party SDK manifests

Every SDK distributed as an XCFramework, Swift package, or Xcode project must include its own `PrivacyInfo.xcprivacy`. When a dependency lacks one, Xcode's Privacy Report (Product > Privacy Report) flags it. Either get an updated SDK version or file a bug with the vendor; do not declare reasons on behalf of a third-party SDK in your own manifest.

---

## App Privacy Nutrition Labels (App Store Connect)

Declared in App Store Connect > App > App Privacy. Covers first-party code AND all third-party SDKs.

### Data type categories

| Category | Example subcategories |
|---|---|
| Contact Info | Name, Email Address, Phone Number, Physical Address |
| Health & Fitness | Health data, Fitness data |
| Financial Info | Payment Info, Credit Info |
| Location | Precise Location, Coarse Location |
| Sensitive Info | Racial/ethnic origin, sexual orientation, religious beliefs, etc. |
| Contacts | Contacts (device address book) |
| User Content | Emails/messages, Photos/Videos, Audio, Gameplay, Customer Support |
| Browsing History | Browsing History, Search History |
| Identifiers | User ID, Device ID |
| Purchases | Purchase History |
| Usage Data | Product Interaction, Advertising Data |
| Diagnostics | Crash Data, Performance Data |
| Other Data | Any data not in the above categories |

### Disclosure dimensions per data type

- **Used to track you** (cross-app/cross-site tracking, requires ATT)
- **Linked to you** (associated with identity but not tracking)
- **Not linked to you** (e.g., aggregated crash logs)

A data type not collected at all need not be declared. Anonymous data that cannot be reconstructed to identify a user counts as "not linked to you".

---

## App Tracking Transparency (ATT)

Call `ATTrackingManager.requestTrackingAuthorization(completionHandler:)` before accessing `ASIdentifierManager.shared().advertisingIdentifier` (IDFA) or any cross-app / cross-site tracking. Rules:

- Do NOT call the ATT prompt from `applicationDidFinishLaunching`; call after the app's first meaningful screen appears.
- Present a pre-prompt screen explaining the value exchange BEFORE the system dialog. Apple does not prohibit this.
- If the user denies, fall back to fingerprint-free attribution (SKAdNetwork / Privacy Clean Room) -- do not attempt probabilistic re-identification.
- Set `NSPrivacyTracking = true` in the manifest AND list the tracking domains in `NSPrivacyTrackingDomains` so the system can block them on denial.

---

## App Store Review Guideline Hot Spots (2026)

| Guideline | Issue | Fix |
|---|---|---|
| 2.1 App Completeness | Crashes, broken flows, placeholder content at review time | Run a full smoke pass on a device in a fresh account before submitting |
| 2.3 Accurate Metadata | Screenshots/previews don't match the actual build | Update assets; no future features, no competitor comparisons |
| 2.5.1 Software Requirements | Private APIs, deprecated frameworks, old Xcode/SDK | Build with the latest stable Xcode; run `xcrun nm` or PrivacyReport to detect private API use |
| 3.1.1 In-App Purchase | Digital goods using external payment | Route all digital purchases through StoreKit; only physical goods / reader apps are exempt |
| 4.0 Minimum Functionality | App is a thin web wrapper | Add native features with real value beyond a WebView |
| 5.1.1 Data Collection | Privacy labels or manifest inconsistent with code | Audit with Xcode Privacy Report; match labels to the merged entitlements and network calls |
| 5.1.2 Data Sharing | Third-party data shared without consent | Gate all sharing on explicit user consent before first share |
| 1.2 User-Generated Content | UGC without moderation/reporting/blocking | Ship moderation, reporting, and blocking before submitting UGC features |

---

## Encryption / Export Compliance

Set in `Info.plist`:

```xml
<key>ITSAppUsesNonExemptEncryption</key>
<false/>
```

Use `<false/>` when the app uses only standard OS HTTPS/TLS and no additional encryption. Use `<true/>` plus an ERN (Encryption Registration Number) when the app implements custom or additional encryption. Declaring this key in `Info.plist` avoids the per-build manual answer in App Store Connect and removes the TestFlight compliance hold.

Exempt categories (BIS ENC items): HTTPS/TLS via `URLSession`/`Network.framework`, standard keychain operations, `CryptoKit` for authentication/signing only, and Apple Pay. Custom symmetric/asymmetric crypto or VPN protocols are NOT exempt.

---

## References

- Apple: Describing use of required reason APIs -- https://developer.apple.com/documentation/bundleresources/describing-use-of-required-reason-api
- Apple: Privacy manifest files -- https://developer.apple.com/documentation/bundleresources/privacy_manifest_files
- Apple: App Privacy Details -- https://developer.apple.com/app-store/app-privacy-details/
- Apple: User Privacy and Data Use -- https://developer.apple.com/app-store/user-privacy-and-data-use/
- Apple: App Tracking Transparency -- https://developer.apple.com/documentation/apptrackingtransparency
- Apple: Complying with Encryption Export Regulations -- https://developer.apple.com/documentation/security/complying-with-encryption-export-regulations
- Apple: ITSAppUsesNonExemptEncryption -- https://developer.apple.com/documentation/bundleresources/information-property-list/itsappusesnonexemptencryption
- Apple: App Store Review Guidelines -- https://developer.apple.com/app-store/review/guidelines/
