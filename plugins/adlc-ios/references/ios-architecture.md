<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
# iOS Architecture Rules

Applied to SwiftUI-first, SPM-modular iOS targets in the cross-platform stack (KMP shared core; SwiftUI shell). Match what the project actually uses; never impose a pattern that is not present.

## Core principle: interface-first, impl-isolated

Features communicate through their public-interface SPM target only. An impl target must never depend on another feature's impl target. If two features interact, one exposes a protocol in its interface target; the other injects it. This keeps the DI graph acyclic and the public API surface narrow.

## SPM module structure (interface / impl split)

Every feature is a local SPM package containing exactly two targets:

```
Packages/
  FeatureX/
    Package.swift
    Sources/
      FeatureXInterface/   # protocols, models, route enum -- all public
      FeatureXImpl/        # views, @Observable models, data access -- package-internal
```

**Access-control rules:**

| Level | Where used |
|---|---|
| `public` | Protocols, models, route enums, factory functions in the Interface target only |
| `package` | Concrete types in the Impl target that must be visible to sibling targets in the same package (e.g., an internal helper shared between two Impl targets) |
| `internal` / private | Everything else inside Impl |

`package` (introduced Swift 5.9 / SE-0386) is the Gradle `implementation` visibility analog: visible across targets within the same SPM package, invisible to external consumers. Use it as the default access level for types in an Impl target that need to cross a target boundary inside the same package; do NOT promote them to `public`.

**Dependency edges:**
- `FeatureXImpl` depends on `FeatureXInterface` and on other features' Interface targets only.
- `AppTarget` depends on every Impl target to wire DI; feature targets never do this.
- Interface targets keep dependencies narrow: only on shared model/core targets, never on another feature's Impl.

**Package.swift skeleton:**

```swift
// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "FeatureX",
    platforms: [.iOS(.v17)],
    products: [
        .library(name: "FeatureXInterface", targets: ["FeatureXInterface"]),
        // Impl is NOT a product; the app target lists it as a local target dependency
    ],
    dependencies: [
        // external packages only
    ],
    targets: [
        .target(
            name: "FeatureXInterface",
            dependencies: []
        ),
        .target(
            name: "FeatureXImpl",
            dependencies: [
                .target(name: "FeatureXInterface"),
                // other features' Interface products here
            ]
        ),
        .testTarget(
            name: "FeatureXTests",
            dependencies: [.target(name: "FeatureXImpl")]
        ),
    ]
)
```

Add `FeatureXImpl` (not the product, the target) to the app's `dependencies` list in the workspace's root Package.swift or xcodeproj so DI wiring is reachable. `FeatureXInterface` is exposed as a `.library` product so other packages can depend on it.

## @Observable and state

Use `@Observable` (Swift 5.9+, Observation framework) for all view-model types. Prefer `@Observable` class over `ObservableObject`/`@Published`; do NOT use both in the same type. Rules:

- `@Observable` models are `@MainActor`-isolated by default in Xcode 26 with approachable concurrency; mark them `@MainActor` explicitly until the project-wide opt-in is confirmed (see Concurrency below).
- Views are structs; they read model properties directly. No `@State` wrapper needed for `@Observable` models passed into a view.
- Pass models through the SwiftUI environment only when a subtree genuinely needs them shared. Use `@Environment(ModelType.self)` with `.environment(model)`.
- For non-shared, leaf-owned state keep the model local (`@State var model = FeatureModel()`).

## Environment-based DI

The app entry point is the composition root. It creates concrete Impl instances and injects them via `.environment(_:)` and custom `EnvironmentKey`s:

```swift
@main struct MyApp: App {
    // Concrete types from *Impl targets -- only the app target knows about them
    private let featureX: any FeatureXService = RealFeatureXService(dep: ...)

    var body: some Scene {
        WindowGroup {
            RootView()
                .environment(\.featureX, featureX)
        }
    }
}
```

Define `EnvironmentKey` in the Interface target (uses the protocol type, not the concrete class). The default value should be a no-op or preview stub, never `fatalError` (that breaks SwiftUI previews):

```swift
// FeatureXInterface -- visible to views that only import the Interface target
struct FeatureXServiceKey: EnvironmentKey {
    static let defaultValue: any FeatureXService = PreviewFeatureXService()
}

extension EnvironmentValues {
    var featureX: any FeatureXService {
        get { self[FeatureXServiceKey.self] }
        set { self[FeatureXServiceKey.self] = newValue }
    }
}
```

## Navigation: type-safe NavigationStack

Feature route types live in the Interface target so any feature can navigate to them. The app (or a root coordinator) owns the `NavigationPath` and binds `.navigationDestination(for:)`:

```swift
// FeatureXInterface
public enum FeatureXRoute: Hashable {
    case detail(id: String)
    case settings
}

// App / RootCoordinator
@Observable @MainActor class AppRouter {
    var path = NavigationPath()

    func navigate(to route: some Hashable) { path.append(route) }
    func pop() { guard !path.isEmpty else { return }; path.removeLast() }
}
```

Pass primitive IDs between features (never concrete model objects). Let the destination's @Observable model fetch from the data layer on appear. Features never import each other's Impl target; they navigate by pushing a route value from the Interface target.

## Concurrency / Swift 6 isolation

- All `@Observable` view-model types should be `@MainActor`-isolated.
- SPM packages do NOT automatically get Swift 6.2 approachable concurrency (`nonisolatedNonsendingByDefault`); opt in explicitly per target with `swiftSettings: [.enableUpcomingFeature("NonisolatedNonsendingByDefault")]`.
- Use `async/await` + structured concurrency for data access; avoid `Task.detached` and unstructured concurrency in view-models.
- KMP bridge boundary: mark any KMP-shared type crossings where `Sendable` conformance is needed; use `@unchecked Sendable` as a last resort with a comment explaining why it is safe.

## Design system

Prefer the project's shared design-system tokens and components over raw SwiftUI primitives. Token targets (color, type, spacing) belong in a `DesignSystemInterface` target; component implementations in `DesignSystemImpl`. Import only the Interface target from feature targets.

## References

- Swift Evolution SE-0386, "Package Access Modifier": https://github.com/apple/swift-evolution/blob/main/proposals/0386-package-access-modifier.md
- Swift 5.9 Release Notes (package keyword): https://www.swift.org/blog/swift-5.9-released/
- Apple, "Migrating from ObservableObject to the Observable macro": https://developer.apple.com/documentation/swiftui/migrating-from-the-observable-object-protocol-to-the-observable-macro
- Apple, SwiftUI NavigationStack: https://developer.apple.com/documentation/swiftui/navigationstack
- Guy Cohen, "Local SPM Mastering Modularization (Xcode 26)": https://medium.com/@guycohendev/local-spm-mastering-modularization-with-swift-package-manager-xcode-15-e37b14c36199
