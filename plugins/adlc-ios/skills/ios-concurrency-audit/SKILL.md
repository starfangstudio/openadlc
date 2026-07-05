---
name: ios-concurrency-audit
description: >-
  This skill should be used when the user asks to "audit Swift concurrency", "fix
  Swift 6 data race errors", "enable strict concurrency", "migrate to Swift 6 language
  mode", "eliminate @unchecked Sendable", "remove nonisolated(unsafe)", "add @MainActor",
  "fix Sendable conformance", "enable approachable concurrency", "set default MainActor
  isolation", "turn on NonisolatedNonsendingByDefault", "migrate a package to Swift 6",
  "fix actor isolation violations", "kill data race warnings", or "enable strict
  concurrency per target in Package.swift". Detects the current Swift language mode and
  concurrency flags, audits actor isolation, Sendable conformance, and suppression
  markers (@unchecked Sendable / nonisolated(unsafe)), applies staged per-target
  enablement via Package.swift SwiftSettings, and verifies a clean build under the
  stricter setting. Covers Swift 6.2 approachable concurrency (SE-0461/0466,
  NonisolatedNonsendingByDefault, defaultIsolation).
version: 0.1.0
---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# iOS concurrency audit

Audit and fix Swift strict concurrency in a SwiftUI/SPM project. Migrate targets to
Swift 6 language mode one at a time, leaf-first. Never force full strict mode on the
entire project in one shot.

## Step 1: Detect first

Run from the repo root. Record everything; mark anything not found `unknown`.

```bash
# Language mode, tools version, existing SwiftSettings flags
grep -rn "swift-tools-version\|swiftLanguageMode\|strictConcurrency\
\|SWIFT_STRICT_CONCURRENCY\|SWIFT_VERSION\|defaultIsolation\|enableUpcomingFeature" \
  --include="Package.swift" --include="*.xcconfig" . | head -40

# Count suppressions -- every hit is a candidate to fix
grep -rn "@unchecked Sendable\|nonisolated(unsafe)" --include="*.swift" . | head -30

# Surface concurrency diagnostics in the current build
xcodebuild build \
  -workspace <W>.xcworkspace -scheme <S> \
  -destination "generic/platform=iOS" 2>&1 \
  | grep -E "actor.isolated|Sendable|data.race|nonisolated" | head -50
```

Record: tools version, language mode per target (v5 / v6 / unset), suppression count,
and whether any target already carries `swiftLanguageMode(.v6)` or `defaultIsolation`.

## Step 2: Plan migration order

Use leaf-first order: Interface targets -> service/data Impl -> UI Impl -> App target ->
Test targets. For exact Package.swift flag syntax, suppression fix patterns, and Xcode
Build Settings, see: [references/swift-concurrency-flags.md](../../references/swift-concurrency-flags.md).

## Step 3: Enable per target

Set `swiftLanguageMode` in each target's `swiftSettings` in Package.swift:

```swift
.target(name: "FeatureXInterface", swiftSettings: [.swiftLanguageMode(.v6)])
.target(name: "FeatureXImpl",      swiftSettings: [.swiftLanguageMode(.v5)]) // not ready yet
```

Tools-version 6.0 does NOT auto-enable v6 language mode; set it explicitly per target.

For Swift 6.2 approachable concurrency on a v6 target, add upcoming features:

```swift
.enableUpcomingFeature("NonisolatedNonsendingByDefault"),  // SE-0461
.enableUpcomingFeature("InferSendableFromCaptures"),
.enableUpcomingFeature("GlobalActorIsolatedTypesUsability"),
```

For UI-only Impl targets, add `defaultIsolation(MainActor.self)` (SE-0466) so the whole
module defaults to `@MainActor` without per-type annotation. Never apply to Interface
or service targets.

## Step 4: Fix violations

Prioritized fixes (full patterns in the reference file):

- `@Observable` view models: add `@MainActor`.
- Non-`Sendable` value types crossing actor boundaries: add `: Sendable`.
- Shared mutable state off main thread: wrap in an `actor`.
- `@unchecked Sendable` on types you own: replace with a proper actor or `@MainActor`
  wrapper. Zero tolerance on owned types; only suppress at C/ObjC boundaries you cannot
  change.
- `nonisolated(unsafe)`: replace with `let` or move the property into an actor.
- `Task.detached`: replace with structured `Task { }` to inherit actor context.
- Third-party imports emitting Sendable noise: use `@preconcurrency import`, not your
  own type suppression.
- KMP-generated non-Sendable types: wrap in a `@MainActor`-isolated Swift struct rather
  than marking the KMP type `@unchecked`.

## Step 5: Verify -- pass/fail, not "looks right"

After each target migration:

```bash
# SPM target
swift build --package-path Packages/<Feature>

# Xcode target -- confirm zero concurrency diagnostics
set -o pipefail && xcodebuild build \
  -workspace <W>.xcworkspace -scheme <S> \
  -destination "generic/platform=iOS" 2>&1 | xcbeautify

xcodebuild build -workspace <W>.xcworkspace -scheme <S> \
  -destination "generic/platform=iOS" 2>&1 \
  | grep -cE "actor.isolated|Sendable|data.race|nonisolated" || echo "0 violations"
```

A clean build with zero concurrency diagnostics on the target is the only acceptance
criterion.

## Outbound checkpoint

Local work needs no approval. Anything outbound (publish, push, post) needs an explicit per-action "yes"; see the global consent law.

## References

- [references/swift-concurrency-flags.md](../../references/swift-concurrency-flags.md) -- full Package.swift
  flag reference, suppression patterns, Xcode Build Settings, migration order, and
  concrete error/fix examples (created alongside this skill).
- Swift 6.2 release notes: https://www.swift.org/blog/swift-6.2-released/
- SE-0461, NonisolatedNonsendingByDefault: https://github.com/apple/swift-evolution/blob/main/proposals/0461-nonisolated-nonsending-by-default.md
- SE-0466, Default actor isolation: https://github.com/apple/swift-evolution/blob/main/proposals/0466-control-default-actor-isolation.md
- Swift 6 migration guide (avanderlee): https://www.avanderlee.com/concurrency/swift-6-migrating-xcode-projects-packages/
- Per-target swiftLanguageMode (Donny Wals): https://www.donnywals.com/setting-the-swift-language-mode-for-an-spm-package/
- Apple, Swift concurrency: https://docs.swift.org/swift-book/documentation/the-swift-programming-language/concurrency/
