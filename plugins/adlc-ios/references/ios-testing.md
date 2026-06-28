<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
# iOS testing reference

Companion to the `ios-testing` skill. Covers patterns that would bloat the skill body.

## Swift Testing anatomy

```swift
import Testing

// Group tests for a type in a struct, not a class
@Suite("FeedViewModel")
struct FeedViewModelTests {

    // Async test; #expect replaces XCTAssertEqual
    @Test func loadsItemsOnAppear() async {
        let store = FeedViewModel(service: StubFeedService(items: .fixture))
        await store.load()
        #expect(store.items.count == 3)
        #expect(store.isLoading == false)
    }

    // #require stops the test on failure (like XCTUnwrap)
    @Test func itemHasValidID() throws {
        let items = [FeedItem].fixture
        let first = try #require(items.first)
        #expect(!first.id.isEmpty)
    }

    // Parameterized: one test entry per argument, all run in parallel
    @Test("Validates edge inputs", arguments: ["", " ", String(repeating: "a", count: 201)])
    func rejectsInvalidTitle(title: String) {
        #expect(!FeedItem.isValidTitle(title))
    }

    // Serialized suite: when test order or shared state requires sequential execution
    @Suite(.serialized)
    struct OrderedSideEffects {
        @Test func step1() { /* ... */ }
        @Test func step2() { /* ... */ }
    }
}
```

Key rules:
- `@Suite` is a struct, not a class. Each `@Test` method can be `async throws`.
- `#expect` never throws; it records a failure and continues. `#require` throws on failure, stopping the test.
- Parameterized arguments must be `Sendable`. Pass value types (IDs, enums, primitives), not actors.
- Tags group tests across suites: `@Test(.tags(.regression))`. Define tags once in a shared `Tag+App.swift`.
- Do not mix XCTest and Swift Testing inside the same type. Migrate test-by-test.

## @Observable store testing pattern

`@Observable` stores are `@MainActor`-isolated. Test them with `await MainActor.run` or mark the test suite `@MainActor`:

```swift
@Suite @MainActor
struct SettingsStoreTests {
    @Test func toggleSaves() async {
        let store = SettingsStore()
        store.toggle(.notifications)
        #expect(store.isEnabled(.notifications))
    }
}
```

Inject a fake dependency through the initialiser (not through the SwiftUI environment) in tests. Example fake:

```swift
struct StubFeedService: FeedService {
    var items: [FeedItem]
    func fetchItems() async throws -> [FeedItem] { items }
}
```

## ViewInspector patterns

ViewInspector traverses the SwiftUI view tree without a simulator. Use it to assert structural correctness: which views render, which are hidden, what text strings appear, and whether buttons exist.

```swift
import Testing
import ViewInspector  // nalexn/ViewInspector

@Test func showsEmptyState() throws {
    let view = FeedView(model: FeedViewModel(service: StubFeedService(items: [])))
    let text = try view.inspect().find(text: "No items yet")
    #expect(text.string() == "No items yet")
}
```

Limits: ViewInspector cannot render Liquid Glass materials, Metal-backed views, or platform-native components (sheets driven by UIKit). Prefer snapshot tests for visual regressions.

## swift-snapshot-testing patterns

pointfreeco/swift-snapshot-testing records `.png` (or `.txt` for accessibility) snapshots and diffs on re-run.

```swift
import XCTest               // snapshot-testing uses XCTestCase
import SnapshotTesting
import SwiftUI

final class FeedSnapshotTests: XCTestCase {
    func test_feedView_content() {
        let view = FeedView(model: .fixture_loaded)
        assertSnapshot(of: UIHostingController(rootView: view),
                       as: .image(on: .iPhone16Pro))
    }

    func test_feedView_empty() {
        let view = FeedView(model: .fixture_empty)
        assertSnapshot(of: UIHostingController(rootView: view),
                       as: .image(on: .iPhone16Pro))
    }
}
```

Rules:
- Commit the `__Snapshots__` directory. Review diffs in PR as visual evidence.
- One device size per test is enough for layout changes. Use `.iPhone16Pro` as the baseline device.
- Record mode: set `isRecording = true` or use `withSnapshotTesting(record: .all)` to regenerate, then revert.
- Add snapshot targets to a dedicated scheme so they can be excluded from the normal unit-test run (slow on CI).

## Sparse XCUITest guidelines

XCUITest is slow and flaky. Limit scope to critical user paths that cannot be covered otherwise:

| Scenario | Rationale |
|---|---|
| Onboarding flow (first launch) | Involves system permission dialogs (notifications, Face ID) |
| Accessibility audit (`XCUIApplication().performAccessibilityAudit()`) | Not inspectable via ViewInspector |
| Deep-link / URL-scheme activation | Requires a running app process |

Launch arguments gate feature flags in tests:

```swift
let app = XCUIApplication()
app.launchArguments = ["--uitesting", "--disable-animations"]
app.launch()
```

Run XCUITest in a separate scheme/target from unit tests to keep the fast feedback loop unaffected.

## Test target layout in Package.swift

```swift
.testTarget(
    name: "FeatureXTests",      // Swift Testing unit tests
    dependencies: [
        .target(name: "FeatureXImpl"),
        .product(name: "ViewInspector", package: "ViewInspector"),
    ]
),
.testTarget(
    name: "FeatureXSnapshotTests",  // separate target; slow, snapshot baseline required
    dependencies: [
        .target(name: "FeatureXImpl"),
        .product(name: "SnapshotTesting", package: "swift-snapshot-testing"),
    ]
),
```

Add the snapshot test target to its own Xcode scheme so it runs independently from unit tests.
