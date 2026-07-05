---
name: figma-implement
description: "This skill should be used when building UI from a Figma design, \"implement this screen\", \"build the component from Figma\", \"turn the design into code\", or when /ai-implement runs a UI slice with adlc-design loaded. Turns an extracted Figma design into production UI that reuses the design system (tokens, components, styles, fonts), covers the states and responsiveness, and reaches the target screen cheaply via mocks and a fast route so the build never flails. Pairs with figma-extract (input) and ui-fidelity (the check)."
version: 0.1.0
---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# Figma implement

Build UI from an extracted Figma design, well: reuse before you rebuild, cover the states, and get to the screen fast so you do not burn hours and tokens trying to render it.

## Step 0: Use the design-system rules; translate, don't transcribe
Ensure a per-repo **design-system rules** file exists (generate it once with the Figma MCP `create_design_system_rules`): naming, framework, token usage, file organization. It steers every generation toward your stack.

Treat the design as **intent, not literal code**:
- **Layout:** a Figma *fixed* width/height is often `fill` / `match_parent` / `100%` / flex in code. Use the captured resizing, Fill -> fill / match_parent, Hug -> wrap / fit-content, Fixed -> a fixed dimension only when truly intended. Honor constraints; do not pin everything to absolute px.
- **Structure:** flatten Figma's incidental nesting into a clean semantic hierarchy; never replicate junk wrapper frames.
- **Output:** re-express `get_design_context` in the project's framework and conventions; never paste the MCP snippet verbatim.

Build the design's result and intent in idiomatic code, not a literal copy of the node tree. The exact mappings (resize mode and constraint to a per-platform primitive), the seven-condition flatten-safety test, instance-override handling, and legit-vs-junk absolute positioning are in [references/figma-translation-detail.md](../../references/figma-translation-detail.md); apply them.

## Step 1: Reuse before building
From the `figma-extract` bundle, map the design to what already exists:
- **Tokens:** bind to the design-token output (`design-tokens`); never hardcode a hex, font, or spacing value.
- **Components:** lead with **Figma Code Connect** (`get_code_connect_map`), it maps each Figma component to its real design-system component, so reuse the DS source of truth, not a regenerated copy. Fall back to the `design-system-audit` inventory. Build a new component only when none fits, build it reusably (props, variants), and add a Code Connect mapping for it (via `figma-code-connect`) so the next design reuses it too.
- **Styles / fonts:** use the design system's type and style primitives.

## Step 2: Plan the route to the screen FIRST (the efficiency gate)
UI flows get deep. Before iterating on pixels, set up the **fastest path to render the target screen**, from the plan's design refs:
- the **mocks** the screen needs (seeded data, auth state, feature flags, stubbed backend), and
- the **quickest route** to it: a deep link, a preview / storybook route, a dev-only entry, or seeded navigation state.

If you cannot reach the screen this way after the planned route, **STOP and ask** (a HALT gate). Never loop for hours navigating the live app to a deep screen; that is the token bonfire we refuse.

## Step 3: Build the states, themes, and breakpoints
Implement the states the plan lists (loading, empty, error, success, permission), every **theme / flavor / mode** the design defines (light / dark, brand, density) via mode-aware tokens (a hardcoded value cannot follow a mode switch), and the responsive breakpoints. A screen that only renders the happy path, in one theme, at one width, is not done. Localization and text overflow, motion, overlays / scroll / stacking, and performance are in [references/figma-robustness-detail.md](../../references/figma-robustness-detail.md).

## Step 4: Verify with fidelity
The slice's failable check is `ui-fidelity`: it measures the running screen against the Figma values and tokens (numbers first, screenshot second). Build to green. A value that renders right but is a **hardcoded hex instead of the token** is still a FAIL. On a fail, `ui-fidelity` hands back the deltas + `path:line`, **edit those nodes, do not regenerate the component** (regenerating clobbers prior correct work and hand-written logic).

## Outbound checkpoint
All local. Pushing the built UI to a remote is outbound: get the operator's explicit yes first.

## References
- Input: `figma-extract` (bundle + dated baseline). Check: `ui-fidelity`. Reuse + craft: `design-system-audit`, `design-tokens`, `visual-craft`, `design-a11y`.
- Depth: [references/figma-translation-detail.md](../../references/figma-translation-detail.md) (layout translation, instances, flatten), [references/figma-robustness-detail.md](../../references/figma-robustness-detail.md) (i18n, motion, overlays, performance).
