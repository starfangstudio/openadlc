---
name: android-compliance
description: >-
  Google Play compliance for an Android app. Triggers: "get the app ready for Play",
  "meet Play's target API level", "bump targetSdk so Play accepts the update", "fill out
  the Data safety form", "audit runtime permissions", "we got a Play policy rejection",
  "declare data collection/sharing". Covers target-SDK deadlines, the runtime-permission
  least-privilege bar, the Data safety declaration, and the operator's explicit yes before submission.
version: 0.1.0
---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# Android Play compliance

Three gates an app must clear to ship and stay on Google Play: it **targets a
recent enough API level**, it **requests only the permissions its core feature
needs**, and its **Data safety declaration matches what the code actually does**.
A miss on any one gets the listing blocked, hidden, or rejected.

## Detect first

```bash
# What does the app currently target / require?
grep -rEn "targetSdk|compileSdk|minSdk" app/build.gradle* gradle/libs.versions.toml
# Every permission the merged manifest will carry (incl. from libraries)
grep -rn "uses-permission" app/src/main/AndroidManifest.xml
./gradlew :app:processReleaseManifest    # then read app/build/.../AndroidManifest.xml for the MERGED set
```

The merged manifest is what Play sees, third-party SDKs inject permissions and
data collection you did not write. Audit the merged result, not just your source.

## Gate 1: target API level

Configure `targetSdk` in the app module (via the version catalog where one
exists). Targeting a recent level keeps the app discoverable on newer OS versions
while `minSdk` still controls how far back it runs.

| App / track | Required target (as of the Aug 31, 2025 requirement) |
|---|---|
| New apps + any update (phones/tablets) | **API 35** (Android 15) or higher |
| Wear OS, Android TV, Android Automotive updates | **API 34** (Android 14) or higher |
| Existing app, to stay available to new users on newer OS | **API 34** (Android 14) or higher |

- Below the bar, Play blocks new submissions and the listing is hidden from
  devices running an OS **newer** than the app's target.
- An **extension** (to Nov 1, 2025 for the 2025 wave) is requestable from Play
  Console when more time is needed. Only permanently-private internal-distribution
  apps are exempt.
- These levels and dates advance every year: **verify the current requirement
  against the official page (linked below) before quoting a number**; do not
  assume this table is still current.
- Bumping `targetSdk` is a behavior change: run the module's tests and a smoke
  pass, because each level opts the app into new restrictions (background limits,
  permission changes, stricter intents). Don't bump blind.

## Gate 2: runtime permissions (least privilege)

The bar: a permission is justified **only if the app's core, user-facing feature
cannot work without it** and a narrower alternative does not exist. Play rejects
apps that over-request or use a permission for something other than the declared
purpose.

- **Prefer a no-permission alternative.** Photo/file picker, document picker,
  `ACTION_*` intents, and the Health Connect / Credential Manager style APIs let
  the user grant one item without a broad permission. Use them before declaring
  `READ_MEDIA_*`, `READ_EXTERNAL_STORAGE`, camera, etc.
- **Request at point of use, with rationale**, not up front. Show the in-context
  explanation, then the system dialog, and degrade gracefully on denial, never
  block the app or re-prompt in a loop.
- **Location:** request `COARSE` unless a feature genuinely needs `FINE`; request
  background location **separately and later**, only with a clear background use.
- **High-risk permissions** (SMS, Call Log, `MANAGE_EXTERNAL_STORAGE`,
  `AccessibilityService`, `QUERY_ALL_PACKAGES`, exact alarms) need an approved
  *permitted use* and often a Play Console declaration form. If the core feature
  is not on Google's allowed list, do not ship the permission.
- **Remove the unused.** Drop permissions no longer used, and add
  `tools:node="remove"` to strip ones a library injects that the feature does not
  need.

## Gate 3: Data safety declaration

Every app on Play (including test tracks) must complete the **Data safety** form,
and the declaration must be **truthful and complete**: covering data collected or
shared by **third-party SDKs**, not just first-party code. A mismatch between the
form and observed behavior is a policy violation.

For each data type the app touches, the form asks:

- **Collected vs. shared** (sent off device to a third party), and **why**
  (purpose: app functionality, analytics, ads, …).
- Whether collection is **required or optional** for the user.
- Whether data is **encrypted in transit** and whether users can **request
  deletion**.
- A linked **privacy policy** is required to complete the form.

Build the declaration from evidence, not memory: the merged-manifest permissions,
the network calls the app makes, and each SDK's published data-collection
disclosure. When a field is genuinely unknown, mark it `unknown` and ask, never
invent a "no collection" answer to clear the form.

## Stop-and-verify

Before calling the app "Play-ready", confirm with a pass/fail check:
1. `targetSdk` meets the current requirement for this app's track (verified
   against the official page, not assumed), and the module's tests pass at the
   new level.
2. Every merged-manifest permission maps to a named core feature; none is unused
   or library-injected-and-unneeded.
3. The Data safety answers match the merged permissions, the actual network
   calls, and every SDK's disclosure.

## Outbound checkpoint

Local work needs no approval. Outbound here (submitting to Play, publishing a release/track, saving the Data safety declaration to Google): stop, present exactly what would go out, and wait for an explicit "yes" (global consent law).

## Privacy-first note

A privacy-first app keeps Gate 2/3 trivial by collecting almost nothing: request
the narrowest permission a feature needs, prefer pickers/intents over broad
storage access, and keep the Data safety form honest by sending no PII and no
unique identifiers off device (see the telemetry rule). The fewer permissions and
the less data leaves the device, the smaller the compliance surface.

## References

- Meet Google Play's target API level requirement, Android Developers:
  https://developer.android.com/google/play/requirements/target-sdk
- Permissions and APIs that access sensitive information (least-privilege policy), Play Console Help: https://support.google.com/googleplay/android-developer/answer/16558241
- Provide information for Google Play's Data safety section, Play Console Help:
  https://support.google.com/googleplay/android-developer/answer/10787469
- App permissions best practices: Android Developers:
  https://developer.android.com/training/permissions/usage-notes
