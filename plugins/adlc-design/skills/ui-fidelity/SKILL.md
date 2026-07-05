---
name: ui-fidelity
description: "This skill should be used to verify a built UI matches its design, \"check the UI against Figma\", \"is this pixel-perfect\", \"run the fidelity check\", \"compare the screen to the design\", or as the failable check for a UI slice in /ai-implement and the design-fidelity lens in /ai-review. Fully automated on both ends: it gets the Figma values and image, renders the running app on the operator's machine, and asserts measured numbers and token references against the design (screenshot second). This is UI's test."
version: 0.1.0
---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# UI fidelity

The automated, both-ends check that a built UI matches its design: **measure** the running app against the Figma values and tokens, then confirm it holistically. It is the failable check for UI slices, the UI half of the acceptance-criteria check, and the design lens in review. UI fidelity is a compliance question: did we build the design, or not?

## Step 1: Get the design truth
From `figma-extract`: the dated baseline image, the **numeric values** (sizes, spacing, positions from the metadata), the **bound token names** (`get_variable_defs`), and the component's **variants / states**. You assert against these, not just the picture.

## Step 2: Render the app (automated, pinned)
Reach the screen via the plan's fast route + mocks (`figma-implement`). Pin a fixed render environment (viewport, density, container) so the check is deterministic (the exact per-platform pins are in [references/ui-fidelity-detail.md](references/ui-fidelity-detail.md)).
- **Web:** `preview_start`, then drive `preview_eval` and `preview_screenshot`.
- **Desktop / device:** computer-use, or the platform screenshot (simulator / emulator).

## Step 3: Measure first (the primary signal)
Numbers beat eyeballs; anti-aliasing and font rendering fool a pixel diff. Query the rendered node and compare exact values against the Figma truth:
- **Geometry + style:** `getBoundingClientRect()` and `getComputedStyle()` (web via `preview_eval`; the native measurement path for Compose / SwiftUI and the tolerance table are in [references/ui-fidelity-detail.md](references/ui-fidelity-detail.md)) for size, spacing, padding, font size / weight, radius, color. Emit numeric **deltas** (28px vs 24px) as the primary verdict.
- **Token compliance (structural):** the rendered value must **reference the expected token / Figma Variable**, not just match it by eye. A hardcoded hex that happens to look right is a **high-severity FAIL**: it bypasses the design system and breaks on the next brand or mode change. This is a **source check** (the `path:line` bound to the node uses a token symbol; delegate to `design-system-audit`), not a runtime one, since a compiled native binary cannot reveal token references.
- **States and variants:** assert every Figma-defined state (hover, focus, disabled, pressed) and variant exists in code; a missing interactive state is a FAIL and an a11y risk (route to `design-a11y`).
- **Responsive + resizing intent:** render at each breakpoint and assert the layout matches that frame. Verify the **resizing behavior** matches the Figma intent (Fill stretches, Hug wraps, Fixed holds). Measure the rendered *result*, not the code's structure, idiomatic code (fill / match_parent instead of a fixed px, a flatter hierarchy than Figma) is correct as long as the rendered design matches; flag fixed px only where the intent is fill / relative.
- **Theme modes:** if the design uses Figma Variable modes (light / dark / brand), render each and assert the build switches correctly. This proves mode-responsiveness; token *reference* is the separate source check above.

## Step 4: Confirm holistically (the secondary signal)
Diff the screenshot against the Figma image for what numbers miss (overall composition, overlap, stacking). Run an a11y smoke gate (axe-style + focus-order / keyboard) as part of the done bar.

## Step 5: Verdict (pass / fail), machine-applicable
Return **PASS** (within tolerance, see [references/ui-fidelity-detail.md](references/ui-fidelity-detail.md)) or **FAIL**. For each mismatch emit: severity, consequence, the exact `path:line`, and a **concrete suggested edit** (the CSS / token change) so the fix can be applied and re-verified in one turn. A fail is an unmet acceptance criterion.

## The fix loop: edit, do not regenerate
On a FAIL, hand back to `figma-implement` the current code + the specific deltas + `path:line`, with the instruction **edit those nodes, do not regenerate the component** (regenerating clobbers prior correct work and hand-written logic). Re-verify only the changed nodes.

## Design drift vs regression drift
This skill checks **design-to-source** fidelity (the build vs the current Figma frame). It does not catch a later code change **drifting from the last good build**; that is a separate visual-regression baseline (commit preview screenshots, accept / deny gate). If the running screen and Figma disagree because the **design moved**, flag drift, do not "fix" code to a dead design.

## Outbound checkpoint
Local: get the design image / values, render and measure the local app, compare. Nothing here is outbound. Posting the result externally needs the operator's explicit yes first.

## References
- Baseline + values: `figma-extract`. Build + fix: `figma-implement`. A11y: `design-a11y`. Craft: `visual-craft`.
- Depth: [references/ui-fidelity-detail.md](references/ui-fidelity-detail.md) (tolerances, determinism pins, native measurement, CLS), [references/figma-robustness-detail.md](references/figma-robustness-detail.md) (motion, overlays, scroll verification).
