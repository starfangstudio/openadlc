<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
Consumed by the `figma-implement` skill (Step 0, "translate, don't transcribe"). Load on
demand; do not load independently. This is the layout-translation engine: it turns the
two real Figma layout signals into idiomatic code primitives per platform, decides what
nesting to flatten, and decides when absolute positioning is a defect.

## The one rule that governs everything

A node's reported `width` / `height` in px is **NOT the source of truth**. It is the
*result* of the layout engine at the size the designer last left the canvas. The source of
truth is the **resize mode** (auto-layout child) or the **constraint** (non-auto-layout
child). Translate the mode/constraint into a responsive primitive; use the reported px only
when the mode is genuinely Fixed (and even then, prefer a token over a raw number).

The two signals are **mutually exclusive on a given node** (verified against Figma's docs):
- If the node's **parent is an auto-layout frame**, the node carries a **resize mode**
  (`layoutGrow` / `layoutAlign` / `layoutSizingHorizontal` / `layoutSizingVertical` in the
  REST API). Constraints do not apply.
- If the node's **parent is a plain frame** (not auto-layout), the node carries a
  **constraint** (`constraints.horizontal` / `constraints.vertical`). Resize mode does not
  apply.

So read the parent first, then read the right signal. Below, the auto-layout rows and the
constraint rows are separate because no node is ever in both columns at once.

## Signal -> primitive lookup (the core table)

Horizontal axis shown; the vertical axis is identical (swap width->height, Row->Column,
maxWidth->maxHeight, Left/Right->Top/Bottom). "DS prop" means: if Code Connect resolved a
DS component, the resize intent usually maps to that component's own size prop, not a raw
layout modifier (see Instance handling).

### A. Parent IS an auto-layout frame (read the resize mode)

| Figma resize mode | REST signal | Web (flex child) | Jetpack Compose (Row/Column child) | SwiftUI (HStack/VStack child) |
|---|---|---|---|---|
| **Fill container** | `layoutGrow: 1` (along axis) or `layoutSizingHorizontal: "FILL"` | `flex: 1 1 0` (i.e. `flex-grow:1; flex-basis:0`), NOT `width:100%` | `Modifier.weight(1f)` (in `RowScope`/`ColumnScope`); set the cross-axis size separately | `.frame(maxWidth: .infinity)` |
| **Hug contents** | `layoutSizingHorizontal: "HUG"` (only valid on a frame that has children) | default flex item: `flex: 0 0 auto`, no width set, let content size it; `width: fit-content` if you must name it | wrap content: no `weight`, no `fillMaxWidth`; intrinsic size (e.g. `Modifier.wrapContentWidth()` if overriding a parent) | intrinsic size: no `.frame` width modifier; the view hugs its content by default |
| **Fixed** | `layoutSizingHorizontal: "FIXED"` | `width: <token>` only if the value is a real design constant (icon 24, avatar 40); else treat as Fill/Hug | `Modifier.width(<token>.dp)` only for true constants | `.frame(width: <token>)` only for true constants |

Two auto-layout gotchas that are NOT a child resize mode but change the child code:

- **Distribution = `SpaceBetween` / `SpaceAround` / `SpaceEvenly`.** If the parent frame's
  `primaryAxisAlignItems` is `SPACE_BETWEEN`, the *gap is the layout*, not a child size.
  Translate the **parent**, not each child: web `justify-content: space-between`; Compose
  `horizontalArrangement = Arrangement.SpaceBetween`; SwiftUI has no such property, so you
  insert `Spacer()` between the children (see the SwiftUI section). Do not give the children
  Fill to fake the spacing.
- **`layoutAlign: "STRETCH"`** on a child means "stretch on the **cross** axis" (a child of
  a Row that fills the Row's height). That is the cross-axis Fill: web `align-self: stretch`;
  Compose `Modifier.fillMaxHeight()` (or `Modifier.align` is not it, use fill); SwiftUI
  `.frame(maxHeight: .infinity)`.

### B. Parent is a PLAIN frame (read the constraint)

Constraints describe what happens when the **parent** resizes. Translate the *relationship*,
not the snapshot px.

| Figma constraint (horizontal) | What it means on parent resize | Web | Jetpack Compose | SwiftUI |
|---|---|---|---|---|
| **Left** | pinned to left, fixed width | `position:absolute; left:<x>` or static block, fixed `width` | `Modifier.width(w).align(Alignment.TopStart)` in a `Box` | `.frame(width: w, alignment: .leading)` |
| **Right** | pinned to right, fixed width | `position:absolute; right:<dist>` | `Box` child with `Modifier.align(Alignment.TopEnd)` | `.frame(maxWidth: .infinity, alignment: .trailing)` on the slot |
| **Left and right** (Stretch) | both edges pinned, width grows with parent | `position:absolute; left:<x>; right:<y>` (no width) OR a block at `width:100%` if it is a normal flow child | `Modifier.fillMaxWidth()` (optionally minus padding) | `.frame(maxWidth: .infinity)` |
| **Center** | stays centered, fixed width | `margin-inline:auto` (flow) or `left:50%; transform:translateX(-50%)` (absolute) | `Box(...) { child(Modifier.align(Alignment.Center)) }` | `.frame(maxWidth: .infinity)` wrapper, child centered (default) |
| **Scale** | width stays a % of parent | `width: <p>%` | `Modifier.fillMaxWidth(<fraction>)` (e.g. `0.7f`) | `.frame(maxWidth: .infinity)` then `.scaleEffect`/`GeometryReader` % (no built-in % width) |

Key reading: **Left and right** is the only horizontal constraint that makes a child *grow*,
it is the constraint equivalent of Fill. **Scale** is the only one that holds a *percentage*;
map it to a fractional fill, never to the snapshot px.

## Per-platform mapping and the real gotchas

### Web (CSS flex / grid)

- **`flex:1 1 0` (or `flex-grow:1`) vs `width:100%` is the #1 mistake.** Figma **Fill** =
  "share the remaining space with my siblings" = `flex-grow`. `width:100%` is
  `flex:0 0 100%`, which forces the item to the parent's full width and **wraps the siblings
  to the next line** if `flex-wrap` is on. Use `width:100%` only for a single full-bleed
  child or a block element outside a flex row. For Fill, set `flex:1 1 0` so the basis is 0
  and the grow factor distributes free space (this matches Figma's "split the gap evenly"
  behavior; `flex:1 1 auto` lets content sizes skew the split).
- **Constraints map to flow OR absolute, pick deliberately.** A `Left and right` child in a
  plain frame is `position:absolute; left/right` *or* a normal `width:100%` block; choose
  flow whenever the parent is a normal stack, reserve absolute for true overlays (see
  Absolute positioning).
- **Figma auto-layout `wrap` = flex `flex-wrap:wrap`**; a 2D grid of equal cells (a real grid,
  not a wrapping row) is `display:grid; grid-template-columns:repeat(N, 1fr)`. Do not emit a
  grid for a single-direction auto-layout, that is a wrapping flex row.
- Gap: auto-layout `itemSpacing` -> `gap:<token>`; never fake it with per-child margins.

### Jetpack Compose

- **`Modifier.weight(1f)` is the Fill primitive, and it ONLY exists inside `RowScope` /
  `ColumnScope`.** A Fill child of an auto-layout Row -> `Modifier.weight(1f)` on that child
  inside a `Row`. `fillMaxWidth()` is different: it makes a composable take its parent's full
  width, which is correct for a single full-width element, not for "share space with
  siblings". Mixing them up gives you either a crash-free-but-wrong full-width child or an
  overflowing row.
- **The 0dp-in-weighted-row rule.** When a child has `Modifier.weight(1f)`, its main-axis
  size is resolved by the weight, you do **not** also set `Modifier.width(...)` on that axis.
  (In the View/XML world this was the literal `0dp` + `layout_weight`; in Compose `weight`
  already implies the 0-basis, so you simply omit the width.) Set only the cross-axis size,
  e.g. `Modifier.weight(1f).height(48.dp)`.
- `weight(weight = 1f, fill = true)` (the default) forces the child to occupy its share even
  if its content is smaller. Use `fill = false` when the child should take *at most* its share
  but hug if smaller, that is the Compose answer to a Fill child that should still shrink to
  content.
- **Distribution:** auto-layout `SPACE_BETWEEN` -> `Row(horizontalArrangement =
  Arrangement.SpaceBetween)`, the direct analog of `justify-content:space-between`. Other gaps:
  `Arrangement.spacedBy(<token>.dp)`.
- Cross-axis stretch (`layoutAlign:STRETCH`) -> `fillMaxHeight()` on a Row child (or
  `fillMaxWidth()` on a Column child), not `weight`.

### SwiftUI

- **There is no `match_parent`.** The Fill primitive is `.frame(maxWidth: .infinity)` (and/or
  `.maxHeight: .infinity`). A view does NOT fill its parent by default; it hugs its content,
  so Hug needs no modifier at all.
- **Distribution has no `space-between` property.** Translate auto-layout `SPACE_BETWEEN` with
  `Spacer()` between the children inside the stack: `HStack { Leading(); Spacer(); Trailing() }`.
  `Spacer()` expands to consume free space and pushes its neighbors to the edges. For
  `SPACE_AROUND` / `SPACE_EVENLY`, wrap with `Spacer()` on the outside too
  (`HStack { Spacer(); A(); Spacer(); B(); Spacer() }`).
- **`.frame(maxWidth: .infinity)` + alignment replaces a one-sided Spacer.** A `Right`
  constraint (or right-aligned single child) is `.frame(maxWidth: .infinity, alignment:
  .trailing)`, cleaner than `HStack { Spacer(); child }`.
- **Scale / % width has no native primitive.** Map a Figma `Scale` constraint with
  `GeometryReader { geo in child.frame(width: geo.size.width * 0.7) }`, not the snapshot px.
- Fixed is `.frame(width:)` / `.frame(height:)`, reserve it for true constants.

## Instance handling (after Code Connect resolves the base component)

When `get_code_connect_map` (per `figma-code-connect`) returns the real DS component for a
node, you do **not** rebuild it, you configure it. Read the instance's override set from the
node and translate each override to a DS prop, slot, or child. The override set lives in the
REST API on the instance node (`componentProperties`, plus the diff between the instance's
children and the main component's children).

| Figma override on the instance | Where to read it | Translate to |
|---|---|---|
| **Text override** (label changed) | `componentProperties` entry of `type:"TEXT"`, or the overridden text child's `characters` | the DS component's text/label prop or its text slot child (e.g. `<Button>Save</Button>`, `Button(text = "Save")`, `Button("Save")`) |
| **Instance-swap prop** (a sub-component was swapped) | `componentProperties` entry of `type:"INSTANCE_SWAP"` (value is the swapped component id) | the DS component's slot/`@Composable` content prop / `ViewBuilder` parameter, pass the swapped DS component into the slot |
| **Boolean / variant prop** | `componentProperties` of `type:"BOOLEAN"` / `type:"VARIANT"` | the matching DS enum/boolean prop (`variant="primary"`, `isLoading=true`); map 1:1 to the value Code Connect declared, never approximate |
| **`visible = false` layer** | the child node's `visible:false` | do NOT render that slot, conditionally omit the child or set the DS prop that hides it (e.g. `showIcon=false`); never render a hidden layer "just in case" |
| **Nested-instance override** (an override inside a nested instance) | walk into the nested instance node and read its own override set | the **nested DS component's** props, a nested instance maps to a nested DS component, recurse the same table |

Nested instances map to nested DS components, all the way down. Resolve the outer DS
component first, then for each child that is itself an instance, recurse: Code Connect on the
child, then its override set. Mark any override you cannot map to a DS prop as `unknown`; do
not invent a prop (matches `figma-code-connect` Step 2).

## Flatten-safety test (collapse incidental wrappers, keep load-bearing ones)

`figma-implement` says "flatten Figma's incidental nesting" and "never replicate junk wrapper
frames". This is the exact test. A wrapper frame is **safe to collapse into its child** ONLY
if **every** condition below holds. If any one fails, the wrapper is load-bearing, keep it.

A wrapper is safe to flatten ONLY if it has:
1. **exactly one child** (zero or multiple children -> the wrapper groups, keep it), AND
2. **no padding** (`paddingLeft/Right/Top/Bottom` all 0), AND
3. **no fill** (no background paint), AND
4. **no stroke** (no border), AND
5. **no corner radius / no clip** (`cornerRadius` 0 and `clipsContent:false`, a radius or
   clip changes rendering), AND
6. **no constraint of its own** that differs from what the child would carry (the wrapper
   is not doing the resizing on behalf of the child), AND
7. **it is not an auto-layout frame whose alignment or distribution positions the child**,
   i.e. not `SPACE_BETWEEN`/`SPACE_AROUND`/`SPACE_EVENLY`, and not a non-default
   `counterAxisAlignItems` (center/end) that the single child relies on for placement.

If all seven pass, drop the wrapper and apply its (none) layout to the child directly. The
common safe case: a `Frame` named "Frame 217" with one child, no padding/fill/stroke/radius,
auto-layout but `itemSpacing:0` and default alignment, that is pure nesting noise, collapse
it. The common UNsafe case: a frame that *looks* empty but has `padding:16` or a
`cornerRadius`, collapsing it silently drops the spacing or the rounded corner.

## Absolute positioning: legitimate vs junk

Figma absolute position appears two ways in the API: a child with
`layoutPositioning: "ABSOLUTE"` inside an auto-layout frame (the designer explicitly
"ignored auto layout" for that child), or any child of a plain frame positioned by x/y +
constraints. Both can be legitimate or junk, judge by *intent*, not by the presence of x/y.

**Legitimate (translate as absolute / overlay, do NOT flag):**
- **Overlay / scrim** that sits on top of content.
- **Badge** pinned to a corner of its anchor (notification dot, count badge).
- **Pin / marker** placed at a coordinate on a map/image.
- **FAB** (floating action button) pinned to a corner of the screen.
  Tell: the child uses `layoutPositioning:"ABSOLUTE"` *on purpose* over a sibling, or its
  constraints pin it to a corner (e.g. `Right` + `Top`). Code it as `position:absolute` /
  Compose `Box` with `Modifier.align(...)` / SwiftUI `.overlay(alignment:)`.

**Junk (flag as a defect, recommend auto-layout):**
- **Hand-positioned siblings** that form a row or column, each placed by x/y with no
  auto-layout, that should be a Row/Column with a gap. Tell: 2+ siblings at incrementally
  increasing x (or y) with consistent spacing, no `layoutMode` on the parent, no overlap.
  That is a stack a designer eyeballed; it will not reflow and is brittle.
  Flag it (this is the low design-readiness signal `figma-extract` Step 3 warns about) and,
  if building anyway, translate to the proper Row/Column with `gap`/`itemSpacing`, do not
  reproduce the magic x/y numbers.

Flag absolute positioning as a defect **only** in the junk case. A correctly-pinned overlay,
badge, pin, or FAB is good design, translating it to absolute positioning is the right call,
not a finding.

## References
- Upstream signals + readiness score: `figma-extract`. Consumer: `figma-implement` (Step 0).
- Component resolution: `figma-code-connect` (Code Connect map + override mapping).
- The check this feeds: `ui-fidelity` (it measures the rendered *result* of these
  translations, idiomatic fill/weight/`.infinity` is correct as long as the result matches).
- Figma docs: auto-layout resizing
  https://help.figma.com/hc/en-us/articles/360040451373-Guide-to-auto-layout ;
  constraints (and the auto-layout mutual-exclusion)
  https://help.figma.com/hc/en-us/articles/360039957734-Apply-constraints-to-define-how-layers-resize
