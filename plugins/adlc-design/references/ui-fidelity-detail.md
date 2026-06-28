<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
Consumed by the `ui-fidelity` skill. Load on demand; do not load independently.

This is the measurement spec behind the PASS / FAIL verdict in `ui-fidelity` Step 5. The
skill says "measure first, screenshot second"; this file says exactly what to measure,
with what tolerance, on what pinned environment, through which native API. Design truth
(values + bound token names + baseline image) comes from `figma-extract`; the fix loop
hands deltas back to `figma-implement`.

---

## 1. Tolerance table (the verdict's pass band)

The verdict compares each measured property against the Figma value. A property is PASS
only if it lands inside its band below. Anything outside is a FAIL with a numeric delta.

| Property | Tolerance | Notes |
| --- | --- | --- |
| Width / height (fixed) | +/-1px | After px->dp/pt conversion at the pinned density (section 6). |
| Width / height (fluid) | +/-2% of the rendered axis | Use for fill / percentage / flex tracks where 1px is noise. |
| Spacing (padding, gap, margin) | +/-1px | Per edge; do not average four edges into one number. |
| Position (x / y in root) | +/-1px | Same coordinate space as the Figma frame origin. |
| Font size | exact | No band. `16px` vs `15px` is a FAIL. |
| Font weight | exact | `600` vs `500` is a FAIL. Numeric weight, not the family name. |
| Line height | +/-1px | Computed used value, not the unitless ratio. |
| Corner radius | +/-1px | Per corner if the design sets per-corner radii. |
| Color (fill, stroke, text) | exact token match | No deltaE slack. The rendered value must equal the Figma value AND reference the expected token (section 4). A hardcoded hex that matches by eye is a high-severity FAIL. |
| Border width | +/-1px | |
| Opacity | +/-0.01 | |
| Shadow (offset / blur / spread) | +/-1px each | Color of the shadow follows the color rule above. |

Why so tight: sub-pixel and rendering noise is handled by the density conversion and the
documented epsilon in section 6, not by loosening the band. A wide band hides real drift.
The "exact" rows are categorical (a token, a weight, a size step), so a band is meaningless.

The FAIL line emitted per mismatch: `severity | property | measured vs expected (delta) |
path:line | suggested edit`. Example: `high | font-weight | 500 vs 600 | Button.tsx:42 |
change font-weight token from weight.medium to weight.semibold`.

---

## 2. Per-platform determinism pin

A fidelity run is only reproducible if the render environment is frozen. Pin all of the
following before the first measurement; record the pin in the verdict so a re-run matches.

### Web (via the preview MCP)

```js
// preview_eval: assert the pinned environment, fail the run if it drifts
({
  dpr: window.devicePixelRatio,                 // pin to 1 for measurement
  width: window.innerWidth,                      // fixed viewport, e.g. 1440
  height: window.innerHeight,                    // fixed viewport, e.g. 900
  reducedMotion: matchMedia('(prefers-reduced-motion: reduce)').matches,
})
```

- Fixed viewport: drive `preview_resize` to the design's target width(s) (section 5); never measure at a floating window size.
- `devicePixelRatio = 1` for the measurement pass so `getBoundingClientRect()` returns CSS px 1:1. Run the screenshot pass separately at the device DPR if you need a retina baseline.
- Animations / transitions off: inject `* { animation: none !important; transition: none !important; scroll-behavior: auto !important; }` and run with `prefers-reduced-motion: reduce`. Measure only after layout settles (await fonts, section 7).
- Pinned font stack: load the exact design fonts (self-host or `document.fonts.ready`); do not let a system fallback render the measured pass. A different fallback shifts every text metric.

### Android (emulator AVD)

```bash
# Pin a known AVD: fixed screen density (dpi) baked into the AVD config.
# Force density at runtime if needed (560 = xxxhdpi example; match the design target):
adb shell wm density 560
adb shell wm size 1440x3120

# Disable all three animation scales (flake + timing noise):
adb shell settings put global window_animation_scale 0
adb shell settings put global transition_animation_scale 0
adb shell settings put global animator_duration_scale 0

# Pin font scale and locale so text metrics and layout are deterministic:
adb shell settings put system font_scale 1.0
adb shell cmd locale set-app-locales <app.package.id> --locales en-US
```

- Density is the conversion constant for section 6; read it back with `adb shell wm density` and use that exact value.
- `font_scale 1.0` is mandatory: any other value rescales every sp dimension and breaks the font-size assertion.
- Prefer `testOptions { animationsDisabled = true }` in Gradle for instrumented runs as a belt-and-suspenders alongside the adb scales.

### iOS (named simulator)

```bash
# Pin a specific simulator by name/UDID so scale and metrics are fixed:
xcrun simctl boot "iPhone 15 Pro"

# Pin Dynamic Type to a known content size category (default is "large").
# Via the launch environment in the UI-test scheme / XCUIApplication:
#   app.launchArguments += ["-UIPreferredContentSizeCategoryName", "UICTContentSizeCategoryL"]
# Or set Reduce Motion for the screenshot pass:
xcrun simctl ui booted increase_contrast disabled
```

- Fixed Dynamic Type: pin one content size category (default `UICTContentSizeCategoryL`); do not measure at the system slider's last position. iOS has no first-class `simctl` flag for content size, so set it through the app's launch environment / `UITraitCollection` override and assert it in-test.
- The simulator's `scale` (points->pixels) is the conversion constant for section 6; read `UIScreen.main.scale`.
- Disable motion for the screenshot pass via Environment Overrides or the simctl ui flag; the layout-frame measurement does not depend on motion but the holistic diff does.

---

## 3. The native measurement path (honest)

Measure the *rendered node*, not the source. Each platform exposes a real geometry API.
Where none exists, scope down to screenshot + accessibility-tree assertion and say so in
the verdict; do not claim a precision you cannot deliver.

### Web: `getBoundingClientRect()` + `getComputedStyle()` via `preview_eval`

```js
// preview_eval: geometry + computed style for one node
(() => {
  const el = document.querySelector('[data-testid="primary-cta"]');
  const r = el.getBoundingClientRect();           // CSS px, viewport-relative
  const s = getComputedStyle(el);
  return {
    x: r.x, y: r.y, width: r.width, height: r.height,
    paddingTop: s.paddingTop, paddingLeft: s.paddingLeft,
    fontSize: s.fontSize, fontWeight: s.fontWeight, lineHeight: s.lineHeight,
    borderRadius: s.borderTopLeftRadius,
    color: s.color, background: s.backgroundColor,  // rgb(...): normalize before compare
  };
})()
```

`getBoundingClientRect()` gives geometry; `getComputedStyle()` gives the resolved style
(font, color, radius, spacing). Normalize colors to one form (e.g. `rgb()` -> hex) before
the exact compare.

### Android: Compose semantics bounds (debug build) or UIAutomator

Preferred, in an instrumented test against the running screen (nodes need a `testTag`; see
the `android-automation-tags` skill):

```kotlin
// Bounds come back in Dp already: no manual px->dp needed.
composeTestRule.onNodeWithTag("primaryCta")
    .assertWidthIsEqualTo(320.dp)                 // throws on > 0.5px rounding miss
    .assertHeightIsEqualTo(48.dp)
    .assertPositionInRootIsEqualTo(expectedLeft = 16.dp, expectedTop = 220.dp)

// Or read the rect for a numeric delta instead of a hard assert:
val bounds: DpRect = composeTestRule.onNodeWithTag("primaryCta").getUnclippedBoundsInRoot()
// bounds.left / top / width / height are Dp. Dump the whole tree to discover nodes:
composeTestRule.onRoot(useUnmergedTree = true).printToLog("FIDELITY")
```

`assertWidthIsEqualTo`, `assertHeightIsEqualTo`, and `assertPositionInRootIsEqualTo` all
take `Dp`; `getUnclippedBoundsInRoot()` / `getBoundsInRoot()` return a `DpRect`. Use
`getUnclippedBoundsInRoot()` when the node is clipped and you still want its laid-out size.
For a non-test debug dump or a View-based screen, `Modifier.onGloballyPositioned { it.size /
it.boundsInWindow() }` returns pixels (convert per section 6), or use UIAutomator
`UiObject2.getVisibleBounds()` (a pixel `Rect`).

Color / font-weight / radius are not in the Compose bounds API; assert those at the source
(section 4), not from the compiled UI.

### iOS: accessibility / layout frame

```swift
// In a UI-test target. frame is a CGRect in POINTS, screen-relative.
let cta = app.buttons["primaryCta"]
let f = cta.frame                                  // CGRect in points
XCTAssertEqual(f.width, 320, accuracy: 1.0)        // points; tolerance per section 1
XCTAssertEqual(f.minX, 16, accuracy: 1.0)
// Cache the snapshot once; each property read re-snapshots and is slow.
```

`XCUIElement.frame` (and `NSObject.accessibilityFrame` for the a11y rect) returns a
`CGRect` in **points**, screen-relative. Convert design px to points with
`UIScreen.main.scale` (section 6). Font / color are not exposed on the frame; assert those
at the source.

### No native measure path -> scope honestly

If the surface cannot be driven by a real geometry API (a canvas/WebGL render, a screen the
harness cannot reach, a platform without test bounds), do NOT fake px deltas. Drop to:
1. a screenshot diff against the dated `figma-extract` baseline (composition only), and
2. an accessibility-tree assertion (the expected nodes / labels / states exist),

and record in the verdict that geometry was screenshot-scoped, not measured. An honest
"composition-only" verdict beats a fabricated pixel number.

---

## 4. Token compliance is a SOURCE check, not a runtime check

A compiled native binary (an APK, an `.app`) carries resolved values, not token
references. You cannot prove from the rendered pixel that `#0A84FF` came from
`color.accent` rather than a hardcoded literal. So token compliance is checked at the
source line bound to the node, delegated to `design-system-audit`:

```bash
# The node measured at Button.tsx:42: does that line reference a token symbol,
# or a raw literal? Raw literal = high-severity FAIL.
grep -nE '#[0-9a-fA-F]{3,8}|rgb\(|Color\(0x|\b[0-9]+\.dp\b|\b[0-9]+sp\b|: ?[0-9]+px' \
  path/to/Button.tsx | grep -v 'tokens\.|theme\.|MaterialTheme|var(--'
```

- Web: the bound value must read `var(--color-accent)` / a theme token, not `#0A84FF`.
- Compose: `MaterialTheme.colorScheme.primary` / a token object, not `Color(0xFF0A84FF)` or a bare `16.dp` where a spacing token exists.
- SwiftUI: `Color("accent")` / a token enum, not `Color(red:..., green:..., blue:...)`.

Hand the path:line list to `design-system-audit`; it owns the inventory of valid token
symbols and returns the per-line compliance verdict. `ui-fidelity` records it as a FAIL row.

Correction to retire: do **not** claim that a successful light/dark mode switch "proves
tokens were referenced." A mode switch only proves the build is **mode-responsive**: a
component can hardcode two literals behind an `if (isDark)` and switch correctly while
referencing no token at all. Mode-switching is its own assertion (the build follows the
mode); token *reference* is the grep above. Keep them separate.

---

## 5. Two-width responsive assertion

Render the surface at the design's **min** and **max** target widths and assert each node's
resize behavior matches its Figma intent (Fill / Fixed / Hug, captured by `figma-extract`).
Measuring the rendered result at two widths is what catches a fixed px where the design
meant fill.

```js
// Web: measure the same node at both widths, derive the deltas.
// 1) preview_resize -> W_min ; eval the node + container widths
// 2) preview_resize -> W_max ; eval again
// containerDelta = container@max - container@min
//   Fill node:  (node@max - node@min)  ≈ containerDelta      (tracks the container)
//   Fixed node: (node@max - node@min)  ≈ 0                    (invariant, within +/-1px)
//   Hug node:   node width ≈ content width at BOTH widths     (tracks its content)
```

| Figma resize | Assertion across [min, max] | FAIL signal |
| --- | --- | --- |
| Fill | node width delta tracks container delta (+/-2%) | node width is constant -> a fixed px leaked in |
| Fixed | node width invariant (+/-1px) | node width grew -> intent lost, it stretched |
| Hug | node width == content width at each stop | node wider than content -> it filled instead of hugging |

Android: re-measure with two AVD widths (`adb shell wm size`) or a resizable / foldable
config and apply the same deltas to the `DpRect` widths. iOS: two device sizes / orientations
and the same deltas on `frame.width`. Assert the *measured* result, not the code shape:
idiomatic `fill` / `match_parent` / `100%` is correct even though Figma stored a fixed px,
that is the whole point of capturing intent in `figma-extract`.

---

## 6. Native false-FAIL guards

Most "FAIL" noise on native is a unit or inset mismatch, not real drift. Apply all three
before emitting a delta:

1. **Convert design px to the platform unit at the pinned density, then compare.**
   - Android: `dp = px / (densityDpi / 160)`. At `densityDpi = 560`, `density = 3.5`, so a 56px Figma value is `56 / 3.5 = 16dp`. Compose bounds are already Dp, so compare Dp to (designPx / density). UIAutomator / `onGloballyPositioned` give px, so divide first.
   - iOS: `points = px / UIScreen.main.scale`. At `scale = 3`, a 48px Figma value is `48 / 3 = 16pt`. `frame` is in points, so compare points to (designPx / scale).
   - Web at DPR 1: CSS px == design px, no conversion. Do not also divide.

2. **Allow a documented sub-pixel epsilon.** Layout rounds to the device grid. Use
   `epsilon = 0.5px` (or `0.5 / density` dp) on top of the section-1 band, and write the
   epsilon into the verdict. Compose's own `assert*IsEqualTo` already rounds to the nearest
   pixel; do not stack a second rounding on top.

3. **Exclude platform-default insets that are not part of the design value.**
   - Android: Compose `BasicText` / `Text` adds default font padding. Compare the text *box* the design specifies; either disable it (`PlatformTextStyle(includeFontPadding = false)` / `LineHeightStyle`) before measuring or subtract it. Buttons / touch targets are auto-expanded to the 48dp minimum tap target, that expansion is correct and must not be measured against a smaller visual Figma frame; measure the visual bounds, assert the tap target separately.
   - iOS: the 44pt minimum tap target and `UIButton` content insets are platform defaults, not design drift. Measure the visual frame; assert the 44pt target as a separate a11y check, not a fidelity FAIL.

A delta that survives all three guards is real. One that vanishes after them was a unit bug.

---

## 7. CLS / font-loading gate (web)

A screen can measure pass at rest and still ship a visible jump as fonts and media load.
Gate on it.

**Metric-matched fallback so the swap does not reflow.** Pair `font-display: swap` with a
fallback `@font-face` whose metrics are overridden to match the web font (values from a tool
like Capsize / Fontaine):

```css
@font-face {
  font-family: "Inter";
  src: url("/fonts/inter.woff2") format("woff2");
  font-display: swap;                 /* show fallback immediately, swap when loaded */
}
/* Metric-matched fallback: same box as Inter, so the swap is invisible. */
@font-face {
  font-family: "Inter-fallback";
  src: local("Arial");
  size-adjust: 107%;                  /* match advance width */
  ascent-override: 90%;
  descent-override: 22%;
  line-gap-override: 0%;
}
body { font-family: "Inter", "Inter-fallback", sans-serif; }
```

**Reserve intrinsic media dimensions** so images / video / embeds do not push content when
they load: set `width` + `height` attributes (or `aspect-ratio` in CSS) on every replaced
element. An unsized image is the most common CLS source after fonts.

**Capture CLS during the fidelity run** and gate it:

```js
// preview_eval: sum layout-shift entries that were NOT user-initiated.
(() => {
  let cls = 0;
  new PerformanceObserver((list) => {
    for (const e of list.getEntries()) {
      if (!e.hadRecentInput) cls += e.value;      // ignore shifts after real input
    }
  }).observe({ type: 'layout-shift', buffered: true });
  return new Promise((r) => setTimeout(() => r({ cls }), 1500));
})()
```

| CLS | Verdict |
| --- | --- |
| <= 0.1 | PASS |
| 0.1 - 0.25 | WARN (needs improvement) |
| > 0.25 | FAIL (poor) |

A CLS FAIL routes the same as a geometry FAIL: deltas + `path:line` back to
`figma-implement` (add the fallback metrics, size the media), then re-verify.

---

## References

- Design truth (values + bound tokens + baseline image): `figma-extract`.
- Build + fix loop (edit nodes, do not regenerate): `figma-implement`.
- Token-symbol inventory + per-line compliance: `design-system-audit`, `design-tokens`.
- `testTag` / semantics wiring for native measurement: `android-automation-tags`.
- A11y smoke gate (tap targets, focus order): `design-a11y`.
- Compose bounds assertions: https://developer.android.com/develop/ui/compose/testing-cheatsheet
- CLS measurement + thresholds: https://web.dev/articles/cls
