<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
Consumed by the `ios-module-scaffolder` skill. Load on demand; do not load independently.

---

## Interface target: source files

**`Packages/<Feature>/Sources/<Feature>Interface/<Feature>Service.swift`:**

```swift
import Foundation

public protocol <Feature>Service: Sendable {
    func fetchThing(id: String) async throws -> <Feature>Thing
}

public struct <Feature>Thing: Hashable, Sendable {
    public let id: String
    public let name: String
    public init(id: String, name: String) { self.id = id; self.name = name }
}
```

**`Packages/<Feature>/Sources/<Feature>Interface/<Feature>Route.swift`:**

```swift
public enum <Feature>Route: Hashable, Sendable {
    case detail(id: String)
    // extend per feature
}
```

**`Packages/<Feature>/Sources/<Feature>Interface/<Feature>EnvironmentKey.swift`:**

```swift
import SwiftUI

struct <Feature>ServiceKey: EnvironmentKey {
    // Default is a no-op preview stub -- never fatalError (breaks Previews)
    static let defaultValue: any <Feature>Service = Preview<Feature>Service()
}

public extension EnvironmentValues {
    var <feature>Service: any <Feature>Service {
        get { self[<Feature>ServiceKey.self] }
        set { self[<Feature>ServiceKey.self] = newValue }
    }
}
```

---

## Impl target: source files

**`Packages/<Feature>/Sources/<Feature>Impl/Real<Feature>Service.swift`:**

```swift
import <Feature>Interface

// package: visible to sibling targets in this package; invisible externally
package final class Real<Feature>Service: <Feature>Service {
    // Inject collaborators from other features' Interface targets only
    init() {}

    public func fetchThing(id: String) async throws -> <Feature>Thing {
        // implementation
    }
}
```

**`Packages/<Feature>/Sources/<Feature>Impl/<Feature>View.swift`:**

```swift
import SwiftUI
import <Feature>Interface

struct <Feature>View: View {
    @Environment(\.<feature>Service) private var service
    @State private var model = <Feature>ViewModel()

    var body: some View {
        // ...
    }
}
```

**`Packages/<Feature>/Sources/<Feature>Impl/<Feature>ViewModel.swift`:**

```swift
import Observation
import <Feature>Interface

@Observable @MainActor
final class <Feature>ViewModel {
    private(set) var things: [<Feature>Thing] = []
    var error: Error?

    func load(using service: any <Feature>Service, id: String) async {
        do { things = [try await service.fetchThing(id: id)] }
        catch { self.error = error }
    }
}
```

---

## Package.swift manifest

```swift
// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "<Feature>",
    platforms: [.iOS(.v17)],        // match detected minimum deployment
    products: [
        // Interface is a public product; Impl is NOT (app target wires it directly)
        .library(name: "<Feature>Interface", targets: ["<Feature>Interface"]),
    ],
    dependencies: [
        // .package(url: "...", from: "...") for any external deps
        // .package(path: "../CoreInterface") for sibling local packages
    ],
    targets: [
        .target(
            name: "<Feature>Interface",
            dependencies: []
        ),
        .target(
            name: "<Feature>Impl",
            dependencies: [
                .target(name: "<Feature>Interface"),
                // other features' Interface products here, never their Impl
            ]
        ),
        .testTarget(
            name: "<Feature>Tests",
            dependencies: [.target(name: "<Feature>Impl")]
        ),
    ]
)
```

---

## Wiring: app target and DI graph

**A. Root Package.swift (SPM-managed workspace):** add `.package(path: "Packages/<Feature>")` to `dependencies`; add `"<Feature>Impl"` (the target, not the product) to the app target's `dependencies`. For Xcode-managed projects: File > Add Package Dependencies > select the local path.

**B. NavigationStack destination** (AppRootView or RootCoordinator, import both `<Feature>Interface` and `<Feature>Impl`):

```swift
.navigationDestination(for: <Feature>Route.self) { route in
    switch route {
    case .detail(let id): <Feature>View(id: id)
    }
}
```

**C. Composition root injection** (only the app target knows about Impl types):

```swift
@main struct MyApp: App {
    private let featureService: any <Feature>Service = Real<Feature>Service()

    var body: some Scene {
        WindowGroup {
            RootView()
                .environment(\.<feature>Service, featureService)
        }
    }
}
```

---

## Verify commands

```bash
# Build the new package targets in isolation
swift build --package-path Packages/<Feature>

# Or via xcodebuild if the workspace is Xcode-managed
xcodebuild build \
  -workspace <App>.xcworkspace \
  -scheme <Feature>Impl \
  -destination 'platform=iOS Simulator,name=iPhone 16'

# Run generated tests
xcodebuild test \
  -workspace <App>.xcworkspace \
  -scheme <Feature>Tests \
  -destination 'platform=iOS Simulator,name=iPhone 16'
```

A clean build proves the targets compile, the `package` access level is respected (no "cannot access" errors across targets), and the DI wiring resolves. Fix any missing EnvironmentKey default or `Sendable` violation at the KMP bridge boundary before claiming done.
