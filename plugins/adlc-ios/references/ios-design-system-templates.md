<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
# iOS Design System: Implementation Templates

Full code templates for the `ios-design-system` skill. The skill body references this
file for detail; keep them in sync.

---

## DSTokens namespace scaffold

```swift
// DesignSystemInterface/DSTokens.swift
// Import the Style Dictionary generated file or copy its namespace.
// Never hard-code values here -- every property aliases the generated output.
import Foundation

public enum DSTokens {
    public enum Color {}
    public enum Spacing {}
    public enum Radius {}
    public enum Typography {}
}
```

---

## Semantic colors (Asset Catalog any/dark)

For each semantic color token:
1. In Xcode: `Assets.xcassets` > New Color Set > name it `ds.<group>.<role>`
   (e.g., `ds.background.primary`).
2. Set Appearances to "Any, Dark". Assign the light raw value to "Any", dark to "Dark".
3. Reference in the token namespace:

```swift
// DesignSystemInterface/DSTokens+Color.swift
extension DSTokens.Color {
    public static let backgroundPrimary = SwiftUI.Color("ds.background.primary",
                                                         bundle: .module)
    public static let textPrimary       = SwiftUI.Color("ds.text.primary",
                                                         bundle: .module)
}
```

Never use `colorScheme == .dark` branches for semantic colors; the Asset Catalog
handles it automatically, including high-contrast variants.

---

## Dynamic Type text styles

```swift
// DesignSystemInterface/DSTokens+Typography.swift
extension DSTokens.Typography {
    // System font: scales automatically with Dynamic Type
    public static let displayLarge = Font.system(.largeTitle, design: .default, weight: .bold)
    public static let bodyDefault  = Font.system(.body,       design: .default, weight: .regular)
    public static let caption      = Font.system(.caption,    design: .default, weight: .regular)

    // Custom font: use Font.custom with relativeTo: so it still scales
    // public static let brandHeading = Font.custom("MyFont-Bold", size: 28, relativeTo: .title)
}
```

---

## @ScaledMetric spacing

```swift
// DesignSystemInterface/DSTokens+Spacing.swift
// @ScaledMetric makes spacing grow proportionally with Dynamic Type.
// Always specify relativeTo: -- without it the scale ratio is unanchored.
extension DSTokens.Spacing {
    @ScaledMetric(relativeTo: .body) public static var xs: CGFloat = 4
    @ScaledMetric(relativeTo: .body) public static var sm: CGFloat = 8
    @ScaledMetric(relativeTo: .body) public static var md: CGFloat = 16
    @ScaledMetric(relativeTo: .body) public static var lg: CGFloat = 24
    @ScaledMetric(relativeTo: .body) public static var xl: CGFloat = 32
}
```

Raw numeric literals in `.padding()` calls inside DS components are a build-time
violation; every spacing value resolves through `DSTokens.Spacing.*`.

---

## DSPrimaryButton component template

```swift
// DesignSystemImpl/DSPrimaryButton.swift
import SwiftUI
import DesignSystemInterface

public struct DSPrimaryButton: View {
    let label: String
    let action: () -> Void

    public var body: some View {
        Button(action: action) {
            Text(label)
                .font(DSTokens.Typography.bodyDefault)
                .padding(.horizontal, DSTokens.Spacing.lg)
                .padding(.vertical, DSTokens.Spacing.sm)
                .background(DSTokens.Color.backgroundPrimary)
                .foregroundStyle(DSTokens.Color.textPrimary)
                .clipShape(RoundedRectangle(cornerRadius: DSTokens.Radius.button))
        }
    }
}
```

Follow this pattern for every new DS component: tokens for all color, spacing, and
radius values; no raw literals.

---

## Liquid Glass modifier

```swift
// DesignSystemInterface/View+Glass.swift
import SwiftUI

public extension View {
    /// Use instead of calling .glassEffect() directly.
    /// Fallback to .ultraThinMaterial on iOS < 26.
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

See `ios-liquid-glass.md` for `GlassEffectContainer` + `.glassEffectID` usage and
the full fallback matrix.

---

## SPM Package.swift skeleton for DesignSystem

```swift
// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "DesignSystem",
    platforms: [.iOS(.v17)],
    products: [
        .library(name: "DesignSystemInterface", targets: ["DesignSystemInterface"]),
        // DesignSystemImpl is NOT a product; the app target lists it as a target dep
    ],
    targets: [
        .target(name: "DesignSystemInterface", dependencies: []),
        .target(
            name: "DesignSystemImpl",
            dependencies: [.target(name: "DesignSystemInterface")],
            resources: [.process("Resources")]  // include Assets.xcassets here
        ),
    ]
)
```
