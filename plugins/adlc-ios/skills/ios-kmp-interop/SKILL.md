---
name: ios-kmp-interop
description: >-
  This skill should be used when the user asks to "wire a SwiftUI app over a Kotlin
  Multiplatform shared core", "integrate KMP into iOS", "embed the shared Kotlin module
  in the iOS target", "add the KMP XCFramework to the iOS app", "call Kotlin from Swift",
  "bridge KMP to SwiftUI", "set up expect/actual for iOS", "use SKIE for Swift async",
  "consume Kotlin Flows in Swift", "add the shared module as a SwiftPM local package",
  "embed CMP in a SwiftUI screen", "UIViewControllerRepresentable for Compose",
  "decide whether to share UI with CMP or keep native SwiftUI", or "wire KMP domain
  layer to SwiftUI views". Covers the SwiftUI-shell-over-KMP-shared-logic stance: share
  domain and data in Kotlin, keep UI in native SwiftUI. Detects KMP presence and
  integration method, configures the Gradle XCFramework build, wires it into the iOS SPM
  graph, wraps KMP types with thin Swift adapters, bridges suspend/Flow via SKIE or
  KMP-NativeCoroutines, and advises when Compose Multiplatform shared UI pays versus
  when native SwiftUI is correct.
version: 0.1.0
---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# iOS KMP interop

Wire a SwiftUI shell over a Kotlin Multiplatform shared core. The standing rule:
**share domain and data in Kotlin; keep every design-led surface in native SwiftUI.**
CMP shared UI is viable only for utilitarian screens; never impose it on flagship surfaces.

## Step 1: Detect first

Never assume KMP or CMP is present:

```bash
# KMP module with iOS targets?
find . -name "build.gradle.kts" -not -path "*/build/*" \
  | xargs grep -l "iosArm64\|iosSimulatorArm64" 2>/dev/null | head -5
# Integration method: CocoaPods (Podfile), SPM binary (binaryTarget in Package.swift)?
find . -name "Podfile" | head -3
find . -name "Package.swift" -not -path "*/build/*" \
  | xargs grep -l "binaryTarget\|XCFrameworks" 2>/dev/null | head -5
# Async bridge (SKIE / KMP-NativeCoroutines)?
find . -name "build.gradle.kts" | xargs grep -l "skie\|nativecoroutines" 2>/dev/null
```

Record: KMP module name, iOS targets, integration method, async bridge, minimum iOS
deployment. Mark anything not found `unknown`. Pick integration method from the decision
table in [references/ios-kmp-interop.md](../../references/ios-kmp-interop.md) before proceeding.

## Step 2: Configure the Gradle XCFramework

In `shared/build.gradle.kts`, add `XCFramework("Shared")` and call `xcf.add(this)` for
`iosArm64()` and `iosSimulatorArm64()`, with `isStatic = true` to avoid dynamic linking
issues. Full snippet in the reference.

Build:
```bash
./gradlew :shared:assembleSharedXCFrameworkDebug
# Output: shared/build/XCFrameworks/debug/Shared.xcframework
```

## Step 3: Wire into the iOS SPM graph

**Monorepo (preferred):** `.package(path: "../shared/build/XCFrameworks/debug")` in
`Package.swift`, add `"Shared"` to the app target's dependencies. Full snippet in the
reference.

**Separate repos:** Compress the XCFramework, compute checksum, upload, use
`.binaryTarget(url:checksum:)`. Details in the reference.

Build the iOS app immediately after wiring to confirm the framework links cleanly.

## Step 4: Write thin Swift adapters

Expose factory functions from Kotlin in `iosMain`; Swift never constructs KMP concrete
types by name:

```kotlin
// shared/src/iosMain/kotlin/IOSEntryPoint.kt
fun createFeedRepository(): FeedRepository = RealFeedRepository()
```

Wrap in a Swift adapter inside the feature's SPM Impl target:

```swift
import Shared

final class KMPFeedAdapter: FeedService {
    private let repo = IOSEntryPointKt.createFeedRepository()

    func fetchFeed() async throws -> [FeedItem] {
        try await repo.fetchFeed()   // SKIE: suspend -> async directly
    }
}
```

Register the adapter in the app's composition root as the `FeedService` implementation.
Only the adapter (in Impl) and the composition root import `Shared`; Interface targets
never do.

## Step 5: Bridge async/Flow

Without a bridge, Kotlin `suspend` functions surface as callback APIs in Swift.

**Add SKIE** to `shared/build.gradle.kts` (`id("co.touchlab.skie") version "0.9.x"`)
for native `async/await` from suspend functions and `AsyncSequence` from Flows.
Check the current version at https://skie.touchlab.co/ before pinning.

**Alternative:** KMP-NativeCoroutines maps Flows to Combine publishers if SKIE is
unacceptable (e.g., binary size).

Sendable: KMP-generated types are not automatically `Sendable`. Wrap KMP calls in
`@MainActor`-isolated functions or apply `@unchecked Sendable` with a comment when the
type is provably immutable. Full patterns in the reference.

## Step 6: Embed CMP only when it pays

For utilitarian screens where CMP shared UI is justified, wrap
`ComposeUIViewController` in `UIViewControllerRepresentable` and add
`CADisableMinimumFrameDurationOnPhone = true` to `Info.plist`. Full code snippet and
the CMP-vs-SwiftUI decision table (Maps, Camera, flagship surfaces) are in
[references/ios-kmp-interop.md](../../references/ios-kmp-interop.md).

## Step 7: Verify (pass/fail)

```bash
./gradlew :shared:assembleSharedXCFrameworkDebug   # 1. KMP builds
xcodebuild build -workspace <App>.xcworkspace -scheme <AppScheme> \
  -destination 'platform=iOS Simulator,name=iPhone 16' | xcbeautify  # 2. iOS links
xcodebuild test -workspace <App>.xcworkspace -scheme <FeatureTests> \
  -destination 'platform=iOS Simulator,name=iPhone 16' | xcbeautify  # 3. adapter test
```

A clean build and a passing adapter test are the proof. Fix linker errors or Sendable
warnings at the bridge before declaring done.

## Outbound checkpoint

Local work needs no approval. Outbound here (pushing a KMP binary to a remote host, opening a PR, publishing the XCFramework as a remote Swift package): stop, present exactly what would go out, and wait for an explicit "yes" (global consent law).

## References

- [references/ios-kmp-interop.md](../../references/ios-kmp-interop.md) -- decision table, full Gradle
  + Package.swift snippets, expect/actual, SKIE setup, CMP code, Sendable guidance.
- JetBrains, iOS integration methods: https://kotlinlang.org/docs/multiplatform/multiplatform-ios-integration-overview.html
- JetBrains, SPM export: https://kotlinlang.org/docs/multiplatform/multiplatform-spm-export.html
- JetBrains, CMP + SwiftUI: https://kotlinlang.org/docs/multiplatform/compose-swiftui-integration.html
- Touchlab SKIE: https://skie.touchlab.co/
- KMP-NativeCoroutines: https://github.com/rickclephas/KMP-NativeCoroutines
