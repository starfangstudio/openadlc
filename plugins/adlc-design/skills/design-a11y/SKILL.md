---
name: design-a11y
description: >-
  This skill should be used when the user asks to "run an accessibility audit",
  "check a11y compliance", "does this meet WCAG 2.2", "audit contrast ratios",
  "check focus visibility", "verify target sizes", "is this keyboard accessible",
  "check VoiceOver order", "check TalkBack semantics", "audit color-not-alone",
  "run axe on this page", "does this pass AA", "accessibility checklist for this
  screen", "check reduced-motion support", "focus is hidden behind the nav bar",
  "our button doesn't pass contrast", "audit the design for screen reader order",
  or "does this meet ISO 40500". Runs a WCAG 2.2 / ISO 40500:2025 Level AA
  design-time audit with per-platform bindings (ARIA + axe for web,
  VoiceOver/performAccessibilityAudit for iOS, TalkBack/Compose semantics for
  Android). Wraps the built-in 'design:accessibility-review' command and adds
  detect-first grounding, a pass/fail checklist, platform-specific verify
  commands, and the ADLC outbound checkpoint.
version: 0.1.0
---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# Design accessibility audit (WCAG 2.2 / ISO 40500:2025)

Wraps `design:accessibility-review`. That command runs the base audit; this
skill adds: detect the platform stack first, map each criterion to the right
platform API, run the automated verify commands, and stop to get the operator's
explicit yes before any outbound action.

The compliance bar is **WCAG 2.2 Level AA** (= ISO/IEC 40500:2025, effective
EU EAA June 2025). Aim for AAA on Focus Appearance (2.4.13): the 2 px / 3:1
ring is achievable at zero extra engineering cost if designed in from the start.

---

## Step 1: Detect platform and conventions

Never assume. Run these and record the results before auditing anything.

```bash
# Web: framework + a11y tooling already present
grep -rEn "aria-|role=|@axe-core|cypress-axe|jest-axe" --include="*.{tsx,jsx,ts,js,vue,html}" . | head -20
grep -rn "axe\|pa11y\|lighthouse" package.json .github/ | head -10

# iOS: SwiftUI vs UIKit; any existing a11y modifiers
grep -rn "accessibilityLabel\|accessibilityHint\|accessibilityElement\|accessibilityReduceMotion\|performAccessibilityAudit" --include="*.swift" . | head -20

# Android/Compose: semantics blocks + a11y test deps
grep -rn "semantics\|contentDescription\|testTag\|AccessibilityNodeInfoCompat\|traversalIndex" --include="*.kt" . | head -20
grep -rn "composeTestRule\|onNodeWithTag\|assertIsDisplayed" --include="*.kt" . | head -10
```

Record: web / iOS / Android / KMP-shared. Mark anything unresolvable `unknown`
and stop to ask; do not invent semantics attribute names or test APIs.

---

## Step 2: Run automated checks per platform

Run the command for the detected platform. Re-run after every fix.

**Web**
```bash
npx axe http://localhost:3000 --include main --tags wcag2a,wcag2aa,wcag22aa
```
Axe catches ~30-40% of WCAG issues; the manual checklist covers the rest.

**iOS (Xcode 15+)** -- add to your UITest target and run:
```bash
xcodebuild test -scheme <Scheme> -destination 'platform=iOS Simulator,name=iPhone 15' \
  -only-testing:<Target>/AccessibilityAuditTests
```
```swift
func testAccessibilityAudit() throws {
    let app = XCUIApplication(); app.launch()
    try app.performAccessibilityAudit()
}
```

**Android / Compose**
```kotlin
@Test fun semanticsAudit() {
    composeTestRule.setContent { YourScreen() }
    composeTestRule.onNodeWithTag("submit_button")
        .assertContentDescriptionEquals("Submit order")
}
```
Then enable TalkBack on device and verify reading order matches the design spec.

For full command options and `XCUIAccessibilityAuditType` flags, see
[references/design-a11y-detail.md](references/design-a11y-detail.md).

---

## Step 3: Design-time checklist (pass/fail)

A single FAIL blocks handoff. Record each as PASS / FAIL / N/A with a brief
note. Never mark PASS without evidence (tool output, token value, or ratio).

```
Contrast
[ ] Normal text (< 18 pt / < 14 pt bold): 4.5:1 vs background      SC 1.4.3
[ ] Large text (>= 18 pt / >= 14 pt bold): 3:1 vs background        SC 1.4.3
[ ] UI chrome (borders, icons, input outlines): 3:1 vs adjacent      SC 1.4.11

Color not alone
[ ] Every state (error, success, disabled, selected) uses icon/shape/
    label in addition to color                                        SC 1.4.1

Target size
[ ] Web: pointer target >= 24x24 CSS px or >= 24 px offset spacing   SC 2.5.8
[ ] iOS: tap target >= 44x44 pt                                       SC 2.5.8
[ ] Android: touch target >= 48x48 dp                                 SC 2.5.8

Focus
[ ] Focus indicator visible; >= 2 px perimeter, >= 3:1 contrast      SC 2.4.7 / 2.4.13
[ ] Focused element not fully hidden by sticky header/sheet/toast     SC 2.4.11
[ ] Tab / VoiceOver / TalkBack order matches visual reading order     SC 2.4.3

Motion
[ ] Animations have a no-motion fallback                              SC 2.3.3, platform HIG
[ ] No content flashes > 3 Hz                                        SC 2.3.1

Gestures
[ ] Every drag/swipe has a single-tap alternative                     SC 2.5.7

Auth / forms
[ ] Multi-step forms do not re-ask for data already given this session SC 3.3.7
[ ] Login does not require cognitive test without accessible alternative SC 3.3.8

Structure
[ ] Heading hierarchy is logical; regions are labeled                 SC 1.3.1
[ ] Instructions do not rely on shape, color, size, position alone    SC 1.3.3
```

For per-platform binding notes on the three most-failed criteria (Focus
Appearance 2.4.13, Target Size 2.5.8, Focus Not Obscured 2.4.11), see
[references/design-a11y-detail.md](references/design-a11y-detail.md).

---

## Step 4: Verify loop

```
Run automated checks (Step 2) -> fix failures -> re-run until clean.
Work the manual checklist (Step 3) -> FAIL items go to the designer as
  annotated spec comments, not verbal notes.
Report format:
  Platform: <web|iOS|Android|KMP>
  Tool output: <axe violations / XCTest failures / manual>
  Checklist: <n PASS, n FAIL, n N/A>
  Blocking failures: <criterion + exact component>
  Recommendations: <non-blocking improvements>
```

---

## Outbound checkpoint

Local work needs no approval. Outbound here (posting audit results to a ticket, PR, Slack, or a Figma comment): stop, present exactly what would go out, and get the operator's explicit "yes" first (global consent law).

---

## References

- W3C WCAG 2.2 specification: https://www.w3.org/TR/WCAG22/
- ISO/IEC 40500:2025: https://www.iso.org/standard/91029.html
- W3C "What's new in WCAG 2.2": https://www.w3.org/WAI/standards-guidelines/wcag/new-in-22/
- Apple HIG Accessibility: https://developer.apple.com/design/human-interface-guidelines/accessibility
- Xcode 15 performAccessibilityAudit: https://www.polpiella.dev/xcode-15-automated-accessibility-audits/
- Material 3 Accessibility: https://m3.material.io/foundations/accessible-design/overview
- Kotlin Multiplatform Compose iOS accessibility: https://kotlinlang.org/docs/multiplatform/compose-ios-accessibility.html
- axe-core rule descriptions: https://github.com/dequelabs/axe-core/blob/develop/doc/rule-descriptions.md
- [references/wcag-2.2.md](references/wcag-2.2.md) -- criteria table + design-time checklist
- [references/design-a11y-detail.md](references/design-a11y-detail.md) -- full command options, XCUIAccessibilityAuditType flags, per-platform binding notes
