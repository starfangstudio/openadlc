---
name: ios-shared-views
description: >-
  This skill should be used when the user asks to "extract a reusable SwiftUI view",
  "pull this UI into a shared component", "deduplicate SwiftUI views", "add a
  @ViewBuilder slot to this view", "this view takes too many parameters", "make a
  design-system component in SwiftUI", "promote this UI to the shared design-system
  target", "refactor copy-pasted SwiftUI", "create a slot-based SwiftUI view", or
  "add a #Preview for this component". Extracts duplicated SwiftUI UI into a
  stateless, slot-based view with a @ViewBuilder API, design-system tokens,
  accessibility traits, and a #Preview. Applies rule-of-three: promote on the
  2nd occurrence when it is the same knowledge, 3rd for merely look-alike shapes.
version: 0.1.0
---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# iOS shared views

Extract duplicated SwiftUI UI into a reusable, stateless, slot-based view.
Apply when the same visual shape appears in 2+ places, or one view conflates
layout with business logic.

## Step 1: Detect first

Run these before touching any code. Record: shared UI target path, token names,
preview convention, accessibility patterns, deployment target. Mark anything
not found `unknown`; never invent a package or token name.

```bash
# Shared/design-system targets
find . -type d \( -name "DesignSystem*" -o -name "SharedUI*" -o -name "CommonUI*" \) \
  -not -path "*/build/*" | head -20

# Token types in use
grep -rEln "Color\.|Font\.|spacing|Padding|Radius" \
  --include="*.swift" . | grep -i "token\|theme\|style" | head -10

# Preview convention (#Preview macro vs PreviewProvider)
grep -rn "#Preview\|PreviewProvider" --include="*.swift" . | head -10
```

## Step 2: Decide whether to extract (rule-of-three)

- Same knowledge in 2+ places: extract on the second occurrence.
- Merely look-alike UI (same shape, different semantics): wait for the third.
- Single use "for later": do NOT extract. Premature components ossify bad APIs.
- Structural variants needing a flag: split into named views (`PrimaryCard`,
  `OutlinedCard`) instead of one view with a `style` enum.

## Step 3: Design the API

Parameter order: required data, required callbacks, optional params (defaulted),
then trailing `@ViewBuilder content` slot.

```swift
struct SectionCard<Content: View>: View {
    let title: String                        // required data
    var onTap: (() -> Void)? = nil          // optional callback
    @ViewBuilder var content: () -> Content  // trailing slot

    var body: some View { ... }
}
```

- Apply any caller-supplied modifier to the outermost container only, never an
  inner node.
- Never capture a ViewModel, router, or domain model. Accept plain data +
  callbacks only (state down, events up).
- Multiple slots: use descriptive names (`leading`, `trailing`, `header`,
  `actions`) with `= { EmptyView() }` defaults for optional slots. Full
  multi-slot naming conventions in
  [references/ios-shared-views-detail.md](../../references/ios-shared-views-detail.md).

## Step 4: Use design-system tokens, not literals

Import only the `DesignSystemInterface` (or equivalent) target. Replace every
hardcoded color, spacing, typography, and radius value with named tokens:

```swift
import DesignSystemInterface

VStack(spacing: DesignTokens.Spacing.md) { ... }
    .padding(DesignTokens.Spacing.md)
    .background(DesignTokens.Color.surfaceDefault)
    .clipShape(RoundedRectangle(cornerRadius: DesignTokens.Radius.card))
```

If the project has no token target yet, mark values `unknown` and invoke the
`adlc-design` design-tokens skill before writing any literal into the component.

## Step 5: Add accessibility traits

Every shared view must declare its role and expose a label at the outermost
container. Match the pattern from Step 1:

```swift
.accessibilityElement(children: .combine)
.accessibilityLabel(title)
.accessibilityAddTraits(.isButton)  // only if the view is interactive
```

For purely decorative containers, use `.accessibilityHidden(true)` and annotate
the reason inline. Bad defaults on a shared view multiply across every call site.
Full a11y doctrine lives in the `adlc-design` design-a11y skill; defer there.

## Step 6: Add a #Preview

One preview per meaningful state variant. Use `#Preview` if iOS 17+; else
`PreviewProvider`. Match the convention discovered in Step 1. Never use
`fatalError` in a preview environment value default (it crashes the canvas; use
a no-op stub instead).

```swift
#Preview("Default") {
    SectionCard(title: "Section title") { Text("Slot content") }
        .padding()
}

#Preview("Empty slot") {
    SectionCard(title: "Empty") { EmptyView() }.padding()
}
```

## Step 7: Place the component in the right target

- 1 feature only: keep it in that feature's `*Impl` target as `internal`.
- 2+ features: move to the shared design-system or common-UI target and import
  its public interface. Never copy the view across impl targets.

## Step 8: Verify (pass/fail)

```bash
# Build the target containing the new view
swift build --package-path Packages/<TargetPackage>

# Confirm all former call sites build (full app)
xcodebuild build -workspace <App>.xcworkspace -scheme <AppScheme> \
  -destination 'platform=iOS Simulator,name=iPhone 16' | xcbeautify

# No remaining duplicated copies
grep -rn "<OriginalViewName>" --include="*.swift" . | grep -v "SharedUI\|DesignSystem"
```

Green build + all previews rendering = done. Fix any failing call site before
marking the extraction complete.

## Anti-patterns to flag

- `@State` or `@Observable` model owned inside a shared view (breaks hoisting).
- Hardcoded `Color(hex:)`, `.padding(16)`, raw spacing literals instead of tokens.
- A `variant: Style` enum switching structural branches -- split into named views.
- Missing `#Preview` or a preview that requires a real network or database.
- Accessibility modifier absent from the outermost container.
- Impl-to-impl import: feature A's impl imports feature B's view directly instead
  of going through the shared design-system interface target.

## Outbound checkpoint

Local work needs no approval. Anything outbound (publish, push, post) needs an explicit per-action "yes"; see the global consent law.

## References

- Apple, ViewBuilder: https://developer.apple.com/documentation/swiftui/viewbuilder
- Apple, accessibilityElement(children:): https://developer.apple.com/documentation/swiftui/view/accessibilityelement(children:)
- Apple, AccessibilityTraits: https://developer.apple.com/documentation/swiftui/accessibilitytraits
- Apple, #Preview macro: https://developer.apple.com/documentation/swiftui/preview(_:traits:body:cameras:)
- Apple, Accessibility modifiers: https://developer.apple.com/documentation/swiftui/view-accessibility
- `adlc-design` pack -- design-tokens skill (token doctrine) and design-a11y skill (a11y doctrine): defer there
- [references/ios-architecture.md](../../references/ios-architecture.md) -- SPM interface/impl split, access levels, DesignSystem target placement
- [references/ios-shared-views-detail.md](../../references/ios-shared-views-detail.md) -- multi-slot naming conventions, exhaustive edge cases
