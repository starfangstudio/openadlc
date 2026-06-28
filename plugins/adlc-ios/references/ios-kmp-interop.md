<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
# KMP Interop Reference

Supporting detail for the `ios-kmp-interop` skill. Read this when you need exact
Gradle configuration, SKIE setup, or CMP integration patterns.

---

## Integration method decision tree

| Scenario | Recommended method |
|---|---|
| Monorepo, no CocoaPods deps | SwiftPM local package (`.package(path:)`) |
| Monorepo, CocoaPods deps in KMP | CocoaPods local podspec |
| Separate repos / distributed SDK | XCFramework exported as remote SwiftPM binary target |
| KMP + CMP sharing UI across platforms | CMP via `ComposeUIViewController` + `UIViewControllerRepresentable` |

---

## Gradle: build the XCFramework (local path integration)

In `shared/build.gradle.kts`:

```kotlin
import org.jetbrains.kotlin.gradle.plugin.mpp.apple.XCFramework

kotlin {
    val xcf = XCFramework("Shared")
    listOf(iosArm64(), iosSimulatorArm64()).forEach {
        it.binaries.framework {
            baseName = "Shared"
            isStatic = true
            xcf.add(this)
        }
    }
}
```

Build tasks:
```bash
./gradlew :shared:assembleSharedXCFrameworkDebug     # debug, simulator + device
./gradlew :shared:assembleSharedXCFrameworkRelease   # release
# Output: shared/build/XCFrameworks/debug/Shared.xcframework
```

---

## SwiftPM local-path binary target (monorepo)

In the iOS app's root `Package.swift` (or `xcodeproj` file reference):

```swift
// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "MyApp",
    platforms: [.iOS(.v17)],
    dependencies: [
        // KMP shared module -- path relative to Package.swift
        .package(path: "../shared/build/XCFrameworks/debug"),
    ],
    targets: [
        .target(
            name: "MyAppCore",
            dependencies: [
                .product(name: "Shared", package: "debug"),
            ]
        ),
    ]
)
```

Note: `isStatic = true` avoids dynamic linking issues when embedding the XCFramework
in an app target.

---

## expect/actual adapter pattern

Define the platform contract in Kotlin:

```kotlin
// shared/src/commonMain/kotlin/Platform.kt
expect class AppDatabase {
    fun fetchUser(id: String): User?
}

// shared/src/iosMain/kotlin/Platform.ios.kt
actual class AppDatabase {
    private val store = IosDataStore()
    actual fun fetchUser(id: String): User? = store.get(id)
}
```

Expose a factory from the shared module so Swift never constructs KMP internals:

```kotlin
// shared/src/iosMain/kotlin/IOSEntryPoint.kt
fun createAppDatabase(): AppDatabase = AppDatabase()
```

Swift usage:
```swift
import Shared

let db = IOSEntryPointKt.createAppDatabase()
let user = db.fetchUser(id: "42")
```

---

## SKIE: suspend functions and Flows

Without SKIE, Kotlin `suspend` functions surface as callback-based APIs in Swift.
With SKIE, they behave as native `async` functions:

Add to `shared/build.gradle.kts`:
```kotlin
plugins {
    id("co.touchlab.skie") version "0.9.x"   // check latest at skie.touchlab.co
}
```

After SKIE:
```swift
// Suspend function -> async/await (no callbacks)
let result = try await sharedRepository.fetchFeed()

// Flow<T> -> AsyncSequence
for await item in sharedRepository.feedFlow() {
    updateUI(item)
}
```

Without SKIE, use KMP-NativeCoroutines as an alternative; it maps `Flow` to Combine
publishers and suspend functions to async wrappers.

---

## CMP inside SwiftUI (UIViewControllerRepresentable bridge)

Define the Compose entry point in the shared module:

```kotlin
// shared/src/iosMain/kotlin/MainViewController.kt
import androidx.compose.ui.window.ComposeUIViewController

fun MainViewController(): UIViewController = ComposeUIViewController {
    SharedFeatureScreen()   // a @Composable from commonMain
}
```

Wrap in SwiftUI:

```swift
import SwiftUI
import Shared

struct SharedFeatureView: UIViewControllerRepresentable {
    func makeUIViewController(context: Context) -> UIViewController {
        Main_iosKt.MainViewController()
    }
    func updateUIViewController(_ uiViewController: UIViewController, context: Context) {}
}
```

Add to `Info.plist` for ProMotion support:
```xml
<key>CADisableMinimumFrameDurationOnPhone</key>
<true/>
```

---

## SwiftUI inside CMP

Pass a `UIHostingController` into the Compose tree via a lambda:

```kotlin
fun ComposeWithSwiftUIEmbedded(
    createSwiftUI: () -> UIViewController
): UIViewController = ComposeUIViewController {
    NativeViewHolder(createSwiftUI)
}
```

```swift
Main_iosKt.ComposeWithSwiftUIEmbedded(createSwiftUI: {
    UIHostingController(rootView: MapView())
})
```

Use this sparingly: native SwiftUI components (Maps, Camera, SafariViewController) are
the primary candidates.

---

## When CMP shared UI pays vs. does not

| Surface | Recommendation |
|---|---|
| Shared domain/data screens (feed, settings, account) | CMP shared UI is viable -- consistent logic, one test suite |
| Design-led marketing / onboarding / flagship screens | Native SwiftUI; design tokens, animations, Liquid Glass (iOS 26) |
| Maps, Camera, AR, SafariViewController | Native always; embed via UIViewControllerRepresentable |
| Notification / widget / App Clip surfaces | Native always; KMP has no access to these extension points |

Rule: if a screen is on the "show-off" path or uses platform-specific affordances
(Dynamic Island, Control Center, Share Sheet), write it in SwiftUI. Share the logic,
not the UI.

---

## Sendable and Swift 6 concurrency at the KMP boundary

KMP-generated Swift types are not automatically `Sendable`. Crossing the KMP boundary
inside a `Task` may produce Sendable warnings. Options:

1. Wrap the KMP call in a `@MainActor`-isolated function (safe for most repository reads).
2. Apply `@unchecked Sendable` with a comment if the KMP type is provably thread-safe
   (e.g., an immutable value object).
3. Use SKIE's structured concurrency support, which marks generated async calls
   appropriately.

---

## References

- JetBrains, iOS integration methods overview:
  https://kotlinlang.org/docs/multiplatform/multiplatform-ios-integration-overview.html
- JetBrains, Swift Package export (XCFramework + Package.swift):
  https://kotlinlang.org/docs/multiplatform/multiplatform-spm-export.html
- JetBrains, Compose Multiplatform + SwiftUI integration:
  https://kotlinlang.org/docs/multiplatform/compose-swiftui-integration.html
- Touchlab, SKIE (Swift Kotlin Interface Enhancer):
  https://skie.touchlab.co/
- rickclephas/KMP-NativeCoroutines (Flow -> Combine / async alternative):
  https://github.com/rickclephas/KMP-NativeCoroutines
- ge-org/multiplatform-swiftpackage Gradle plugin:
  https://github.com/ge-org/multiplatform-swiftpackage
