<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
# iOS Navigation Reference

Supporting detail for the `ios-navigation` skill. Covers complete patterns for
typed route enums, AppRouter, deep-link decoding, and cross-module navigation wiring.

## Typed route enum (Interface target)

Route types live in `<Feature>Interface` so any feature can push to them without
importing the Impl target.

```swift
// Packages/<Feature>/Sources/<Feature>Interface/<Feature>Route.swift
import Foundation

public enum <Feature>Route: Hashable, Sendable {
    case list
    case detail(id: String)
    case settings
}
```

Rules:
- Conform to `Hashable` and `Sendable` (required for `NavigationPath` and Swift 6).
- Pass primitive IDs only (String, UUID, Int). Never pass model objects across
  feature boundaries; the destination view fetches from the data layer on appear.
- Extend with new cases in the Interface target; the app-level `.navigationDestination`
  switch picks them up automatically.

## AppRouter (@Observable, @MainActor)

```swift
// AppTarget / RootCoordinator (knows all Impl targets)
import Observation
import SwiftUI
import FeatureAInterface
import FeatureBInterface

@Observable @MainActor
final class AppRouter {
    var path = NavigationPath()

    func push(_ route: some Hashable & Sendable) {
        path.append(route)
    }

    func pop() {
        guard !path.isEmpty else { return }
        path.removeLast()
    }

    func popToRoot() {
        path = NavigationPath()
    }

    // Deep-link entry point: replaces the entire path
    func apply(deepLink: AppDeepLink) {
        path = NavigationPath()
        switch deepLink {
        case .featureADetail(let id):
            path.append(FeatureARoute.detail(id: id))
        case .featureBSettings:
            path.append(FeatureBRoute.settings)
        }
    }
}
```

Inject `AppRouter` into the environment from the composition root. Feature views read
`@Environment(AppRouter.self)` and call `router.push(FeatureARoute.detail(id:))`;
they never import each other's Impl target.

## RootView: NavigationStack wiring

```swift
// AppTarget
import SwiftUI
import FeatureAInterface
import FeatureAImpl        // only the app target does this
import FeatureBInterface
import FeatureBImpl

struct RootView: View {
    @Environment(AppRouter.self) private var router

    var body: some View {
        @Bindable var router = router
        NavigationStack(path: $router.path) {
            FeatureAListView()
                // Register every route type the stack may receive
                .navigationDestination(for: FeatureARoute.self) { route in
                    switch route {
                    case .list:      FeatureAListView()
                    case .detail(let id): FeatureADetailView(id: id)
                    case .settings:  FeatureASettingsView()
                    }
                }
                .navigationDestination(for: FeatureBRoute.self) { route in
                    switch route {
                    case .settings: FeatureBSettingsView()
                    // ...
                    }
                }
        }
    }
}
```

Key: all `.navigationDestination(for:)` registrations must be attached in the same
`NavigationStack` scope (or a descendant that is always in the view hierarchy). Late
registrations (in a lazily-loaded view) will not resolve routes pushed before the view
appears.

## Deep-link decoding (URL-based)

```swift
// AppDeepLink.swift (AppTarget)
enum AppDeepLink {
    case featureADetail(id: String)
    case featureBSettings

    // e.g. myapp://featureA/detail?id=abc123
    init?(url: URL) {
        guard url.scheme == "myapp",
              let host = url.host else { return nil }
        let pathComponents = url.pathComponents.filter { $0 != "/" }
        switch (host, pathComponents.first) {
        case ("featureA", "detail"):
            let id = URLComponents(url: url, resolvingAgainstBaseURL: false)?
                .queryItems?.first(where: { $0.name == "id" })?.value
            guard let id else { return nil }
            self = .featureADetail(id: id)
        case ("featureB", "settings"):
            self = .featureBSettings
        default:
            return nil
        }
    }
}

// In @main App struct
.onOpenURL { url in
    if let link = AppDeepLink(url: url) {
        router.apply(deepLink: link)
    }
}
```

## NavigationView deprecation map

| Old pattern | Replacement |
|---|---|
| `NavigationView { ... }` | `NavigationStack { ... }` (iOS 16+) |
| `NavigationLink(destination:isActive:)` | `router.push(Route.detail(id:))` + `.navigationDestination(for:)` |
| `NavigationLink(tag:selection:)` | `NavigationPath.append` + typed destination |
| `@EnvironmentObject` coordinator | `@Observable AppRouter` via `.environment(router)` |

## Cross-module navigation rule

A feature pushing to another feature:

```swift
// FeatureA view -- imports FeatureBInterface only, not FeatureBImpl
import FeatureBInterface
import SwiftUI

struct FeatureADetailView: View {
    @Environment(AppRouter.self) private var router

    var body: some View {
        Button("Go to B Settings") {
            router.push(FeatureBRoute.settings)
        }
    }
}
```

The app's `.navigationDestination(for: FeatureBRoute.self)` resolves the route to
the concrete `FeatureBSettingsView` (which lives in `FeatureBImpl`). Feature A never
imports Feature B's Impl target.

## References

- Apple, SwiftUI NavigationStack:
  https://developer.apple.com/documentation/swiftui/navigationstack
- Apple, NavigationPath:
  https://developer.apple.com/documentation/swiftui/navigationpath
- Apple, navigationDestination(for:destination:):
  https://developer.apple.com/documentation/swiftui/view/navigationdestination(for:destination:)
- Apple, onOpenURL(_:):
  https://developer.apple.com/documentation/swiftui/view/onopenurl(perform:)
