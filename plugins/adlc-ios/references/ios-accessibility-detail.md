<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
Consumed by the `ios-accessibility` skill. Load on demand; do not load independently.

## VoiceOver modifier code samples

### Interactive elements: label + hint on icon-only buttons

```swift
Button(action: submit) { Image(systemName: "checkmark.circle.fill") }
    .accessibilityLabel("Submit order")
    .accessibilityHint("Confirms and places the order")
```

### Decorative content: hide from VoiceOver

```swift
Image("background-wave").accessibilityHidden(true)
```

### Card/row grouping: one focus stop per row

```swift
VStack(alignment: .leading) {
    Text(item.title); Text(item.subtitle).foregroundStyle(.secondary)
}.accessibilityElement(children: .combine)
```

Use `.combine` when reading order is predictable. Use `.ignore` only when a custom control fully manages its own a11y tree and supplies `.accessibilityLabel`.

### State-bearing elements: expose current value

```swift
Toggle("Notifications", isOn: $enabled).accessibilityValue(enabled ? "On" : "Off")
```

### Hit areas: expand without changing visual size (min 44x44 pt, Apple HIG)

```swift
iconButton.frame(minWidth: 44, minHeight: 44).contentShape(Rectangle())
```

## Dynamic Type: `@ScaledMetric` examples

Apply to icon frames, hit areas, and fixed spacing constants:

```swift
@ScaledMetric private var iconSize: CGFloat = 24
@ScaledMetric(relativeTo: .title) private var cardPadding: CGFloat = 16
```

Never hardcode `.font(.system(size: 14))`; use semantic styles (`.font(.body)`).
Test at xSmall and xxxLarge in Simulator or via Accessibility Inspector font slider.

## `performAccessibilityAudit` CI snippet

Minimal test (Xcode 15+ / iOS 17+):

```swift
func testScreenPassesAudit() throws {
    let app = XCUIApplication(); app.launch()
    try app.performAccessibilityAudit()
}
```

To scope the audit or suppress known false positives, pass `AXAuditElement` flags to `performAccessibilityAudit(_:)`.
See Apple docs: https://developer.apple.com/documentation/xctest/xcuiapplication/performaccessibilityaudit(_:)

CI command:

```bash
xcodebuild test -only-testing:<UITestTarget>/AccessibilityAuditTests
```
