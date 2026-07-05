---
name: ios-swiftui-preview
description: >-
  This skill should be used when the user asks to "add SwiftUI previews", "generate
  #Preview macros", "cover all UI states in previews", "add a loading/error/empty
  preview", "preview this view in dark mode", "add Dynamic Type preview variants",
  "make this snapshot-test ready", "my previews don't build", "replace PreviewProvider
  with #Preview", "preview every content state", "add accessibility size variants to
  previews", or "generate previews for each state of this view". Generates #Preview
  macros (iOS 17+) covering a full state matrix (loading / error / empty / content),
  dark mode, and Dynamic Type variants, structured so the same previews can back a
  snapshot test harness without rewrite. Analog of android-compose-preview for SwiftUI.
version: 0.1.0
---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# iOS SwiftUI preview scaffolding

Generate `#Preview` macros that drive every visual state of a SwiftUI view: state
matrix, dark mode, and Dynamic Type variants, structured to back a snapshot harness
without rewrite.

## Step 1: Detect first

Before generating anything, read what exists:

```bash
# Existing previews in the target
grep -rn "#Preview\|PreviewProvider" --include="*.swift" . | head -20

# UI state type (sealed enum / phase struct)
grep -rn "enum.*State\|enum.*Phase\|enum.*UiState" --include="*.swift" . | head -15

# Preview service stubs already present?
grep -rn "Preview.*Service\|stub" --include="*.swift" . | head -10

# Minimum deployment (traits require iOS 17+)
grep "\.iOS" $(find . -name "Package.swift" -not -path "*/.build/*" | head -1) 2>/dev/null
```

Record: minimum deployment target, existing preview coverage, UI state type name,
observation strategy (`@Observable` vs `ObservableObject`), and whether a preview
service stub already exists. Mark anything you cannot determine `unknown`; never
invent state cases.

## Step 2: Enumerate the state matrix

Read the view's state type and list every visually distinct case before writing any
code. Typical matrix: `loading`, `content(data)`, `content(long/boundary data)`,
`empty`, `error(message)`. If the view takes plain parameters with no sealed type,
enumerate the parameter combos that produce distinct visuals.

List the cases back and confirm before generating.
For the full table and copy-paste templates see
[references/ios-swiftui-preview-patterns.md](../../references/ios-swiftui-preview-patterns.md).

## Step 3: Ensure a preview stub exists

Previews must never hit the network, read a database, or construct a ViewModel.
Preview the stateless inner view that accepts state as a parameter, or inject a no-op
stub through the Environment.

If the project uses `@Observable` + Environment DI (the stack default), the
`EnvironmentKey.defaultValue` should already be a `Preview<Feature>Service` stub
(see `ios-module-scaffolder`). If it is missing, add one. Never use `fatalError`
as a default; it crashes every `#Preview` that reads the environment.

See the stub pattern in [references/ios-swiftui-preview-patterns.md](../../references/ios-swiftui-preview-patterns.md).

## Step 4: Write the #Preview macros

One `#Preview` block per state case plus two cross-cutting variants:
- Dark mode (`preferredColorScheme(.dark)`) -- exercises color tokens and adaptive assets.
- Accessibility Dynamic Type (`.environment(\.dynamicTypeSize, .accessibility3)`) --
  surfaces text truncation and layout breaks.

Keep all previews in the same file as the view, name them `"<ViewType> - <State>"`.
Use `traits: .sizeThatFitsLayout` for small self-sizing components (chips, badges,
cells); use the default device frame for full-screen views.

Do NOT multiply variants: each state x each variant is a snapshot to maintain. Dark
mode + one AX size is the default. Add more only when the view has documented a11y
requirements (defer the a11y doctrine to the adlc-design pack).

Abbreviated example (full templates in the reference file):

```swift
#Preview("<Feature>View - Loading") {
    <Feature>View(state: .loading)
        .environment(\.<feature>Service, Preview<Feature>Service())
}

#Preview("<Feature>View - Dark") {
    <Feature>View(state: .content(<Feature>Item(id: "1", title: "Check")))
        .preferredColorScheme(.dark)
        .environment(\.<feature>Service, Preview<Feature>Service())
}

#Preview("<Feature>View - AX Large Text") {
    <Feature>View(state: .content(<Feature>Item(id: "2", title: "AX")))
        .environment(\.dynamicTypeSize, .accessibility3)
        .environment(\.<feature>Service, Preview<Feature>Service())
}
```

## Step 5: Verify (pass/fail, not "looks right")

```bash
# Build the target; a compile error means a broken preview
xcodebuild build \
  -workspace <App>.xcworkspace \
  -scheme <Feature>Impl \
  -destination 'platform=iOS Simulator,name=iPhone 16' | xcbeautify

# Pure SPM package
swift build --package-path Packages/<Feature>
```

A clean build confirms every `#Preview` block compiles. If the Xcode canvas crashes
but the build succeeds, run `Product > Clean Build Folder` and retry; if it still
fails, bisect by commenting out half the previews to isolate the offender.

## Guardrails

- Never construct a `ViewModel` inside a `#Preview`; inject state via parameters or
  Environment stubs.
- Never `fatalError` in any preview-path default.
- If the view reads from a singleton, `@AppStorage`, or `UserDefaults` directly,
  that is a design smell: report it and stop rather than working around it in the preview.
- Snapshot harness integration is a separate step; report missing wiring and stop
  rather than adding dependencies unilaterally.

## Outbound checkpoint

Local work needs no approval. Anything outbound (publish, push, post) needs an explicit per-action "yes"; see the global consent law.

## References

- [references/ios-swiftui-preview-patterns.md](../../references/ios-swiftui-preview-patterns.md) -- full state
  matrix table, copy-paste templates, traits pattern, Dynamic Type sizes reference
  (created alongside this skill).
- Apple, `#Preview(_:body:)` macro:
  https://developer.apple.com/documentation/swiftui/preview(_:body:)
- Apple, `#Preview(_:traits:body:)` with `PreviewTrait`:
  https://developer.apple.com/documentation/swiftui/preview(_:traits:body:cameras:)
- Apple, Previews in Xcode (canonical guide):
  https://developer.apple.com/documentation/swiftui/previews-in-xcode
