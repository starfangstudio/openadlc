<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
# iOS Accessibility Reference

Quick-reference for SwiftUI VoiceOver modifiers, Dynamic Type patterns, and
`performAccessibilityAudit` usage. Consumed by the `ios-accessibility` skill.

---

## VoiceOver modifier cheat-sheet

| Modifier | When to use | Notes |
|---|---|---|
| `.accessibilityLabel("…")` | Every interactive or meaningful element | Overrides the default; keep it < 40 chars; always localized |
| `.accessibilityHint("…")` | Non-obvious actions | Describes the *result*, not the *action* ("Opens detail view", not "Tap here") |
| `.accessibilityValue("…")` | State-bearing elements (toggles, sliders, progress) | "On" / "Off", "3 of 5", percentage |
| `.accessibilityTraits(.isButton)` | Custom views acting as buttons | Combine traits: `.isButton.isSelected` |
| `.accessibilityAddTraits(.updatesFrequently)` | Live-updating values | Reduces VoiceOver re-announcement noise |
| `.accessibilityRemoveTraits(.isImage)` | Decorative images whose label would be noise | Pair with `.accessibilityHidden(true)` for purely decorative assets |
| `.accessibilityHidden(true)` | Decorative or redundant elements | VoiceOver skips entirely |
| `.accessibilityElement(children: .combine)` | Card / row grouping multiple sub-labels | Merges children into one focusable element; preview confirms order |
| `.accessibilityElement(children: .ignore)` | Custom control that draws its own a11y tree | You must supply `.accessibilityLabel` when using this |
| `.accessibilityAction("…") { }` | Swipe-up/down custom action | Supplement, not replace, the tap |
| `.accessibilityRotorEntry(id:in:)` | Expose items in a custom rotor | Pair with `.accessibilityRotor("…") { }` on the container |
| `.accessibilityFocused(_:)` | Programmatically move VoiceOver focus | E.g. after an alert dismisses or a sheet opens |
| `.accessibilitySortPriority(_:)` | Override reading order within a group | Higher = earlier; default 0 |

---

## Dynamic Type with `@ScaledMetric`

Use `@ScaledMetric` for any hardcoded point value that participates in the layout:

```swift
// Scales relative to the .body text style by default
@ScaledMetric private var iconSize: CGFloat = 24
@ScaledMetric(relativeTo: .title) private var cardPadding: CGFloat = 16

var body: some View {
    Image(systemName: "star.fill")
        .frame(width: iconSize, height: iconSize)
        .padding(cardPadding)
}
```

Rules:
- Every icon frame, spacing constant, and minimum hit-area dimension is a
  `@ScaledMetric` candidate.
- Never hardcode point values in `.frame()` or `.padding()` for content that
  scales with text -- use `@ScaledMetric` or a relative layout (`.padding(.horizontal)`,
  `Spacer()`).
- Test at xSmall, Large (default), and xxxLarge via Simulator > Device > Increase
  Text Size, or in Xcode Accessibility Inspector (Font size slider).

---

## `performAccessibilityAudit` (Xcode 15+)

Runs Apple's Accessibility Inspector checks programmatically inside an XCUITest target.

### Minimal CI test

```swift
import XCTest

final class AccessibilityAuditTests: XCTestCase {
    func testMainScreenPassesAudit() throws {
        let app = XCUIApplication()
        app.launch()
        // Audit the full screen against all built-in checks
        try app.performAccessibilityAudit()
    }
}
```

### Scope to specific audit types

```swift
// Only contrast and Dynamic Type issues
try app.performAccessibilityAudit(for: [.contrast, .dynamicType])
```

Available `XCUIAccessibilityAuditType` flags (Xcode 15):
`.contrast`, `.dynamicType`, `.elementDetection`, `.hitRegion`,
`.sufficientElementDescription`, `.textClipping`, `.trait` (and `.all` / `.none`).

### Suppress a known false-positive

```swift
try app.performAccessibilityAudit { issue in
    // Return true to ignore the issue (i.e., "this is known/acceptable")
    issue.element?.identifier == "decorativeBackground" ? true : false
}
```

### Run in CI (xcodebuild)

```bash
set -o pipefail && xcodebuild test \
  -workspace <App>.xcworkspace \
  -scheme <Scheme> \
  -destination 'platform=iOS Simulator,name=iPhone 16,OS=latest' \
  -only-testing:<UITestTarget>/AccessibilityAuditTests \
  | xcbeautify
```

Fail the CI step on any unresolved audit issue. Track count per build; target
zero new issues per PR.

---

## Liquid Glass (iOS 26) accessibility notes

- Text is always rendered on solid layers, not directly on glass: no extra
  modifier needed for text legibility.
- Respect `@Environment(\.accessibilityReduceTransparency)` and
  `@Environment(\.accessibilityReduceMotion)` when adding custom glass effects.
  Let the system handle the Reduce Transparency / Increase Contrast adaptations
  automatically; override only if your custom layer cannot.
- Glass containers scale with Dynamic Type automatically when sized with
  `@ScaledMetric` or flexible layouts.

---

## References

- Apple, SwiftUI Accessibility modifiers: https://developer.apple.com/documentation/swiftui/view-accessibility
- Apple, AccessibilityTraits: https://developer.apple.com/documentation/swiftui/accessibilitytraits
- Apple, `performAccessibilityAudit(_:)`: https://developer.apple.com/documentation/xctest/xcuiapplication/performaccessibilityaudit(_:)
- Apple, Accessibility Inspector (Xcode): https://developer.apple.com/library/archive/documentation/Accessibility/Conceptual/AccessibilityMacOSX/OSXAXTestingApps.html
- Apple HIG Accessibility: https://developer.apple.com/design/human-interface-guidelines/accessibility
- iOS 26 Liquid Glass accessibility notes: https://vikramios.medium.com/the-liquid-glass-ui-revolution-everything-ios-developers-need-to-know-right-now-e29144a5e88a
