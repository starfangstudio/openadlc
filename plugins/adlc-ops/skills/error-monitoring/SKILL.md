---
name: error-monitoring
description: >-
  This skill should be used when the user asks to "add crash reporting", "set up Sentry",
  "wire up Crashlytics", "make crashes visible", "add error monitoring", "why are crashes
  unreadable", "fix obfuscated stack traces", "upload dSYM", "upload ProGuard mapping",
  "upload IL2CPP symbols", "set up release health", "track crash-free rate", "alert on
  crash spike", "configure crash alerts", "triage a crash", "scrub PII from crash reports",
  or "add error tracking day one". Covers Sentry (default, cross-platform: iOS, Android,
  Unity, backend) and Firebase Crashlytics (mobile alternative): SDK wiring, symbolication
  (iOS dSYM, Android ProGuard/R8, Unity IL2CPP), release health, alerting, PII scrubbing,
  and outbound approval (SDK sends data to a third party, so get the operator's explicit yes first).
version: 0.1.0
---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# Error monitoring

Wire crash and error reporting so production failures are visible on day one.
**Sentry** is the default: one SDK covers iOS, Android, Unity, and backend.
Use **Firebase Crashlytics** only when the project already depends on Firebase
and cross-platform error tracking in one dashboard is not needed.

## Detect first

Inspect the project before adding anything:

```bash
# iOS: SPM/CocoaPods dependencies
grep -r "Sentry\|Crashlytics\|Firebase" . \
  --include="Package.resolved" --include="Podfile.lock" -l 2>/dev/null

# Android: Gradle deps
grep -rn "sentry\|crashlytics\|firebase" . \
  --include="*.gradle" --include="*.gradle.kts" | grep -v "//\|#"

# Unity: manifest and packages
find . -name "packages-lock.json" -o -name "manifest.json" | \
  xargs grep -l "sentry\|firebase" 2>/dev/null

# Backend: package files
grep -rn "sentry" package.json requirements.txt pyproject.toml go.mod 2>/dev/null
```

Record: SDK present (`sentry` / `crashlytics` / `none`), platforms covered, whether
a DSN or `google-services.json` is configured. Mark anything not found `unknown`.

## SDK setup

**Sentry** -- run the wizard once per platform; it patches build files and writes credentials:

```bash
brew install getsentry/tools/sentry-wizard
sentry-wizard -i ios       # adds Xcode build phase + .sentryclirc
sentry-wizard -i android   # patches build.gradle + writes sentry.properties
```

Unity: configure via **Tools > Sentry** in the Unity Editor (DSN, Auth Token, Org Slug,
Project Name). The SDK auto-initializes before the engine starts.

Minimum iOS init (AppDelegate or SwiftUI App initializer):

```swift
SentrySDK.start { options in
    options.dsn = "https://<key>@o<orgId>.ingest.sentry.io/<projectId>"
    options.tracesSampleRate = 0.2
    options.enableAutoSessionTracking = true
}
```

Keep the DSN in a CI secret, not hardcoded in source.

**Crashlytics** -- drop in `GoogleService-Info.plist` (iOS) or `google-services.json`
(Android). Crash capture is automatic after SDK init; no extra code needed.

For full platform-specific init snippets (Android, Unity), see
[references/error-monitoring-detail.md](references/error-monitoring-detail.md).

## Symbolication

Unreadable stack traces are the #1 reason crash monitoring fails in production.
Configure symbol uploads before the first release build.

The Auth Token (`SENTRY_AUTH_TOKEN` / Firebase service account) needs `project:write`
scope and must reach the build step that produces the release artifact (local or CI).

For exact upload commands (iOS dSYM, Android ProGuard/R8, Unity IL2CPP) for both
Sentry and Crashlytics, see
[references/error-monitoring-symbolication.md](references/error-monitoring-symbolication.md).

## Release health

Enable per-release crash-free tracking immediately after SDK setup:

- Sentry: `options.enableAutoSessionTracking = true` (default on). Attach a release
  string (`options.releaseName = "myapp@1.2.3+45"`) so regressions surface per build.
  View under **Releases > Health**.
- Crashlytics: crash-free data is automatic once the SDK is initialized.

Target crash-free sessions >= 99.5 % before promoting a build to wider rollout.

## Alerting and triage

Set up at least one alert on day one:

1. In Sentry: **Alerts > Create Alert > Sessions > Crash Free Session Rate**,
   threshold < 99 %, notify via email or Slack webhook.
2. Triage: new crash in dashboard > check symbolicated frames > reproduce locally >
   fix > verify the crash no longer appears in the next build's event stream.

Rule: the alert fires before a user files a ticket.

## Privacy: scrub PII from crash reports

Crash reports are outbound data. Apply these rules before enabling any SDK:

- Do not attach user email, name, account ID, or device ID to Sentry events.
  Use an opaque internal ID (`options.user.id` set to a non-PII handle) if user
  context helps triage.
- Strip free-text fields from breadcrumbs: search queries, form values, URLs
  containing user tokens, error message strings that embed PII.
- Sentry `beforeSend` hook: filter or scrub sensitive keys before the event
  leaves the device.
- For full PII policy, defer to the `adlc-privacy` pack.

## Verify

Trigger a test crash and confirm it appears symbolicated in the dashboard:

```swift
// iOS -- remove before shipping
SentrySDK.crash()
```

```kotlin
// Android -- remove before shipping
throw RuntimeException("Sentry test crash")
```

Pass criteria: class and method names visible (not hex addresses), file names and line
numbers present for C# frames (Unity), no "Missing debug information" banner.
If frames are unsymbolicated, consult the symbolication reference.

## Outbound approval

Local work needs no approval. Outbound here (sending the first crash event to Sentry/Crashlytics, enabling the SDK in a release build that ships to users, or any privacy declaration change on the App Store, Play Store, or privacy policy that the SDK requires): stop and ask the operator for an explicit yes. Present exactly what would go out and wait for the yes before doing it (global consent law).

## References

- [references/error-monitoring-detail.md](references/error-monitoring-detail.md) (additional init
  snippets, Unity wizard detail)
- [references/error-monitoring-symbolication.md](references/error-monitoring-symbolication.md) (iOS dSYM,
  Android ProGuard/R8, Unity IL2CPP symbol upload commands for Sentry + Crashlytics)
- Sentry iOS SDK: https://docs.sentry.io/platforms/apple/guides/ios/
- Sentry Android SDK: https://docs.sentry.io/platforms/android/
- Sentry Unity SDK: https://docs.sentry.io/platforms/unity/
- Sentry Unity native support (IL2CPP): https://docs.sentry.io/platforms/unity/native-support/
- Sentry release health: https://docs.sentry.io/product/releases/health/
- Sentry alerts: https://docs.sentry.io/product/alerts/
- Firebase Crashlytics iOS: https://firebase.google.com/docs/crashlytics/ios/get-deobfuscated-reports
- Firebase Crashlytics Android: https://firebase.google.com/docs/crashlytics/get-deobfuscated-reports
- Firebase Crashlytics Unity: https://firebase.google.com/docs/crashlytics/unity/get-started
