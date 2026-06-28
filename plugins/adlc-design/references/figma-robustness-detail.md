<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
Consumed by the `figma-implement` and `ui-fidelity` skills. Load on demand; do not load
independently.

These are the real-world clauses a Figma design never shows you. A static frame is one
string, one language, one closed state, one screenshot, at one row count. Production is
the German plural, the Arabic mirror, the open modal over a scrolled list, the 5000-row
feed. The implementer builds for these; `ui-fidelity` asserts them. "Looks right in the
happy frame" is not a passing bar.

## 1. Localization / text robustness

A Figma frame shows one string at one length. Translation expands it (English -> German
~+35%, Finnish/Russian longer; short labels can double). Build for the worst case, not
the mock string.

### Build inputs (use these, not the Figma string)
- **Pseudo-localize** every visible string while building. It accents, expands, and
  brackets text so truncation, clipping, and concatenation bugs surface before translation.

| Platform | How to turn it on |
|---|---|
| Android | `android { buildTypes { debug { isPseudoLocalesEnabled = true } } }`, then Settings > System > Languages, add **English (XA)** (accent + expand) and **Arabic (XB)** (RTL mirror). Needs API 18+ and a reboot after enabling Developer options. |
| Web | `pseudo-localization` npm pkg (`pseudoLocalization.start()` in dev) or the PseudoLocalizer Chrome extension; or load a generated `xx-pseudo` locale in your i18n setup (i18next/Lingui `pseudoLocale`). |
| iOS | Xcode scheme > Run > Options > App Language = **Double-Length Pseudolanguage** and **Right-to-Left Pseudolanguage**. |

- **Longest-known string:** also build with the longest real value the field can hold
  (the longest product name, the 2-line user name, the currency with the most digits).
  Cite the source of the longest string in the slice notes.

### Layout rules so expansion does not break the box
- **Flex children must get `min-width: 0`** (and `min-height: 0` for column flex). A flex
  item defaults to `min-width: auto`, which refuses to shrink below its content, so a long
  word blows the row out and breaks sibling truncation. The text child that truncates needs
  `min-width: 0` on itself AND on every flex ancestor between it and the flex container.

```css
.row { display: flex; gap: 8px; }
.row > .label { min-width: 0; }          /* without this, truncation below silently fails */
.row > .label > .text {
  min-width: 0;
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;  /* single-line truncate */
}
```

- **Truncate vs wrap is an explicit decision, cited per text node.** Never leave it to
  the default. State which and why in the slice notes (e.g. "title: truncate 1 line, full
  value in `title` attr / accessibilityLabel; description: wrap to 3 lines then clamp").

| Intent | Web | Compose | SwiftUI |
|---|---|---|---|
| Truncate 1 line | `white-space:nowrap; overflow:hidden; text-overflow:ellipsis` | `maxLines = 1, overflow = TextOverflow.Ellipsis` | `.lineLimit(1).truncationMode(.tail)` |
| Clamp to N lines | `display:-webkit-box; -webkit-line-clamp:N; -webkit-box-orient:vertical; overflow:hidden` | `maxLines = N, overflow = TextOverflow.Ellipsis` | `.lineLimit(N)` |
| Wrap, no clamp | (default) `overflow-wrap:break-word` | (default) `softWrap = true` | (default) `.fixedSize(horizontal:false, vertical:true)` to let it grow |

  Truncated text MUST still expose the full value to accessibility (web: `title`; Compose:
  `Modifier.semantics { contentDescription = full }`; SwiftUI: `.accessibilityLabel(full)`).

### Direction-aware (no hardcoded left/right)
- **Web: use logical properties, never physical ones.** They flip automatically under
  `dir="rtl"`. Flexbox and Grid are already flow-relative (`justify-content`,
  `inset-inline`), so they flip too.

| Physical (do not use) | Logical (use) |
|---|---|
| `margin-left` / `margin-right` | `margin-inline-start` / `margin-inline-end` |
| `padding-left` / `padding-right` | `padding-inline-start` / `padding-inline-end` |
| `left` / `right` | `inset-inline-start` / `inset-inline-end` |
| `border-left` | `border-inline-start` |
| `text-align: left` | `text-align: start` |

  Shorthands: `margin-inline: 8px 16px` (start end), `padding-block` for top/bottom.
  Supported in all major browsers since 2021. Set `dir` on `<html>` from the locale.

- **Compose:** lay out with start/end, not left/right. `PaddingValues(start =, end =)`,
  `Arrangement.Start`, `Alignment.Start` all honor `LocalLayoutDirection`. Use
  `Icons.AutoMirrored.*` (e.g. `Icons.AutoMirrored.Filled.ArrowBack`) for directional
  icons so they mirror in RTL. Test by wrapping a preview in
  `CompositionLocalProvider(LocalLayoutDirection provides LayoutDirection.Rtl)`.
- **SwiftUI:** use leading/trailing edges, never `.leading`-as-left assumptions; SwiftUI
  mirrors automatically. Force-test with `.environment(\.layoutDirection, .rightToLeft)`.
  Add `.flipsForRightToLeftLayoutDirection(true)` to images that encode direction (a back
  chevron); leave it off for content that must not mirror (a logo, a play button).

### Things that must NOT mirror in RTL
Logos, brand marks, media-transport icons (play/pause/forward), phone numbers, code,
charts whose axis is semantic. Mirror navigation/progress/directional affordances; keep
content-meaning glyphs as-is.

## 2. Motion

A Figma file carries interactions: prototype connections with **transition** type,
duration, easing, and **Smart Animate** between variants. Read them; do not invent motion,
and do not drop it.

### Read the motion from Figma
- REST: `GET /v1/files/:key/nodes?ids=:id` -> on a node, `transitionNodeID`,
  `transitionDuration` (ms), `transitionEasing`; prototype flows live under
  `prototypeStartNodeID` / interaction objects.
- MCP: `get_design_context` surfaces interaction intent; `get_metadata` for the node map.
  Smart-animate between component variants = a state transition you must implement (the two
  variants are the from/to keyframes).

### Implement with the project's motion tokens, never magic numbers
Bind to the `motion` tokens from `design-tokens` (duration + easing), the same way color
binds to color tokens. A hardcoded `300ms ease-in-out` is the motion equivalent of a
hardcoded hex: a FAIL.

| Transition kind | Web | Compose | SwiftUI |
|---|---|---|---|
| Enter / exit (mount) | `@keyframes` + class toggle, or Web Animations API | `AnimatedVisibility(enter = fadeIn()+expandVertically(), exit = ...)` | `.transition(.opacity.combined(with:.scale))` on conditional view |
| State / value change | `transition: <prop> var(--motion-duration) var(--motion-easing)` | `animate*AsState(animationSpec = tween(durationToken, easing = token))` | `withAnimation(.easeInOut(duration: token)) { state = ... }` |
| Layout size change | `transition: all` (avoid; animate specific props) | `Modifier.animateContentSize()` (place BEFORE `size`/`defaultMinSize` in the chain) | `.animation(.default, value:)` on the sized view |
| List item add/remove | FLIP / View Transitions API | `Modifier.animateItem()` in `LazyColumn` | `.animation` on `ForEach` with stable `id` |

### Always ship a reduced-motion path (non-negotiable)
Vestibular triggers; this is WCAG 2.3.3. Disable or replace non-essential motion when the
OS preference is set. Keep an opacity cross-fade (safe) instead of large translate/scale.

```css
/* Web: guard, never assume motion is welcome */
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: .01ms !important; animation-iteration-count: 1 !important;
    transition-duration: .01ms !important; scroll-behavior: auto !important;
  }
}
```
- **Compose:** read the system setting and branch the spec:
  `Settings.Global.getFloat(context.contentResolver, Settings.Global.ANIMATOR_DURATION_SCALE, 1f) == 0f`
  (also covers Battery Saver), or `ValueAnimator.areAnimatorsEnabled()`; when reduced, use
  `snap()` or a short `tween` with no large translate/scale.
- **SwiftUI:** `@Environment(\.accessibilityReduceMotion) var reduceMotion`; gate the
  animation: `withAnimation(reduceMotion ? nil : .easeInOut(duration: token)) { ... }`,
  or swap a slide for a cross-fade.

### How `ui-fidelity` verifies motion (not a single screenshot)
Motion is invisible in one frame. The check captures the **sequence**, not a still:
- Trigger the interaction (`preview_eval`/`preview_click`), then capture before -> mid ->
  after frames (or record), and assert the **end state** matches the target variant AND
  that a transition occurred (intermediate frame differs from both ends).
- Assert the **duration/easing reference the motion token**, not a literal (read
  `getComputedStyle(el).transitionDuration` / inspect the `AnimationSpec`).
- Re-run with reduced-motion forced (Chrome DevTools Rendering tab >
  "prefers-reduced-motion: reduce"; Compose/SwiftUI: set the env/setting) and assert the
  large-motion path is gone (end state still correct, no long translate/scale). A missing
  reduced-motion path is a FAIL.

## 3. Overlays, scroll & stacking

Modals, menus, sheets, toasts, tooltips, dropdowns. The single most common production bug:
the overlay is clipped or buried by an ancestor. Figma draws it floating at the top of the
canvas; the DOM/view tree puts it inside a card with `overflow: hidden`.

### Escape the ancestor (clipping + stacking)
- **Two independent traps:** (a) an ancestor `overflow: hidden|auto|clip|scroll` **clips**
  the overlay; (b) an ancestor that forms a **stacking context** (`transform`, `opacity<1`,
  `filter`, `will-change`, `position` + `z-index`, `isolation:isolate`) **caps** its
  z-index. A bigger `z-index` cannot escape a parent stacking context; even `position:fixed`
  is trapped by an ancestor `transform`. Both require leaving the subtree.
- **Web fix, in order of preference:**
  1. Native top layer: `<dialog>.showModal()` and the Popover API (`popover` attr +
     `popovertarget`) render in the browser **top layer**, above everything, no z-index war,
     with backdrop and focus handling for `<dialog>`. Prefer these.
  2. Portal: `ReactDOM.createPortal(node, document.body)` (or a dedicated `#overlay-root`)
     to render outside the clipping/stacking subtree while keeping React context. Pair with
     a positioning lib (Floating UI) for menus/tooltips anchored to a trigger.
- **Compose:** `Dialog`, `ModalBottomSheet`, `DropdownMenu`, and `Popup` already render in a
  separate window/layer above the composition; do not fake an overlay with a `Box` z-index.
- **SwiftUI:** `.sheet`, `.fullScreenCover`, `.popover`, `.alert`, `.confirmationDialog`
  present above the view tree; do not hand-roll with `zIndex` inside a clipped container.

### Safe-area insets (overlays especially)
A bottom sheet, toast, or sticky footer must not sit under the notch, home indicator, or
status bar.

| Platform | Inset source |
|---|---|
| Web | `env(safe-area-inset-top/right/bottom/left)` in padding/margin; REQUIRES `<meta name="viewport" content="viewport-fit=cover">` or the env values are 0. |
| Compose | `Modifier.windowInsetsPadding(WindowInsets.safeDrawing)` (or `.systemBars`, `.ime`, `.navigationBars`); enable edge-to-edge with `enableEdgeToEdge()`. |
| SwiftUI | safe area is respected by default; read via `GeometryReader { $0.safeAreaInsets }`, extend deliberately with `.ignoresSafeArea()` + re-inset with `.safeAreaInset(edge:)`. |

### How `ui-fidelity` verifies overlays & scroll (not the initial frame)
- **Render the OPEN overlay and measure it.** Trigger the open, wait for it, then
  `getBoundingClientRect()`/`getComputedStyle()` on the overlay and its backdrop: position,
  size, elevation/shadow, that it is on top (hit-test the center point returns the overlay),
  and that it is NOT clipped (bounds not constrained by an ancestor). Assert focus moved in
  and Escape/scrim-tap closes it.
- **Render the scrolled-past-sticky state.** Scroll the container past a sticky/pinned
  header (`preview_eval`: `el.scrollTo(0, N)`), then screenshot + measure: the sticky
  element is still pinned at its edge, content scrolls under it, no z-index bleed-through,
  no double scrollbars. The initial unscrolled frame proves nothing about either of these.

## 4. Performance / render cost

A 12-row Figma mock hides what 5000 rows do. Build lists for growth and keep the tree
shallow, or the screen jank-stutters on real data.

### Virtualize anything that can grow
Render only the visible window (plus a small buffer), not the whole collection.

| Platform | Use | Not |
|---|---|---|
| Web (React) | `react-window` (`FixedSizeList` / `VariableSizeList`), or TanStack Virtual | mapping the full array into the DOM |
| Web (no lib) | `content-visibility: auto` + `contain-intrinsic-size` to skip offscreen render/paint | rendering everything eagerly |
| Compose | `LazyColumn` / `LazyRow` / `LazyVerticalGrid` with stable `key =` | `Column { items.forEach { } }` inside a `verticalScroll` |
| SwiftUI | `List` (cell-recycling) or `LazyVStack`/`LazyVGrid` in a `ScrollView` | a plain `VStack` of all rows |

### Keep the tree shallow; avoid per-row heavy work
- **No div-soup / no deep view nesting.** Each wrapper adds layout + paint + (Compose)
  recomposition cost, multiplied by row count. Flatten incidental Figma nesting (the
  `figma-implement` rule applies double in lists): prefer one semantic container per row over
  five nested frames.
- **Hoist heavy work out of the row.** No per-row date/number formatting, no per-row regex,
  no per-row image decode at full size, no allocations in the render path. Precompute/memoize
  (web: `useMemo`/`React.memo`; Compose: stable params + `remember`, give items a stable
  `key`; SwiftUI: stable `Identifiable` ids), and use thumbnail-sized images.
- **Stable keys are mandatory** for virtualized/lazy lists, or the runtime re-creates rows on
  every change (lost scroll position, dropped frames).

### How `ui-fidelity` asserts performance (light, realistic)
Not a full benchmark, a smoke gate at realistic scale:
- Seed the list with a **realistic row count** taken from the mock's domain (if the mock
  implies a feed, use ~1000+ rows, not 12) via the slice's mocks.
- Assert the long-list state stays responsive: only a windowed subset is in the
  DOM/hierarchy (web: count rendered row nodes << total; Compose: only visible items
  composed), the screen scrolls without dropped frames, and time-to-interactive at scale
  stays within tolerance. A list that renders all N rows is a FAIL even if it looks right.

## Outbound checkpoint

All of this is local: building, pseudo-localizing, rendering, measuring, scrolling,
seeding large lists. Reading Figma prototype/interaction data over the REST API or MCP is a
network read, no approval needed. Writing back to Figma, or pushing the built UI or captures to a
remote, is outbound: stop, show what would go out, get the operator's explicit yes first.

## References
- Build: `figma-implement`. Check: `ui-fidelity`. Input + baseline: `figma-extract`.
- Motion/spacing tokens: `design-tokens` (+ `design-tokens-detail.md`). A11y gate:
  `design-a11y`. Reuse: `design-system-audit`, `figma-code-connect`.
