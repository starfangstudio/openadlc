---
name: ios-testing
description: >-
  This skill should be used when the user asks to "add a test for this iOS feature",
  "write a Swift test", "set up Swift Testing", "test an @Observable store", "unit test
  a view-model", "test with #expect or #require", "add parameterized tests", "set up
  ViewInspector for SwiftUI view tests", "add snapshot tests", "add swift-snapshot-testing",
  "write an XCUITest", "run the iOS tests", "add a test target to a Swift package", or
  "what testing libraries should I use for iOS". Implements the iOS test pyramid: Swift
  Testing (@Test/@Suite/#expect/#require, parameterized, parallel) for unit tests of
  @Observable stores/logic; ViewInspector for view-tree unit tests; swift-snapshot-testing
  for visual regression; sparse XCUITest for E2E paths requiring a live process. Wraps
  the adlc-testing strategy and specializes execution for the SwiftUI + @Observable stack.
version: 0.1.0
---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# iOS testing

Layer tests pyramid-style: many fast unit tests (Swift Testing) at the base, a thin layer
of view-tree and snapshot tests in the middle, and a few targeted XCUITest E2E flows at
the top. Bias toward depth over breadth: test behavior and real edge cases, not framework
internals.

## Step 1: Detect first

Run from the repo root before writing or modifying any test:

```bash
# Which test framework is in use?
grep -rEl "import Testing|import XCTest" --include="*.swift" . | head -20

# Existing test targets
find . -name "Package.swift" -not -path "*/build/*" \
  -exec grep -l "testTarget" {} \;

# Third-party test dependencies already present
grep -Ei "ViewInspector|SnapshotTesting|swift-snapshot-testing" \
  $(find . -name "Package.swift" -not -path "*/build/*") 2>/dev/null

# Minimum iOS deployment (affects Swift Testing availability: iOS 16+)
grep -E "\.iOS\(" $(find . -name "Package.swift" -not -path "*/build/*") | head -5
```

Record: framework in use (Swift Testing / XCTest / mixed), which test libraries are
already depended upon, and the iOS deployment target. Mark anything not found `unknown`.
Never introduce a new dependency without checking it is not already present.

## Step 2: Unit-test @Observable stores with Swift Testing

Default to Swift Testing for all new unit tests (Xcode 16+, iOS 16+ minimum). See
[references/ios-testing.md](../../references/ios-testing.md) for full syntax, @MainActor patterns,
fake-construction, and serialized suites.

Quick shape:

```swift
import Testing

@Suite @MainActor
struct FeatureStoreTests {
    @Test func loadsOnAppear() async {
        let store = FeatureStore(service: StubFeatureService(items: .fixture))
        await store.load()
        #expect(store.items.count > 0)
        #expect(store.isLoading == false)
    }

    @Test("Rejects invalid inputs", arguments: ["", " ", String(repeating: "x", count: 300)])
    func rejectsInvalidInput(input: String) {
        #expect(!FeatureStore.isValidInput(input))
    }
}
```

Rules: inject fakes through the initializer, not the SwiftUI environment. Keep test types
as structs. Use `#require` to stop on nil before asserting further.

## Step 3: View-tree unit tests with ViewInspector

Use ViewInspector (nalexn/ViewInspector) to assert structural correctness of SwiftUI views
without a simulator: which views render, what text appears, button existence. Add to the
test target: `.package(url: "https://github.com/nalexn/ViewInspector", from: "0.10.0")`.
See [references/ios-testing.md](../../references/ios-testing.md) for patterns and known limits
(no Liquid Glass materials, no Metal-backed views, no system sheets).

## Step 4: Visual regression with swift-snapshot-testing

Use pointfreeco/swift-snapshot-testing for per-UI-state image snapshots. Keep snapshot
tests in a separate `<Feature>SnapshotTests` target and scheme so they do not slow the
unit-test loop. Commit `__Snapshots__`; review diffs as visual evidence in PR. Add:
`.package(url: "https://github.com/pointfreeco/swift-snapshot-testing", from: "1.17.0")`.
See [references/ios-testing.md](../../references/ios-testing.md) for device config and record mode.

## Step 5: Sparse XCUITest for E2E paths

Restrict XCUITest to paths that require a live app process: onboarding + system permission
dialogs, accessibility audits (`XCUIApplication().performAccessibilityAudit()`), and
deep-link activation. Everything else belongs in unit or snapshot tests.

Gate feature flags with launch arguments:

```swift
app.launchArguments = ["--uitesting", "--disable-animations"]
```

Run XCUITest in a dedicated scheme separate from unit tests.

## Step 6: Verify (pass/fail)

```bash
# SPM package unit tests
swift test --package-path Packages/<Feature>

# xcodebuild unit tests (workspace)
set -o pipefail && xcodebuild test \
  -workspace <W>.xcworkspace \
  -scheme <FeatureTests> \
  -destination "platform=iOS Simulator,name=iPhone 16,OS=latest" | xcbeautify

# Run only one suite or test method
swift test --filter "FeatureStoreTests/loadsOnAppear"
# or with xcodebuild:
# -only-testing:<T>/FeatureStoreTests/loadsOnAppear
```

A green run is the proof. Never mark done on a red suite unless the failure is pre-existing and tracked.

## What to test

Test state transitions, mappers, and service boundaries. Do not test SwiftUI layout math,
framework internals, or impossible states. Prefer fakes over mocks; avoid third-party mock
libraries unless already in the project.

## Outbound checkpoint

Local work needs no approval. Anything outbound (publish, push, post) needs an explicit per-action "yes"; see the global consent law.

## References

- [references/ios-testing.md](../../references/ios-testing.md) -- Swift Testing syntax, @Observable
  store pattern, ViewInspector patterns, snapshot-testing patterns, test target layout
  (created alongside this skill).
- Apple, Swift Testing documentation: https://developer.apple.com/xcode/swift-testing/
- swift-testing open source (swiftlang/swift-testing): https://github.com/swiftlang/swift-testing
- ViewInspector (nalexn/ViewInspector): https://github.com/nalexn/ViewInspector
- swift-snapshot-testing (pointfreeco/swift-snapshot-testing): https://github.com/pointfreeco/swift-snapshot-testing
- adlc-testing strategy (test pyramid, what-to-test doctrine): load the adlc-testing pack.
