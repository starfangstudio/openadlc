---
name: figma-extract
description: "This skill should be used when the user or a plan / sub-issue references a Figma file, frame, or component and the work needs the design pulled into the build, \"get the design from Figma\", \"extract this screen/component\", \"what does the Figma say\", \"download the design baseline\", \"check the design for drift\", or when /ai-plan or /ai-implement loads adlc-design for a UI task. Pulls the design context and a dated image baseline for a Figma node via the Figma REST API (the Dev Mode MCP is an optional fallback), records what is reusable, and flags drift from a prior baseline. Figma is the only supported design tool."
version: 0.1.0
---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# Figma extract

Pull a Figma node into the build: its structure, the tokens and components it uses, and a dated image baseline the fidelity check compares against. Read-only; downloads images locally.

**Load only on demand:** run this only when the issue references Figma or a design surface. No design in play, no Figma calls. Requires a Figma access token in the environment (`FIGMA_ACCESS_TOKEN`); the Dev Mode MCP is an optional fallback, not required.

## Step 1: Resolve the node
Take the Figma URL or `node-id` from the issue / plan. If none is given, ask for the exact frame or component link; do not guess. One screen or component per extract.

## Step 2: Pull the design (Figma REST API by default; MCP only as a fallback)
**Default to the Figma REST API** for everything it can serve, it is faster and richer than the MCP: the full node tree, exact geometry, **layout constraints and auto-layout resizing (Fixed / Hug / Fill)**, components, and styles, plus the **Images endpoint** to render any node to PNG / SVG at any scale (your baseline). It needs a Figma access token, read it from the environment, never hardcode it. REST reads are network reads, no approval needed. The endpoints, the `X-Figma-Token` header, the `FIGMA_ACCESS_TOKEN` env var, node-id parsing, and curl examples are in [references/figma-rest-detail.md](../../references/figma-rest-detail.md).

Fall back to the **Figma MCP only** when the REST API cannot serve it (no token set, the Code Connect map, or Variables on a non-Enterprise plan), in this order (so a large frame does not blow context):
1. `get_design_context` for the curated, code-oriented intent of the selection (if truncated, `get_metadata` for the node map, then re-fetch only the nodes you need).
2. `get_code_connect_map` for the **Code Connect** mapping (the reuse backbone, returns your real DS component; no mapping -> flag, run `figma-code-connect`).
3. `get_variable_defs` for the bound token names and **all their modes** (light / dark / brand). On Enterprise, the REST Variables API is richer; otherwise use the MCP. The token *pipeline* stays with `design-tokens`.
4. `get_screenshot` as a quick selection check; the REST Images endpoint is preferred for the saved baseline.

Capture the **layout intent** explicitly, Fixed / Hug / Fill, constraints, auto-layout, not just literal px, so `figma-implement` can translate it into idiomatic responsive code rather than copying fixed dimensions. Cite what you find; mark anything you cannot resolve `unknown`, never invent a value.

## Step 3: Score design-readiness (input quality gates output quality)
Input quality dominates output quality more than model strength. Score the node before anything is built: is a flow laid out with **auto-layout** (not hand-positioned siblings)? are **Variables bound** (not raw hex/px)? are **layers named** (not "Frame 217")? Emit a **design-readiness note**; if the node is low-quality (no variables, junk wrapper frames, or siblings hand-placed by x/y that should be a Row/Column), **warn and recommend a cleanup or a kick back to design** rather than building on sand. Absolute positioning is a defect only in that junk case; a legitimately-absolute overlay / badge / FAB is fine (see [references/figma-translation-detail.md](../../references/figma-translation-detail.md)).

## Step 4: Render the image baseline
Render the node via the REST **Images endpoint** (any scale; SVG for vectors) and save the PNG locally as the **dated fidelity baseline** (e.g. `design-baseline/<screen>@<date>.png`); fall back to the MCP `get_screenshot`. This is what `ui-fidelity` measures the running app against. Record the node id and the date beside it. Production asset / icon extraction at platform densities is in [references/figma-rest-detail.md](../../references/figma-rest-detail.md).

## Step 5: Check for drift
If the plan already carries a baseline for this node, compare the fresh pull against it. Designs are volatile (a token update overnight, half a screen changed on a call). If the live design has moved, **flag the drift and stop**: the plan's baseline is stale, run `iterate-plan` before building to a design that no longer exists. Diff the structured pull field-by-field (geometry, bound token names, component refs), not the PNG; the exact trip rules are in [references/figma-rest-detail.md](../../references/figma-rest-detail.md).

## Output
A **design bundle** per node, ready for `figma-implement` and `ui-fidelity`: the node id, the **layout intent** (resize mode + constraint), bound token names (and their modes), the Code Connect component (or `unknown`), the instance override set, the design-readiness note, and the dated baseline image. Hand tokens to `design-tokens`, the reusable-component list to `design-system-audit`.

## Outbound checkpoint
Reading Figma and saving images locally needs no approval. Writing back to Figma (any POST), or pushing downloaded assets to a remote, is outbound: stop, show what would go out, get the operator's explicit yes first.

## References
- Token pipeline: the `design-tokens` skill. Component reuse / DS adherence: the `design-system-audit` skill. The fidelity check: the `ui-fidelity` skill.
- Depth: [references/figma-rest-detail.md](../../references/figma-rest-detail.md) (REST endpoints, drift diff, asset density), [references/figma-translation-detail.md](../../references/figma-translation-detail.md) (how the captured layout intent becomes code).
