---
name: ios-module-scaffolder
description: >-
  Scaffolds a two-target SPM local package (public Interface target + package-internal
  Impl target) wired into the app target and the Environment DI graph. Use when the
  user asks to "scaffold a new iOS feature module", "create an SPM interface/impl
  target pair", "add a new feature package wired for DI", "bootstrap a new iOS module",
  or "wire a new SPM target into the app".
version: 0.1.0
---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# iOS module scaffolder

Scaffold a new feature as an SPM local package with a `<Feature>Interface` target
(public protocols, models, route enum) and a `<Feature>Impl` target (concrete types,
views, @Observable view-models), wired into the app target and the Environment DI
graph. Features communicate through the Interface target only -- never through the Impl.

## Step 1: Detect conventions before generating anything

Never assume the workspace layout. Inspect first:

```bash
# Where do local packages live?
find . -name "Package.swift" -not -path "*/build/*" -not -path "*/.build/*" | head -20

# What is the workspace structure? (xcworkspace or root Package.swift)
find . \( -name "*.xcworkspace" -o -name "*.xcodeproj" \) \
  -not -path "*/build/*" | head -10

# How are local packages referenced from the app target?
grep -rn "\.package(path:" --include="Package.swift" . | head -20

# Naming convention for existing feature packages
ls -d */Packages/*/  2>/dev/null | head -20
find . -name "Package.swift" -not -path "*/build/*" -exec dirname {} \; | head -20

# DI approach: Environment keys, EnvironmentObject, Factory, manual
grep -rEln "@EnvironmentObject|@Environment\(\\\\|EnvironmentKey|EnvironmentValues" \
  --include="*.swift" . | head -10

# Observable strategy
grep -rEln "@Observable|ObservableObject|@Published" \
  --include="*.swift" . | head -10

# Navigation strategy
grep -rEln "NavigationStack|NavigationPath|navigationDestination" \
  --include="*.swift" . | head -10

# Swift tools version in use
grep "swift-tools-version" $(find . -name "Package.swift" \
  -not -path "*/build/*" | head -1) 2>/dev/null
```

Record: package directory convention (`Packages/<Feature>/`), tools version, minimum
iOS deployment, DI approach, observation strategy, navigation owner (App / Coordinator).
Mark anything you cannot determine `unknown` and ask; never invent path conventions or
EnvironmentKey names.

## Step 2: Generate the Interface target (public contracts only)

The Interface target holds protocols, models, route enum, and the EnvironmentKey. No
concrete types, no SwiftUI views, no UI framework imports beyond what models need.

For the source file templates (`<Feature>Service.swift`, `<Feature>Route.swift`,
`<Feature>EnvironmentKey.swift`), see
[references/ios-module-scaffolder-detail.md](../../references/ios-module-scaffolder-detail.md) (Interface target section).

## Step 3: Generate the Impl target (concrete types + views)

Concrete types default to `internal`. Use `package` access only for types that must
cross a target boundary inside this package; do NOT promote them to `public`.

For the source file templates (`Real<Feature>Service.swift`, `<Feature>View.swift`,
`<Feature>ViewModel.swift`), see
[references/ios-module-scaffolder-detail.md](../../references/ios-module-scaffolder-detail.md) (Impl target section).

## Step 4: Write Package.swift

For the full manifest template (targets, products, dependency stubs), see
[references/ios-module-scaffolder-detail.md](../../references/ios-module-scaffolder-detail.md) (Package.swift section).

Key invariants:
- Interface is a public `.library` product; Impl is NOT exported as a product.
- Impl's target dependencies list Interface and other features' Interface products only, never their Impl.
- Match the detected `swift-tools-version` and minimum iOS deployment target.

## Step 5: Wire into the app target and DI graph

For the full wiring snippets (root Package.swift entry, `.navigationDestination`, `@main` App injection), see
[references/ios-module-scaffolder-detail.md](../../references/ios-module-scaffolder-detail.md) (Wiring section).

Key rule: the app target is the only target that imports `<Feature>Impl`. Feature targets
that navigate to `<Feature>` import `<Feature>Interface` only, push a `<Feature>Route`
value, and let the app's `.navigationDestination` resolve it.

## Step 6: Verify (pass/fail, not "looks right")

For the exact `swift build` and `xcodebuild` commands, see
[references/ios-module-scaffolder-detail.md](../../references/ios-module-scaffolder-detail.md) (Verify commands section).

A clean build proves the targets compile, `package` access level is respected (no
"cannot access" errors across targets), and the DI wiring resolves. Fix any missing
EnvironmentKey default or `Sendable` violation before claiming done.

## Guardrails

- Impl-to-Impl dependency is forbidden. If two features interact, one exposes a
  protocol in its Interface target; the other injects it via the environment.
- Never use `public` for types that only need to cross a target boundary inside the
  same package -- use `package` (Swift 5.9+, SE-0386).
- Never `fatalError` in an EnvironmentKey default; it crashes SwiftUI Previews. Use
  a no-op preview stub instead.
- No business logic in SwiftUI View structs. No `Task.detached`. No `GlobalScope`
  equivalent (`Task { ... }` at call site, not in init).
- KMP shared core: if a shared domain layer already exists, wrap it with a thin Swift
  adapter in the Impl target. Do not rewrite logic that lives in the KMP module.

## Outbound checkpoint

Local work needs no approval. Anything outbound (publish, push, post) needs an explicit per-action "yes"; see the global consent law.

## References

- [references/ios-module-scaffolder-detail.md](../../references/ios-module-scaffolder-detail.md) -- full source
  file templates, Package.swift manifest, wiring snippets, and verify commands.
- [references/ios-architecture.md](../../references/ios-architecture.md) -- SPM interface/impl split,
  `package` access level, @Observable, Environment DI, NavigationStack, Swift 6
  concurrency isolation (created alongside this skill).
- Swift Evolution SE-0386, "Package Access Modifier" (Swift 5.9):
  https://github.com/apple/swift-evolution/blob/main/proposals/0386-package-access-modifier.md
- Apple, SPM PackageDescription reference:
  https://docs.swift.org/package-manager/PackageDescription/PackageDescription.html
- Apple, "Migrating from ObservableObject to the Observable macro":
  https://developer.apple.com/documentation/swiftui/migrating-from-the-observable-object-protocol-to-the-observable-macro
- Apple, SwiftUI NavigationStack:
  https://developer.apple.com/documentation/swiftui/navigationstack
