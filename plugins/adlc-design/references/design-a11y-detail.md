<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
Consumed by the `design-a11y` skill. Load on demand; do not load independently.

---

## Automated check commands

### Web

```bash
# axe-core CLI against a running dev server (port 3000 is an example)
npx axe http://localhost:3000 --include main --tags wcag2a,wcag2aa,wcag22aa

# Or via @axe-core/playwright / cypress-axe in the test suite
npx playwright test --grep a11y
npx cypress run --spec "cypress/e2e/a11y.cy.ts"
```

Axe catches ~30-40% of WCAG issues automatically; the rest require the manual checklist below.

### iOS (Xcode 15+)

```swift
// In a UITest target -- runs Accessibility Inspector audits via XCTest
func testAccessibilityAudit() throws {
    let app = XCUIApplication()
    app.launch()
    try app.performAccessibilityAudit()
}
```

```bash
xcodebuild test -scheme <Scheme> -destination 'platform=iOS Simulator,name=iPhone 15' \
  -only-testing:<Target>/AccessibilityAuditTests
```

`performAccessibilityAudit()` accepts `XCUIAccessibilityAuditType` flags to narrow scope (e.g. `.contrast`, `.hitRegion`, `.dynamicType`).

### Android / Compose

```kotlin
// In a Compose UI test
@Test
fun semanticsAudit() {
    composeTestRule.setContent { YourScreen() }
    // Check labeling
    composeTestRule.onNodeWithTag("submit_button")
        .assertContentDescriptionEquals("Submit order")
    // Check traversal order
    composeTestRule.onAllNodesWithTag("list_item")
        .assertCountEquals(expectedCount)
}
```

Enable the Compose a11y inspector overlay on device: Developer options > Accessibility > Enable accessibility features > TalkBack, then verify reading order and labels match the design spec.

---

## Design-time checklist (pass/fail)

Work through this for every new screen or component. A single FAIL blocks handoff.

```
Contrast
[ ] Normal text (< 18 pt / < 14 pt bold): 4.5:1 vs. background         SC 1.4.3
[ ] Large text (>= 18 pt / >= 14 pt bold): 3:1 vs. background           SC 1.4.3
[ ] UI chrome (borders, icons, input outlines): 3:1 vs. adjacent         SC 1.4.11

Color not alone
[ ] Every state (error, success, disabled, selected) uses icon/shape/
    label in addition to color                                            SC 1.4.1

Target size
[ ] Web: pointer target >= 24x24 CSS px or >= 24 px offset spacing       SC 2.5.8
[ ] iOS: tap target >= 44x44 pt (Apple HIG; exceeds WCAG minimum)        SC 2.5.8
[ ] Android: touch target >= 48x48 dp (Material 3)                       SC 2.5.8

Focus
[ ] Focus indicator visible; aim for >= 2 px perimeter, >= 3:1 contrast  SC 2.4.7 / 2.4.13
[ ] Focused element not fully hidden by sticky header/sheet/toast         SC 2.4.11
[ ] Tab / VoiceOver / TalkBack order matches visual reading order         SC 2.4.3

Motion
[ ] Animations have a no-motion fallback                                  SC 2.3.3 (AAA), platform HIG
[ ] No content flashes > 3 Hz                                            SC 2.3.1

Gestures
[ ] Every drag/swipe has a single-tap alternative                         SC 2.5.7

Auth / forms
[ ] Multi-step forms do not re-ask for data already given in this session SC 3.3.7
[ ] Login does not require cognitive test (CAPTCHA/puzzle) without
    an accessible alternative                                             SC 3.3.8
[ ] Help mechanism appears in a consistent position across screens        SC 3.2.6

Structure
[ ] Heading hierarchy is logical; regions are labeled                     SC 1.3.1
[ ] Instructions do not rely on shape, color, size, position alone       SC 1.3.3
```

Record each item as PASS / FAIL / N/A with a brief note. Do not mark PASS without evidence (tool output, design token value, or a measured ratio).

---

## Per-platform binding notes (three most-failed criteria)

### 2.4.13 Focus Appearance (aim for AAA)

- **Web:** CSS `:focus-visible` outline, min `2px solid`, offset `2px`; test with `axe` rule `focus-visible` + manual keyboard walk.
- **iOS:** SwiftUI has no direct focus ring; use `.accessibilityFocused(_:)` + a custom overlay in `ZStack` for custom UI. UIKit: override `drawFocusEffect(in:with:)`.
- **Android:** Compose `Indication` / `BorderStroke` in `focusedBorder`; XML: `android:state_focused` drawable selector with a visible ring.

### 2.5.8 Target Size (Minimum) -- 24 px web / 48 dp mobile

- **Web:** `min-width: 24px; min-height: 24px` or add invisible padding. Icon-only buttons need `padding: 8px` minimum around the 8 px icon.
- **iOS:** Wrap controls in `.frame(minWidth: 44, minHeight: 44)`; use `.contentShape(Rectangle())` to expand the hit area without changing visual size.
- **Android:** `minWidth="48dp"` and `minHeight="48dp"` on `MaterialButton`; Compose: `Modifier.sizeIn(minWidth = 48.dp, minHeight = 48.dp)`.

### 2.4.11 Focus Not Obscured (Minimum)

Check `position: sticky` / `position: fixed` headers, bottom sheets, snackbars, and cookie banners. Ensure `scroll-margin-top` / `scroll-padding-top` compensates for fixed elements. Test by tabbing to each interactive element with keyboard only.
