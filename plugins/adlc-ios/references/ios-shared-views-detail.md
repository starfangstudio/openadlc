<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
Consumed by the `ios-shared-views` skill. Load on demand; do not load independently.

## Step 1 detection commands

```bash
# Shared/design-system targets
find . -type d \( -name "DesignSystem*" -o -name "SharedUI*" -o -name "CommonUI*" \) \
  -not -path "*/build/*" | head -20

# Token types in use
grep -rEln "Color\.|Font\.|spacing|Padding|Radius" \
  --include="*.swift" . | grep -i "token\|theme\|style" | head -10

# Preview convention (#Preview macro vs PreviewProvider)
grep -rn "#Preview\|PreviewProvider" --include="*.swift" . | head -10

# Accessibility patterns
grep -rn "accessibilityLabel\|accessibilityElement\|accessibilityAddTraits" \
  --include="*.swift" . | head -10

# Deployment target (iOS 17+ enables #Preview macro)
grep -rn "\.iOS(\|IPHONEOS_DEPLOYMENT_TARGET" . | head -5
```

## API design template

Parameter order: required data, required callbacks, optional params (defaulted), then trailing `@ViewBuilder content` slot.

```swift
struct SectionCard<Content: View>: View {
    let title: String                        // required data
    var onTap: (() -> Void)? = nil          // optional callback
    @ViewBuilder var content: () -> Content  // trailing slot

    var body: some View { ... }
}
```

Multiple slots: use descriptive names (`leading`, `trailing`, `header`, `actions`) with `= { EmptyView() }` defaults for optional slots.

## Design-system token usage

```swift
import DesignSystemInterface

VStack(spacing: DesignTokens.Spacing.md) { ... }
    .padding(DesignTokens.Spacing.md)
    .background(DesignTokens.Color.surfaceDefault)
    .clipShape(RoundedRectangle(cornerRadius: DesignTokens.Radius.card))
```

## Preview samples

```swift
#Preview("Default") {
    SectionCard(title: "Section title") { Text("Slot content") }
        .padding()
}

#Preview("Empty slot") {
    SectionCard(title: "Empty") { EmptyView() }.padding()
}
```

Use `#Preview` if iOS 17+; else `PreviewProvider`. Match the convention discovered in Step 1. Never use `fatalError` in a preview environment value default -- it crashes the preview canvas; use a no-op stub instead.

## Step 8 verification commands

```bash
# Build the target containing the new view
swift build --package-path Packages/<TargetPackage>

# Confirm all former call sites build (full app)
xcodebuild build -workspace <App>.xcworkspace -scheme <AppScheme> \
  -destination 'platform=iOS Simulator,name=iPhone 16' | xcbeautify

# No remaining duplicated copies
grep -rn "<OriginalViewName>" --include="*.swift" . | grep -v "SharedUI\|DesignSystem"
```
