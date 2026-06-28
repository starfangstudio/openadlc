<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
Consumed by the `error-monitoring` skill. Load on demand; do not load independently.

## SDK setup: Sentry

Run the wizard once per platform; it patches build files and generates credentials:

```bash
brew install getsentry/tools/sentry-wizard
sentry-wizard -i ios       # iOS: adds Xcode build phase + .sentryclirc
sentry-wizard -i android   # Android: patches build.gradle + writes sentry.properties
```

Unity: configure via **Tools > Sentry** in the Unity Editor (DSN, Auth Token, Org Slug,
Project Name). The SDK auto-initializes before the engine starts, catching engine crashes.

Minimum iOS init (AppDelegate or SwiftUI App initializer):

```swift
SentrySDK.start { options in
    options.dsn = "https://<key>@o<orgId>.ingest.sentry.io/<projectId>"
    options.tracesSampleRate = 0.2   // tune for production volume
    options.enableAutoSessionTracking = true
}
```

Keep the DSN in environment config or a CI secret, not hardcoded in source.

## SDK setup: Crashlytics (mobile alternative)

Add `GoogleService-Info.plist` (iOS), `google-services.json` (Android), or the Unity
Firebase package. Crash capture is automatic after SDK init; no extra code needed.

## Alerting triage loop

1. In Sentry: **Alerts > Create Alert > Sessions > Crash Free Session Rate**,
   threshold < 99 %, notify via email or Slack webhook.
2. Triage: new crash in dashboard > check symbolicated frames > reproduce
   locally > fix > verify crash no longer appears in the next build's event stream.

Never wait for user reports; the alert should fire before a user files a ticket.

## Verify: test crash snippets

Trigger a test crash and confirm it appears symbolicated in the dashboard:

```swift
// iOS Sentry test (remove before shipping)
SentrySDK.crash()

// Android Sentry test (remove before shipping)
throw RuntimeException("Sentry test crash")
```

Check: class and method names visible (not hex addresses), file names and line
numbers present for C# frames (Unity), no "Missing debug information" banner.
If frames are unsymbolicated, consult the symbolication reference.
