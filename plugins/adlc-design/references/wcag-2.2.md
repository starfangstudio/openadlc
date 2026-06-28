<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
# WCAG 2.2 / ISO 40500:2025 -- Design-time reference

WCAG 2.2 was published October 5, 2023 and ratified as ISO/IEC 40500:2025
on October 21, 2025. It is backwards-compatible with WCAG 2.1. The legal bar
for most jurisdictions (EU EAA June 2025, US ADA/508 guidance, UK PSBAR) is
**Level AA**.

---

## New success criteria in WCAG 2.2

Nine criteria were added. Level AA items are the compliance bar.

### Level A (new)

| SC | Name | Short rule |
|---|---|---|
| 3.2.6 | Consistent Help | Help mechanisms appear in the same relative order on every page/screen they repeat. |
| 3.3.7 | Redundant Entry | Do not ask the user for the same information twice in one process; auto-populate or offer selection. |

### Level AA (new -- the compliance bar)

| SC | Name | Short rule |
|---|---|---|
| 2.4.11 | Focus Not Obscured (Minimum) | When a component receives focus, it is not *entirely* hidden by sticky headers, overlays, or other author content. |
| 2.5.7 | Dragging Movements | Every drag interaction has a single-pointer alternative (e.g. tap + tap, not only swipe-to-reorder). |
| 2.5.8 | Target Size (Minimum) | Pointer targets are at least 24x24 CSS px, or have 24 px of offset spacing from every adjacent target. |
| 3.3.8 | Accessible Authentication (Minimum) | Authentication must not require solving a cognitive test (CAPTCHA, puzzle) unless an alternative is provided. |

### Level AAA (new -- aspirational)

| SC | Name | Short rule |
|---|---|---|
| 2.4.12 | Focus Not Obscured (Enhanced) | Focus indicator is *never* hidden -- not even partially. |
| 2.4.13 | Focus Appearance | Focus ring: >= 2 px perimeter, >= 3:1 contrast vs. unfocused pixels, not just color. |
| 3.3.9 | Accessible Authentication (Enhanced) | No cognitive test at all, even with alternative. |

---

## Carry-over criteria most often failed in design

These are pre-2.2 criteria that regularly appear in audit findings.

| SC | Level | Rule |
|---|---|---|
| 1.4.3 Contrast (Minimum) | AA | Text < 18 pt: 4.5:1. Text >= 18 pt or bold >= 14 pt: 3:1. |
| 1.4.6 Contrast (Enhanced) | AAA | 7:1 / 4.5:1 respectively. |
| 1.4.11 Non-text Contrast | AA | UI component boundaries and state indicators: 3:1 vs. adjacent color. |
| 1.4.1 Use of Color | A | Color must not be the *only* means to convey information or a state. |
| 1.3.1 Info and Relationships | A | Structure conveyed visually (heading, list, table) must be programmatic (role/semantics). |
| 1.3.3 Sensory Characteristics | A | Instructions must not rely solely on shape, color, size, location, or sound. |
| 2.1.1 Keyboard | A | All functionality operable by keyboard; no keyboard trap. |
| 2.4.3 Focus Order | A | Focus order preserves meaning and operability. |
| 2.4.7 Focus Visible | AA | Keyboard focus indicator is visible (2.2 raises this to 2.4.11/13). |
| 1.4.10 Reflow | AA | Content reflows at 320 CSS px viewport without horizontal scroll (mobile-proxy). |
| 1.4.12 Text Spacing | AA | No loss of content when line-height >= 1.5x, letter-spacing >= 0.12em, word-spacing >= 0.16em. |
| 1.4.13 Content on Hover/Focus | AA | Hover/focus-revealed content: dismissable, hoverable, persistent. |

---

## Mobile platform notes (not in WCAG text -- design-time mapping)

WCAG is technology-neutral but mobile platforms map as follows:

| Criterion | iOS (SwiftUI/UIKit) | Android (Compose/XML) |
|---|---|---|
| Target size 2.5.8 (24 px CSS equiv.) | Apple HIG: 44x44 pt minimum tap target | Material 3: 48x48 dp minimum touch target |
| Focus/keyboard order 2.4.3 | `accessibilityActivationPoint`, VoiceOver reading order (frame-based then explicit) | `semantics { traversalIndex }`, TalkBack reading order |
| Color not alone 1.4.1 | Pair color with shape, icon, or label in every state indicator | Same; use `semantics { stateDescription }` for programmatic state |
| Reduced motion | `@Environment(\.accessibilityReduceMotion)` | `LocalReduceMotionEnabled` / `WindowManager.isReduceMotionEnabled()` |
| Non-text contrast 1.4.11 | Button borders, icon strokes, input field outlines >= 3:1 | Same; verify in dark/light + high-contrast mode |

---

## Design-time checklist (pass/fail)

Run this before marking any design component or screen ready for dev handoff.

```
[ ] Contrast: text 4.5:1 (< 18 pt) / 3:1 (>= 18 pt bold); UI chrome 3:1 non-text
[ ] Color not alone: every state (error, success, disabled, active) uses icon/shape/label + color
[ ] Target size: web >= 24x24 CSS px with 24 px spacing; iOS >= 44x44 pt; Android >= 48x48 dp
[ ] Focus indicator: visible, >= 2 px perimeter, >= 3:1 contrast vs. unfocused (aim for AAA 2.4.13)
[ ] Focus not obscured: sticky nav / bottom sheet / toast never fully covers the focused element
[ ] Keyboard / reading order: tab/swipe order matches visual top-to-bottom, left-to-right flow
[ ] Reduced motion: animations have a no-motion fallback; no flashing > 3 Hz
[ ] Touch gestures: every drag/swipe has a tap-based alternative
[ ] Auth: no CAPTCHA or puzzle without an accessible alternative
[ ] Redundant entry: multi-step forms do not re-ask for data already provided
```

---

## References

- W3C WCAG 2.2 specification: https://www.w3.org/TR/WCAG22/
- ISO/IEC 40500:2025 announcement: https://www.iso.org/standard/91029.html
- W3C "What's new in WCAG 2.2": https://www.w3.org/WAI/standards-guidelines/wcag/new-in-22/
- Deque WCAG 2.2 resources: https://dequeuniversity.com/resources/wcag-2.2/
- Apple HIG -- Accessibility: https://developer.apple.com/design/human-interface-guidelines/accessibility
- Material 3 -- Accessibility: https://m3.material.io/foundations/accessible-design/overview
- axe-core rules: https://github.com/dequelabs/axe-core/blob/develop/doc/rule-descriptions.md
