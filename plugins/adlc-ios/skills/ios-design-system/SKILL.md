---
name: ios-design-system
description: >-
  This skill should be used when the user asks to "build a SwiftUI design system", "wire
  design tokens into iOS", "consume the token pipeline output in SwiftUI", "create semantic
  color tokens for iOS", "set up Dynamic Type with design tokens", "add dark mode support
  using Asset Catalog", "implement @ScaledMetric spacing from tokens", "add a DS component",
  "replace raw Color() with token colors", "replace hard-coded padding with token spacing",
  "apply Liquid Glass to a SwiftUI view", "add glassEffect to a card", "gate glassEffect
  for iOS 26", "set up a GlassEffectContainer", "create a ds-glass wrapper", "build a
  token-based text style extension", "map Style Dictionary output to SwiftUI", or "set up
  DesignSystemInterface and DesignSystemImpl SPM targets". Builds or extends a token-based
  SwiftUI design system that consumes adlc-design token pipeline output (Style Dictionary
  ios-swift build), covering semantic colors (Asset Catalog any/dark), Dynamic Type text
  styles, @ScaledMetric spacing, reusable DS components, and Liquid Glass (iOS 26
  .glassEffect() gated with ultraThinMaterial fallback).
version: 0.1.0
---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# iOS design system

Consume the adlc-design token pipeline output and produce a token-based SwiftUI design
system: semantic colors, Dynamic Type text styles, `@ScaledMetric` spacing, and Liquid
Glass components. Defer a11y doctrine to adlc-design `design-a11y`; test strategy to
adlc-testing. This skill owns the iOS consumption layer only.

## Step 1: Detect first

Never create before inspecting:

```bash
# Token build output present?
find . -path "*/build/ios/*/DesignTokens.swift" | head -5
find . -name "DesignTokens.swift" -not -path "*/build/*" | head -5

# Existing DS SPM targets
find . -name "Package.swift" -not -path "*/build/*" | \
  xargs grep -l "DesignSystem" 2>/dev/null | head -5

# Raw-value violations
grep -rEn 'Color\(red:|\.padding\([0-9]|Font\.system\(size:' \
  --include="*.swift" . | grep -v build/ | grep -v test | head -20
```

Record: token build path, DS targets present, raw violations. Mark anything undetermined
`unknown`; ask before inventing names. If the token build is absent, run adlc-design
`design-tokens` first (`node style-dictionary.config.mjs`), then re-detect.

## Step 2: SPM targets

Create `Packages/DesignSystem/` with two targets:
- `DesignSystemInterface` -- `DSTokens` namespace, `View+Glass.swift`, color/type/spacing
  extensions, `EnvironmentKey` stubs. All `public`. Feature targets import this only.
- `DesignSystemImpl` -- concrete DS components (`DSPrimaryButton`, `GlassCard`, etc.),
  Assets.xcassets. The app target imports this for DI wiring.

Full `Package.swift` skeleton: [references/ios-design-system-templates.md](references/ios-design-system-templates.md).

## Step 3: Wire token output into DSTokens

Map the Style Dictionary `DesignTokens.swift` output into a typed `DSTokens` namespace.
Never hard-code values; every property aliases the generated output. For each semantic color,
add an Asset Catalog entry (Any, Dark); never branch on `colorScheme` for semantic colors.
For the color extension snippet and Asset Catalog steps, see
[references/ios-design-system-detail.md](references/ios-design-system-detail.md).
Full scaffolds: [references/ios-design-system-templates.md](references/ios-design-system-templates.md).

## Step 4: Dynamic Type text styles + @ScaledMetric spacing

Use `Font.system(_ style:)` (or `Font.custom(_:size:relativeTo:)` for brand fonts) so
text scales automatically. Use `@ScaledMetric(relativeTo:)` for spacing; always supply
`relativeTo:`. Raw numeric literals in DS `.padding()` calls are violations; fail them
in verify. Spacing extension snippet:
[references/ios-design-system-detail.md](references/ios-design-system-detail.md).

## Step 5: DS components (no raw controls where a DS component exists)

Each DS component lives in `DesignSystemImpl` and reads exclusively from `DSTokens.*`.
Rule: no raw `Color(...)`, no numeric `.padding(N)`, no `Font.system(size:)` inside
a DS component. Usage pattern and full component templates:
[references/ios-design-system-detail.md](references/ios-design-system-detail.md) and
[references/ios-design-system-templates.md](references/ios-design-system-templates.md).

## Step 6: Liquid Glass (iOS 26 gate required)

Never call `.glassEffect()` directly at feature call sites. Wrap it in a `DSGlassModifier`
that gates on `#available(iOS 26, *)` and falls back to `.ultraThinMaterial`. Use
`GlassEffectContainer` only when sibling glass elements must morph together. Do not apply
glass to content-heavy surfaces. Full modifier implementation, `.glassEffectID`, and
fallback matrix: [references/ios-design-system-detail.md](references/ios-design-system-detail.md) and
[references/ios-liquid-glass.md](references/ios-liquid-glass.md).

## Step 7: Verify (pass/fail)

```bash
swift build --package-path Packages/DesignSystem  # must succeed

grep -rEn 'Color\(red:|\.padding\([0-9]|Font\.system\(size:' \
  --include="*.swift" . | grep -v build/ | grep -v DesignSystem | grep -v test
# Zero matches = clean. Any match = missing token reference.
```

Toggle Appearance in iOS Simulator Settings to confirm dark mode. Do not claim done
without a clean build and empty violation grep.

## Outbound checkpoint

Local work needs no approval. Anything outbound (publish, push, post) needs an explicit per-action "yes"; see the global consent law.

## References

- [references/ios-design-system-detail.md](references/ios-design-system-detail.md) -- code snippets for
  DSTokens color/spacing extensions, DS component usage pattern, and DSGlassModifier
  implementation (load on demand).
- [references/ios-liquid-glass.md](references/ios-liquid-glass.md) -- `.glassEffect()` signature,
  `GlassEffectContainer`, `.glassEffectID`, fallback matrix.
- [references/ios-design-system-templates.md](references/ios-design-system-templates.md) -- full DSTokens
  scaffold, Asset Catalog steps, typography/spacing extensions, component templates,
  Package.swift skeleton.
- adlc-design `design-tokens` skill -- token pipeline, `build/ios/<brand>/DesignTokens.swift`.
- adlc-design `design-a11y` skill -- contrast, VoiceOver, reduce-motion doctrine.
- Apple, `glassEffect(_:in:)`: https://developer.apple.com/documentation/swiftui/view/glasseffect(_:in:)
- Apple, `GlassEffectContainer`: https://developer.apple.com/documentation/swiftui/glasseffectcontainer
- Apple WWDC 2025 Session 219, "Meet Liquid Glass": https://developer.apple.com/videos/play/wwdc2025/219/
- Apple, `@ScaledMetric`: https://developer.apple.com/documentation/swiftui/scaledmetric
- Apple, HIG -- Materials: https://developer.apple.com/design/human-interface-guidelines/materials
- Style Dictionary v5, ios-swift: https://styledictionary.com/reference/hooks/formats/predefined/
