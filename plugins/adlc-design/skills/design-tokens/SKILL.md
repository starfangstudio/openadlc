---
name: design-tokens
description: >-
  This skill should be used when the user asks to "set up a design-token pipeline",
  "generate theme code from tokens", "wire Style Dictionary for web iOS and Android",
  "establish a multi-brand token source of truth", "import tokens from Figma", "sync
  Claude Design tokens to native code", "add a brand theme", "swap brand colors without
  touching layout", "emit CSS custom properties from tokens", "generate a SwiftUI Color
  extension from tokens", "produce a Compose theme from design tokens", "normalize tokens
  to DTCG", "set up multi-platform token output", or "hook tokens into Tailwind". Covers
  the full pipeline: source (Claude Design /design-sync or DTCG JSON or Figma REST API),
  normalize to DTCG 2025.10, transform via Style Dictionary v5 into web/iOS/Android
  outputs, and multi-brand config (N brand files, one component-structure token set).
version: 0.1.0
---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# Design tokens

Establish or extend a design-token source of truth and emit native theme code for web,
iOS, and Android from a single DTCG 2025.10 JSON source, across N brand themes.

**Boundary:** tokens govern color, type, spacing, radius, shadow, and motion. Layout
and composition are NOT tokens; they are written in code and stay unchanged across brands.

## Step 1: Detect first

Never assume what already exists. Grep before creating anything:

```bash
# Existing token files (any format)
find . -name "*.json" | xargs grep -l '"\$value"\|"value"' 2>/dev/null | grep -i token | head -20
# Style Dictionary config
find . -name "style-dictionary*" -o -name "sd.config*" | head
# Existing build output
find . -path "*/build/web*" -o -path "*/build/ios*" -o -path "*/build/android*" | head -10
# Hardcoded values that should be tokens
grep -rEn '#[0-9a-fA-F]{3,8}|rgba?\(' src/ --include="*.kt" --include="*.swift" --include="*.tsx" | head -20
```

Record: token format in use (DTCG `$value`/`$type` vs. legacy), existing SD config,
number of brands, output paths. Mark anything you cannot determine `unknown`.

## Step 2: Establish the token source

Use the highest-priority source available:

**Priority 1 -- Claude Design `/design-sync`**
When the project uses Claude Design, tokens arrive pre-structured. Run `/design-sync`
in Claude at claude.ai/design to pull the latest token JSON into the repo, then proceed
to Step 3.

**Priority 2 -- DTCG 2025.10 JSON (portable, no external dependency)**
Create or accept a handwritten DTCG file. Minimum token categories for a brand theme:
`color`, `dimension` (spacing/radius), `fontFamily`, `fontWeight`, `duration`,
`cubicBezier`. See [references/design-tokens-dtcg.md](../../references/design-tokens-dtcg.md) for the
exact field shapes and a minimal example.

**Priority 3 -- Figma REST API (Enterprise only)**
Pull variables via the Figma REST API and map to DTCG groups/tokens with a thin
normalization script; do NOT call the Dev Mode MCP. If access is unavailable, fall back
to Priority 2. For the exact endpoints and mapping notes, see
[references/design-tokens-detail.md](../../references/design-tokens-detail.md).

After fetching from any source, normalize to DTCG before touching Style Dictionary.

## Step 3: Structure for multi-brand

Organize token files with globals aliasing into brand-specific values. Never put layout,
grid, or z-index into brand files -- those are structural and shared.

For the canonical directory layout, see
[references/design-tokens-detail.md](../../references/design-tokens-detail.md).

## Step 4: Wire Style Dictionary v5

Install: `npm install style-dictionary@^5` (or `bun add style-dictionary@^5`).

Create `style-dictionary.config.mjs` iterating over your brand list, with `usesDtcg: true`
and platform entries for `web` (css), `ios` (ios-swift), `android` (xml resources), and
`android-compose` (Kotlin object). For the full annotated config and optional Tailwind
integration, see [references/design-tokens-detail.md](../../references/design-tokens-detail.md).

If the project already has an SD config, extend it rather than replacing it. Merge
`usesDtcg: true` and add missing brand entries; preserve existing transforms.

## Step 5: Verify (pass/fail)

Run `node style-dictionary.config.mjs`, confirm output files exist for every brand x
platform, and grep for hardcoded hex/color values in source (zero matches required).

For the full verify script, see [references/design-tokens-detail.md](../../references/design-tokens-detail.md).

Do not claim done without a passing build and an empty hardcoded-value grep.

## Outbound checkpoint

Local work needs no approval. Outbound here (pushing generated files to a remote, publishing a token package to a registry such as npm/Maven/SPM/CocoaPods, syncing tokens back to Claude Design or any external design tool, writing to the Figma REST API POST /variables): stop, present exactly what would go out, and get the operator's explicit "yes" first (global consent law).

## References

- [references/design-tokens-detail.md](../../references/design-tokens-detail.md) -- token directory layout,
  full SD v5 multi-brand config, Tailwind integration, verify script, and Figma REST API
  variable endpoints.
- [references/design-tokens-dtcg.md](../../references/design-tokens-dtcg.md) -- DTCG 2025.10 format
  spec, the full multi-brand SD v5 build script, platform transform table, and Figma
  REST API variable endpoints.
- DTCG 2025.10 stable specification: https://www.designtokens.org/tr/2025.10/
- Style Dictionary v5 config reference: https://styledictionary.com/reference/config/
- Style Dictionary DTCG support: https://styledictionary.com/info/dtcg/
- SD predefined formats (css/variables, ios-swift, android/*, compose/object):
  https://styledictionary.com/reference/hooks/formats/predefined/
- SD multi-brand-multi-platform example:
  https://github.com/amzn/style-dictionary/tree/master/examples/advanced/multi-brand-multi-platform
- Figma REST API variables endpoints:
  https://developers.figma.com/docs/rest-api/variables-endpoints/
