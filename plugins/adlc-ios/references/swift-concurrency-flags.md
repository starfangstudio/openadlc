<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
# Swift Concurrency Migration Flags

Reference for the `ios-concurrency-audit` skill. Covers Package.swift settings, detection
commands, and fix patterns for Swift 6 / 6.2 strict concurrency.

---

## 1. Detect current language mode

```bash
# Check swift-tools-version and any swiftLanguageMode settings
grep -rn "swift-tools-version\|swiftLanguageMode\|strictConcurrency\|StrictConcurrency\
\|SWIFT_STRICT_CONCURRENCY\|SWIFT_VERSION" \
  --include="Package.swift" --include="*.xcconfig" --include="project.pbxproj" . | head -40

# Show compiler flags from xcodebuild (reveals implicit -strict-concurrency)
xcodebuild build -workspace <W>.xcworkspace -scheme <S> \
  -destination "generic/platform=iOS" \
  OTHER_SWIFT_FLAGS="-v" 2>&1 | grep -E "strict-concurrency|language-mode|enable-upcoming"

# Count live @unchecked Sendable and nonisolated(unsafe) markers
grep -rn "@unchecked Sendable\|nonisolated(unsafe)" --include="*.swift" . | wc -l
grep -rn "@unchecked Sendable\|nonisolated(unsafe)" --include="*.swift" . | head -30
```

---

## 2. Package.swift SwiftSettings reference

### Set language mode per target (safe staged migration)

```swift
// swift-tools-version: 6.0   ← tools version does NOT force language mode
.target(
    name: "FeatureXInterface",
    swiftSettings: [
        .swiftLanguageMode(.v6)   // opt this target in to Swift 6 strict checking
    ]
),
.target(
    name: "FeatureXImpl",
    swiftSettings: [
        .swiftLanguageMode(.v5)   // keep on v5 until ready; no enforcement yet
    ]
)
```

To keep a whole package at tools-version 6 but stay on v5 language mode, omit
`swiftLanguageMode` or set it to `.v5` on each target.

### Enable specific Swift 6.2 approachable-concurrency upcoming features

```swift
.target(
    name: "FeatureXImpl",
    swiftSettings: [
        .swiftLanguageMode(.v6),
        // Approachable concurrency (Swift 6.2+, SE-0461/0463/0466/0470)
        .enableUpcomingFeature("NonisolatedNonsendingByDefault"),  // SE-0461
        .enableUpcomingFeature("InferSendableFromCaptures"),       // SE-0462
        .enableUpcomingFeature("GlobalActorIsolatedTypesUsability"),
        .enableUpcomingFeature("InferIsolatedConformances"),
    ]
)
```

### Default MainActor isolation for a module (SE-0466, Swift 6.2+)

```swift
.target(
    name: "UIFeatureImpl",
    swiftSettings: [
        .swiftLanguageMode(.v6),
        .defaultIsolation(MainActor.self)   // whole module defaults to @MainActor
    ]
)
```

Use only on targets that are purely UI-bound. Service/data targets must NOT use this.

---

## 3. Xcode project (non-SPM targets)

In Build Settings, set per-target:

| Setting | Value |
|---|---|
| `SWIFT_VERSION` | `6.0` (or `5.0` for staged rollout) |
| `SWIFT_STRICT_CONCURRENCY` | `complete` (was `minimal` / `targeted`) |

Under Xcode 16+, `SWIFT_STRICT_CONCURRENCY = complete` is equivalent to Swift 6 mode for
concurrency checks even when `SWIFT_VERSION = 5`.

---

## 4. Suppression patterns: when to use and when to eliminate

| Pattern | When legitimate | Replace with |
|---|---|---|
| `@unchecked Sendable` | Wrapping a C/ObjC type you cannot change | A `@MainActor`-isolated wrapper or an actor |
| `nonisolated(unsafe)` | A stored property that is provably write-once before concurrency starts | Constant (`let`) or actor-isolated property |
| `@Sendable` closure captures | Need to pass a closure off-actor | Make captured value `Sendable` or copy value type |

Zero tolerance for `@unchecked Sendable` on types you own. Every occurrence is a bug to
fix, not to suppress.

---

## 5. Common error patterns and fixes

### Actor isolation violation on @Observable view model

```swift
// Error: main actor-isolated property accessed from non-isolated context
@Observable final class FeedViewModel {   // missing @MainActor
    var items: [Item] = []
}

// Fix:
@Observable @MainActor final class FeedViewModel {
    var items: [Item] = []
}
```

### Sendable violation crossing actor boundary

```swift
// Error: type 'SearchResult' does not conform to 'Sendable'
struct SearchResult { var title: String; var image: UIImage }

// Fix: make Sendable (value types are fine; UIImage needs care)
struct SearchResult: Sendable { var title: String; var imageData: Data }
```

### Task.detached with implicit captures

```swift
// Avoid: captures self without isolation guarantee
Task.detached { await self.load() }

// Fix: structured Task, inherit actor context
Task { await self.load() }
```

### nonisolated async (pre-6.2 behavior)

```swift
// Pre-6.2: nonisolated async runs on cooperative thread pool
// 6.2 + NonisolatedNonsendingByDefault: runs in caller's context

nonisolated func fetchData() async -> [Item] { ... }
// With SE-0461 enabled, this inherits the caller's actor context.
// If you need explicit off-actor execution, mark it @concurrent.
```

---

## 6. Migration order (leaf-first)

1. Interface targets (no dependencies, pure protocols/structs -- easiest).
2. Data/service Impl targets (actors, async APIs).
3. UI Impl targets (add `@MainActor` or `defaultIsolation(MainActor.self)`).
4. App target (wires everything; fix any remaining isolation gaps).
5. Test targets last (they import Impl targets, so fix after Impl is clean).

---

## Sources

- Swift 6.2 release: https://www.swift.org/blog/swift-6.2-released/
- SE-0461, NonisolatedNonsendingByDefault: https://github.com/apple/swift-evolution/blob/main/proposals/0461-nonisolated-nonsending-by-default.md
- SE-0466, Default isolation: https://github.com/apple/swift-evolution/blob/main/proposals/0466-control-default-actor-isolation.md
- Approachable Concurrency guide (avanderlee): https://www.avanderlee.com/concurrency/approachable-concurrency-in-swift-6-2-a-clear-guide/
- Swift 6 migration (avanderlee): https://www.avanderlee.com/concurrency/swift-6-migrating-xcode-projects-packages/
- Per-target swiftLanguageMode (Donny Wals): https://www.donnywals.com/setting-the-swift-language-mode-for-an-spm-package/
