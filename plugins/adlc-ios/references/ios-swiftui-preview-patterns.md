<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
# iOS SwiftUI Preview Patterns

Referenced by `skills/ios-swiftui-preview/SKILL.md`. Contains copy-paste templates
for the state-matrix previews, dark mode, Dynamic Type variants, and the traits pattern.

## State matrix

Enumerate these cases for every view with a sealed state type:

| State | What to show |
|---|---|
| `loading` | Progress indicator, no content |
| `content(data)` | Representative data; also a boundary case (long text, zero count) |
| `empty` | Empty-state illustration or message |
| `error(message)` | Error text, retry affordance |

If the view takes plain parameters with no sealed type, enumerate the parameter
combinations that produce visually distinct layouts.

## Full state matrix + variants template

```swift
import SwiftUI

// MARK: - Previews

#Preview("<Feature>View - Loading") {
    <Feature>View(state: .loading)
        .environment(\.<feature>Service, Preview<Feature>Service())
}

#Preview("<Feature>View - Content") {
    <Feature>View(state: .content(
        <Feature>Item(id: "1", title: "Representative title", subtitle: nil)
    ))
    .environment(\.<feature>Service, Preview<Feature>Service())
}

#Preview("<Feature>View - Content (long text)") {
    <Feature>View(state: .content(
        <Feature>Item(id: "2",
                      title: String(repeating: "Long title word ", count: 8),
                      subtitle: "Subtitle that may wrap to multiple lines")
    ))
    .environment(\.<feature>Service, Preview<Feature>Service())
}

#Preview("<Feature>View - Empty") {
    <Feature>View(state: .empty)
        .environment(\.<feature>Service, Preview<Feature>Service())
}

#Preview("<Feature>View - Error") {
    <Feature>View(state: .error("Network unreachable"))
        .environment(\.<feature>Service, Preview<Feature>Service())
}

// Dark mode -- exercises color tokens and adaptive assets
#Preview("<Feature>View - Dark") {
    <Feature>View(state: .content(
        <Feature>Item(id: "3", title: "Dark mode check", subtitle: nil)
    ))
    .preferredColorScheme(.dark)
    .environment(\.<feature>Service, Preview<Feature>Service())
}

// Accessibility Dynamic Type xxxLarge -- surfaces text truncation and layout breaks
#Preview("<Feature>View - AX Large Text") {
    <Feature>View(state: .content(
        <Feature>Item(id: "4", title: "AX large text", subtitle: "Subtitle")
    ))
    .environment(\.dynamicTypeSize, .accessibility3)
    .environment(\.<feature>Service, Preview<Feature>Service())
}
```

## Traits for small / self-sizing components

```swift
// .sizeThatFitsLayout shrinks the canvas to the view's intrinsic size
#Preview("<Feature>Badge", traits: .sizeThatFitsLayout) {
    <Feature>BadgeView(count: 42)
}
```

Use `traits: .sizeThatFitsLayout` for chips, badges, and cells. Use the default
device-framed canvas for full-screen views. Available iOS 17+ via `PreviewTrait`.

## Preview stub pattern (when no stub exists)

```swift
// In <Feature>Interface -- defaultValue is the preview stub, NEVER fatalError
struct <Feature>ServiceKey: EnvironmentKey {
    static let defaultValue: any <Feature>Service = Preview<Feature>Service()
}
```

A `fatalError` in an `EnvironmentKey.defaultValue` crashes every `#Preview` that
reads the environment before an explicit `.environment(...)` injection. Always use a
no-op stub as the default.

## Dynamic Type sizes reference

| Environment value | `ContentSizeCategory` / `DynamicTypeSize` | Typical use |
|---|---|---|
| `.environment(\.sizeCategory, .large)` | Default system size | Baseline |
| `.environment(\.dynamicTypeSize, .xLarge)` | Slightly bigger | Common user setting |
| `.environment(\.dynamicTypeSize, .accessibility3)` | xxxLarge | Stress test: truncation, overflow |

Prefer `.dynamicTypeSize` (SwiftUI native, iOS 15+) over the deprecated
`.sizeCategory` (`UIContentSizeCategory` shim).
