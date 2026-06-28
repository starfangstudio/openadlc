<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
# iOS 26 Liquid Glass: API Surface and Fallbacks

Covers the `.glassEffect()` SwiftUI API (iOS 26+), `GlassEffectContainer`, and
the `if #available` fallback strategy for iOS 17–25 targets.

## Core modifier

```swift
// Applies the Liquid Glass material to any view (iOS 26+)
view
    .padding()
    .glassEffect()                          // default shape: rectangle with system corner radius
    .glassEffect(.regular, in: .rect(cornerRadius: 16))   // explicit shape
    .glassEffect(.regular, in: .capsule)    // pill shape
```

`glassEffect(_:in:)` signature:
- First arg: `GlassEffectStyle` -- `.regular` (default), `.clear`, `.tinted`, `.prominent`
- Second arg: any `Shape` (uses `RoundedRectangle`, `Capsule`, `Circle`, etc.)
- No required tint; material adapts to background content automatically.

## GlassEffectContainer

Wrap sibling views that should share a unified glass shape and coordinate morph
animations:

```swift
GlassEffectContainer(spacing: 8) {
    VStack(spacing: 8) {
        HeaderView()
            .glassEffect()
            .glassEffectID("header", in: namespace)
        CardView()
            .glassEffect()
            .glassEffectID("card", in: namespace)
    }
}
```

- `.glassEffectID(_:in:)` requires a `@Namespace` for cross-state morphing.
- Elements inside one `GlassEffectContainer` merge into a single fluid shape when
  adjacent; use `spacing:` to control merge distance.
- Do NOT nest `GlassEffectContainer` inside another; flatten the hierarchy.

## Availability gate (mandatory pattern)

Gate every call site; never call `.glassEffect()` without a check:

```swift
// ViewModifier approach -- preferred for reuse
struct GlassBackground: ViewModifier {
    func body(content: Content) -> some View {
        if #available(iOS 26, *) {
            content.glassEffect()
        } else {
            content.background(.ultraThinMaterial)
        }
    }
}

extension View {
    func dsGlassBackground() -> some View {
        modifier(GlassBackground())
    }
}
```

Apply through the design system wrapper (`.dsGlassBackground()`) so the fallback
is one edit, not N call sites.

## Design system token integration

Never hard-code glass shapes at call sites. Define a design-system-level modifier that
reads from the token layer:

```swift
// DesignSystemImpl/GlassCard.swift
struct GlassCard<Content: View>: View {
    let cornerRadius: CGFloat    // sourced from DSTokens.Radius.card
    @ViewBuilder let content: () -> Content

    var body: some View {
        content()
            .padding(DSTokens.Spacing.card)
            .dsGlassBackground(cornerRadius: cornerRadius)
    }
}
```

`DSTokens.Radius.card` resolves from the Style Dictionary build output
(`build/ios/<brand>/DesignTokens.swift`). Import only the tokens target from
feature targets; never import DesignSystemImpl directly.

## What Liquid Glass is NOT for

- Do not apply `.glassEffect()` to plain text blocks, data tables, or content-heavy
  surfaces; it degrades readability.
- Do not use it as a general card style for every surface; reserve it for floating
  UI layers (toolbars, overlays, sheets, action panels).
- Accessibility: glass materials reduce contrast; always verify AA contrast against
  every background the glass floats over. Defer a11y doctrine to the adlc-design
  `design-a11y` skill.

## Fallback matrix

| iOS version | Material | Notes |
|---|---|---|
| iOS 26+ | `.glassEffect()` | Full Liquid Glass with morphing |
| iOS 17–25 | `.ultraThinMaterial` | No morphing; acceptable visual proxy |
| iOS < 17 | Unsupported deployment target (minimum iOS 17 per project) | N/A |

## References

- Apple WWDC 2025, "Meet Liquid Glass" (Session 219):
  https://developer.apple.com/videos/play/wwdc2025/219/
- Apple, SwiftUI `glassEffect(_:in:)` documentation:
  https://developer.apple.com/documentation/swiftui/view/glasseffect(_:in:)
- Apple, `GlassEffectContainer` documentation:
  https://developer.apple.com/documentation/swiftui/glasseffectcontainer
- Apple, Human Interface Guidelines -- Materials:
  https://developer.apple.com/design/human-interface-guidelines/materials
- Skyscraper guide, "Apple Liquid Glass in iOS 26: Complete SwiftUI Implementation":
  https://getskyscraper.com/blog/apple-liquid-glass-ios-26-swiftui-guide
