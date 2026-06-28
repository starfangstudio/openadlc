<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
Consumed by the `ios-design-system` skill. Load on demand; do not load independently.

## DSTokens color extension (Step 3)

Wire the Style Dictionary output into a typed `DSTokens` namespace. Never hard-code values;
every property aliases the generated output.

```swift
// DesignSystemInterface/DSTokens+Color.swift
extension DSTokens.Color {
    public static let backgroundPrimary = SwiftUI.Color("ds.background.primary", bundle: .module)
    public static let textPrimary       = SwiftUI.Color("ds.text.primary", bundle: .module)
}
```

Add an Asset Catalog entry for each semantic color (New Color Set, Appearances "Any, Dark").
The catalog handles dark mode and high-contrast automatically; never branch on `colorScheme`
for semantic colors.

Full color/type/spacing scaffolds and Asset Catalog step-by-step: [references/ios-design-system-templates.md](references/ios-design-system-templates.md).

## @ScaledMetric spacing extension (Step 4)

```swift
extension DSTokens.Spacing {
    @ScaledMetric(relativeTo: .body) public static var md: CGFloat = 16
}
```

Always supply `relativeTo:`; without it the scale ratio is unanchored.

## DS component usage pattern (Step 5)

```swift
Text(label)
    .font(DSTokens.Typography.bodyDefault)
    .padding(.horizontal, DSTokens.Spacing.lg)
    .background(DSTokens.Color.backgroundPrimary)
```

Full component templates (`DSPrimaryButton`, `GlassCard`, etc.):
[references/ios-design-system-templates.md](references/ios-design-system-templates.md).

## Liquid Glass modifier implementation (Step 6)

```swift
// DesignSystemInterface/View+Glass.swift
public extension View {
    func dsGlassBackground(cornerRadius: CGFloat = DSTokens.Radius.card) -> some View {
        modifier(DSGlassModifier(cornerRadius: cornerRadius))
    }
}

struct DSGlassModifier: ViewModifier {
    let cornerRadius: CGFloat
    func body(content: Content) -> some View {
        if #available(iOS 26, *) {
            content.glassEffect(.regular, in: RoundedRectangle(cornerRadius: cornerRadius))
        } else {
            content.background(.ultraThinMaterial,
                               in: RoundedRectangle(cornerRadius: cornerRadius))
        }
    }
}
```

`GlassEffectContainer` is only needed when sibling glass elements must morph together.
Full API surface, `.glassEffectID`, and fallback matrix:
[references/ios-liquid-glass.md](references/ios-liquid-glass.md).
