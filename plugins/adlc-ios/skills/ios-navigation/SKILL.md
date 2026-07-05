---
name: ios-navigation
description: >-
  This skill should be used when the user asks to "set up type-safe navigation",
  "wire NavigationStack", "replace NavigationView", "add a typed route enum",
  "set up NavigationPath", "add a router", "push a route from a feature",
  "wire a deep link", "handle onOpenURL", "navigate between modules without
  importing Impl", "add navigationDestination", "decouple navigation across
  SPM modules", "set up an AppRouter", or "make navigation testable". Implements
  value-based NavigationStack navigation with typed route enums in the Interface
  SPM target, an @Observable AppRouter owning NavigationPath, decoupled
  cross-module navigation (features push routes, app resolves them), and deep-link
  decoding via onOpenURL. Detects existing navigation strategy first; never
  imposes NavigationStack on a project already using a coordinator pattern.
version: 0.1.0
---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# iOS navigation

Implement type-safe SwiftUI navigation: typed route enums in the Interface target,
an `@Observable AppRouter` owning `NavigationPath`, and deep-link decoding via
`onOpenURL`. Features push route values; the app resolves them. No feature imports
another feature's Impl target.

## Step 1: Detect first

Never overwrite an existing nav strategy. Inspect the project:

```bash
grep -rEln "NavigationStack|NavigationView|NavigationPath|Coordinator" \
  --include="*.swift" . | head -20
grep -rEln "navigationDestination|NavigationLink|Route\b|\.push\b" \
  --include="*.swift" . | head -20
grep -rEln "class.*Router|class.*Coordinator|onOpenURL" \
  --include="*.swift" . | head -10
```

Record: nav strategy, route type location, whether `AppRouter` exists, deep links
wired. Mark unknowns `unknown`; ask before generating anything. If `NavigationView`
is found, present a migration plan and wait for approval before touching files.

## Step 2: Add route enum to the Interface target

```swift
// Packages/<Feature>/Sources/<Feature>Interface/<Feature>Route.swift
public enum <Feature>Route: Hashable, Sendable {
    case list
    case detail(id: String)   // primitives only -- never model objects
}
```

`Hashable` is required by `NavigationPath`; `Sendable` is required for Swift 6.
Full patterns and the cross-module navigation rule:
[references/ios-navigation.md](../../references/ios-navigation.md).

## Step 3: Create or extend AppRouter

If no router exists, create one in the app target:

```swift
@Observable @MainActor
final class AppRouter {
    var path = NavigationPath()
    func push(_ route: some Hashable & Sendable) { path.append(route) }
    func pop() { guard !path.isEmpty else { return }; path.removeLast() }
    func popToRoot() { path = NavigationPath() }
    func apply(deepLink: AppDeepLink) { /* see reference */ }
}
```

Inject at the composition root via `.environment(router)`. Feature views read it
with `@Environment(AppRouter.self) private var router`. If a coordinator already
exists, adapt it to expose a `NavigationPath` binding; do not replace it wholesale.

## Step 4: Wire NavigationStack and deep links in the app target

Only the app target registers `.navigationDestination` (it is the only target that
imports Impl). Attach all registrations on a view that is always in the hierarchy;
late registration inside a lazily loaded view silently fails.

```swift
// @main App struct
private let router = AppRouter()

var body: some Scene {
    WindowGroup {
        NavigationStack(path: Bindable(router).path) {
            HomeView()
                .navigationDestination(for: <Feature>Route.self) { route in
                    switch route {
                    case .list:           <Feature>ListView()
                    case .detail(let id): <Feature>DetailView(id: id)
                    }
                }
        }
        .environment(router)
        .onOpenURL { url in
            if let link = AppDeepLink(url: url) { router.apply(deepLink: link) }
        }
    }
}
```

Full `AppDeepLink` URL-parse implementation:
[references/ios-navigation.md](../../references/ios-navigation.md).

## Step 5: Verify (pass/fail)

```bash
# Routes compile in isolation
swift build --package-path Packages/<Feature>

# Full app compiles with wired destinations
xcodebuild build \
  -workspace <App>.xcworkspace \
  -scheme <App> \
  -destination 'platform=iOS Simulator,name=iPhone 16,OS=latest' | xcbeautify

# Deep link resolves at runtime
xcrun simctl openurl booted "myapp://featureA/detail?id=test-123"
```

If `navigationDestination` does nothing, the registration is in a lazily loaded
view; move it to the root stack scope. If a `Sendable` error fires on the route
enum, add `& Sendable` in the Interface target.

## Guardrails

- Feature targets import only sibling Interface targets, never Impl targets.
- Pass primitive IDs between features; let the destination fetch the model on appear.
- `AppRouter` must be `@MainActor`; never mutate `path` from a background task.
- If the project uses TCA's `NavigationStackStore`, extend that pattern instead.

## Outbound checkpoint

Local work needs no approval. Anything outbound (publish, push, post) needs an explicit per-action "yes"; see the global consent law.

## References

- [references/ios-navigation.md](../../references/ios-navigation.md) -- AppRouter, deep-link
  URL decoder, cross-module nav rule, NavigationView migration table.
- Apple, NavigationStack (iOS 16+): https://developer.apple.com/documentation/swiftui/navigationstack
- Apple, NavigationPath: https://developer.apple.com/documentation/swiftui/navigationpath
- Apple, navigationDestination(for:destination:): https://developer.apple.com/documentation/swiftui/view/navigationdestination(for:destination:)
- Apple, onOpenURL(perform:): https://developer.apple.com/documentation/swiftui/view/onopenurl(perform:)
- [references/ios-architecture.md](../../references/ios-architecture.md) -- SPM interface/impl, @Observable, DI.
