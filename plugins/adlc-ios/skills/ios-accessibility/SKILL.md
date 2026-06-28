---
name: ios-accessibility
description: >-
  This skill should be used when the user asks to "add VoiceOver support",
  "apply accessibility labels", "set accessibilityLabel or accessibilityHint",
  "make this view accessible", "audit accessibility", "run an accessibility
  audit on iOS", "check VoiceOver order", "fix Dynamic Type", "my text doesn't
  scale with font size", "add @ScaledMetric", "run performAccessibilityAudit",
  "add accessibility to a SwiftUI view", "combine accessibility elements",
  "hide decorative images from VoiceOver", "fix accessibilityElement grouping",
  "add custom rotor", "check hit region size", "audit contrast in Xcode",
  "wire accessibility tests into CI", "does this pass the Accessibility
  Inspector", or "fix a11y issues on iOS". Applies and audits SwiftUI
  accessibility: VoiceOver modifiers (.accessibilityLabel/Hint/Value/traits,
  .accessibilityElement), Dynamic Type scaling via @ScaledMetric, and
  automated audit via Xcode Accessibility Inspector and
  performAccessibilityAudit() in CI. WCAG doctrine and the AA compliance bar
  are owned by the adlc-design design-a11y skill -- this skill adds the
  SwiftUI/VoiceOver bindings and the iOS-specific verify loop.
version: 0.1.0
---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# iOS accessibility (SwiftUI + VoiceOver)

Apply VoiceOver modifiers, enforce Dynamic Type scaling, and verify with
`performAccessibilityAudit()`. WCAG 2.2 AA doctrine and the per-criterion
compliance bar live in the `adlc-design` `design-a11y` skill -- load it for
contrast ratios, target size minimums, and the design-time checklist. This
skill covers the SwiftUI bindings and the iOS audit loop only.

## Step 1: Detect first

Never impose modifiers blindly. Inspect what exists:

```bash
# Existing a11y modifiers
grep -rn "accessibilityLabel\|accessibilityHint\|accessibilityValue\
\|accessibilityElement\|accessibilityHidden\|accessibilityTraits\
\|accessibilityAction\|ScaledMetric\|performAccessibilityAudit" \
  --include="*.swift" . | head -30

# UITest target present?
find . -name "*UITest*" -o -name "*AccessibilityAudit*" | grep -v ".build" | head -10

# iOS deployment target (determines which APIs are safe to use)
grep -rn "\.iOS\|IPHONEOS_DEPLOYMENT_TARGET" \
  --include="Package.swift" --include="*.pbxproj" . | head -10
```

Record: existing modifier usage (match conventions, don't re-do what exists),
UITest target name, minimum deployment version. Mark anything not found
`unknown`. Never invent modifier arguments or identifier strings.

## Step 2: Apply VoiceOver modifiers

Cover these four cases on every screen. For code samples, see
[references/ios-accessibility-detail.md](references/ios-accessibility-detail.md).

- **Interactive elements:** `.accessibilityLabel` + `.accessibilityHint` on every icon-only button.
- **Decorative content:** `.accessibilityHidden(true)` to hide from VoiceOver.
- **Card/row grouping:** `.accessibilityElement(children: .combine)` for one focus stop per row. Use `.combine` when reading order is predictable; use `.ignore` only when a custom control fully manages its own a11y tree and supplies its own `.accessibilityLabel`.
- **State-bearing elements:** `.accessibilityValue` to expose current state (e.g., toggle on/off).
- **Hit areas:** expand to min 44x44 pt via `.frame(minWidth:minHeight:).contentShape(Rectangle())`.

## Step 3: Enforce Dynamic Type with `@ScaledMetric`

Every hardcoded point value that participates in layout is a `@ScaledMetric`
candidate. Apply to icon frames, hit areas, and fixed spacing constants. Never
hardcode `.font(.system(size:))`; use semantic styles (`.font(.body)`, etc.).
Test at xSmall and xxxLarge in Simulator or via Accessibility Inspector font slider.

For code samples, see [references/ios-accessibility-detail.md](references/ios-accessibility-detail.md).

## Step 4: Audit (Accessibility Inspector + CI)

**Manual (Xcode Accessibility Inspector):** Open Xcode > Open Developer Tool >
Accessibility Inspector. Point at the running simulator. Run the audit and
clear every issue before calling the feature done.

**Automated CI (`performAccessibilityAudit`, Xcode 15+ / iOS 17+):** Add a
`XCUITest` that calls `app.performAccessibilityAudit()` after launch. Run with
`xcodebuild test -only-testing:<UITestTarget>/AccessibilityAuditTests`. Target
zero new audit issues per PR. For the full snippet including scope flags and
false-positive suppression, see
[references/ios-accessibility-detail.md](references/ios-accessibility-detail.md).

## Step 5: Verify loop (pass/fail, not "looks right")

```
1. Accessibility Inspector audit -> 0 issues remaining.
2. VoiceOver on simulator (Cmd+F5) -> every interactive element has a label;
   reading order matches visual order.
3. Dynamic Type xxxLarge -> no truncation, no overflow, hit areas >= 44x44 pt.
4. xcodebuild AccessibilityAuditTests -> exit 0.
Report:
  Screen: <name>
  Inspector issues fixed: <n>
  VoiceOver walk: PASS | FAIL <element list>
  Dynamic Type xxxLarge: PASS | FAIL <detail>
  performAccessibilityAudit: PASS | FAIL <issue list>
```

## Outbound checkpoint

Local work needs no approval. Anything outbound (publish, push, post) needs an explicit per-action "yes"; see the global consent law.

## References

- [references/ios-accessibility-detail.md](references/ios-accessibility-detail.md) -- VoiceOver modifier
  code samples, `@ScaledMetric` examples, `performAccessibilityAudit` snippet and CI command.
- [references/ios-accessibility.md](references/ios-accessibility.md) -- VoiceOver modifier
  table, Liquid Glass a11y notes.
- `adlc-design` `design-a11y` skill -- WCAG 2.2 AA doctrine, contrast ratios,
  target size minimums, design-time checklist (cite up for compliance bar).
- Apple, SwiftUI Accessibility modifiers:
  https://developer.apple.com/documentation/swiftui/view-accessibility
- Apple, AccessibilityTraits:
  https://developer.apple.com/documentation/swiftui/accessibilitytraits
- Apple, `performAccessibilityAudit(_:)`:
  https://developer.apple.com/documentation/xctest/xcuiapplication/performaccessibilityaudit(_:)
- Apple HIG Accessibility:
  https://developer.apple.com/design/human-interface-guidelines/accessibility
