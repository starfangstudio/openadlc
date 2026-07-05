---
name: visual-craft
description: >-
  This skill should be used when the user asks to "make this UI look less generic",
  "apply craft to the design", "fix the AI-generated look", "this looks like a template",
  "stop the purple gradient default", "make the typography distinctive", "the spacing feels
  off", "apply the type scale", "enforce the design system aesthetics", "review the UI for
  generic tells", "check the motion for bounce/elastic", "verify the color palette is
  perceptually consistent", "this looks like shadcn/Tailwind defaults", or "add personality
  to the UI". Detects the project's existing tokens and aesthetic first, then critiques or
  builds against THEM. Enforces: modular fluid type scale (clamp(), 16px body floor, 3x+
  size jump between body and display), OKLCH palettes for perceptual uniformity, 4/8px
  spacing grid, named elevation tokens, spring-physics motion (200-400ms micro) with
  mandatory prefers-reduced-motion, and an anti-generic layer that commits the output to one
  bold context-specific aesthetic direction.
version: 0.1.0
---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# Visual craft

Separate distinctive UI from generic-AI output by grounding every decision in the
project's own tokens and aesthetic, then verifying against a concrete checklist.

## Detect first

Never assume the project's stack or existing style direction. Read before critiquing.

Run the detection commands from [references/visual-craft-detail.md](../../references/visual-craft-detail.md)
(token JSON files, Tailwind/CSS config, Compose/SwiftUI theme grep, font-family grep).

Record: active font families, primary hue (H in OKLCH), spacing unit (4px or 8px base),
elevation strategy (named tokens vs. inline values), existing motion easing. Mark
anything not found `unknown`. Ask before inventing token names or palette values.

## Creative generation pass

Use the official `frontend-design` skill (or Claude Design at claude.ai/design) for the
creative/generation pass. This skill does NOT replace that step; it adds the craft layer
on top. If the task is greenfield UI generation, invoke `frontend-design` first, THEN
apply the steps below to the output.

## Step 1: Typography

Apply these rules against the detected or generated type setup:

- **Scale:** modular, minimum 1.2 ratio at smallest breakpoint, 1.333 at widest.
  Use `clamp()` for fluid steps; never hard-code sizes per breakpoint.
- **Body floor:** 16px minimum. No UI copy below 16px except legal/meta (14px max exception).
- **Display/body jump:** 3x minimum between body size and the largest heading.
- **Pairing:** one display face (headings only) + one utility face (body, labels, UI copy).
  If the project uses Inter, Roboto, or Arial as its ONLY font, flag it. Propose a
  distinctive alternative; do not swap without operator approval.

For the fluid scale CSS snippet and the distinctive font shortlist, see
[references/visual-craft-detail.md](../../references/visual-craft-detail.md).

## Step 2: Color -- OKLCH palettes

If the palette is in HSL, hex, or RGB: convert to OKLCH for the design-system source.

Perceptual uniformity rules: equal L steps (~10-12% apart), L delta >= 50 for AA text
contrast, neutral grays sharing the brand hue at C < 0.05, high chroma peaked at L 40-60.

Flag immediately if the primary palette is purple/indigo with no brand rationale
(H roughly 270-310). Propose an alternative hue; do not change without operator approval.

For OKLCH anatomy, full palette-building steps, and the hue range table, see
[references/visual-craft-detail.md](../../references/visual-craft-detail.md).

## Step 3: Spacing and elevation

- **Grid:** 4px base unit. All padding, gap, and margin values are multiples of 4.
  Prefer multiples of 8 for section-level spacing.
- **Elevation:** named token set, minimum three tiers. Shadow color must tint toward the
  brand primary hue, not pure `rgba(0,0,0,0.1)`.
- Flag uniform `0.1`-opacity shadows on every element: that is the generic tell.

For token name conventions, a shadow color example, and the three-tier reference, see
[references/visual-craft-detail.md](../../references/visual-craft-detail.md).

## Step 4: Motion

- **Duration:** micro-interactions 200-400ms. Full-screen transitions 400-500ms.
- **Easing:** spring physics or M3 `emphasized` easing tokens; no `cubic-bezier` bounce
  unless the animation is semantically playful (games, celebration moments).
- **Reduce:** `prefers-reduced-motion` fallback is non-negotiable. Ship it with the first
  animation.
- Flag elastic/bounce easing applied broadly.

For the duration table, M3 spring tokens, and the `prefers-reduced-motion` CSS block, see
[references/visual-craft-detail.md](../../references/visual-craft-detail.md).

## Step 5: Anti-generic layer

Run the full tell list from [references/anti-generic-checklist.md](../../references/anti-generic-checklist.md).

Minimum four-point check:

1. **Font:** not Inter/Roboto/Arial as sole typeface.
2. **Primary color:** not purple/indigo-on-white with no brand rationale.
3. **Layout:** not a centered uniform three-card grid as the hero pattern.
4. **Shadow:** not uniform `0 1px 3px rgba(0,0,0,0.1)` on every surface.

Commit to ONE bold, context-specific aesthetic direction before output. State it
explicitly: "This UI is [editorial serif + warm amber on near-black]" or "geometric
mono + electric teal on off-white." Vague is not a direction.

## Step 6: Verify

Pass/fail against the project's own tokens (not generic bars):

```
[ ] Fluid type scale applied: all sizes are clamp() or token references, none hardcoded
[ ] Body never below 16px
[ ] Display/body ratio >= 3x
[ ] All palette values in OKLCH in source; accessible pairs verified (L delta >= 50)
[ ] No purple/indigo palette without documented brand rationale
[ ] Spacing values are multiples of 4px
[ ] Elevation uses named tokens; shadow tinted toward brand hue
[ ] Animations: 200-400ms micro, spring/emphasized easing, prefers-reduced-motion present
[ ] Font: distinctive display + utility pair, not Inter-only
[ ] Layout: not uniform three-card grid as primary hero pattern
[ ] Shadow: not uniform 0.1-opacity on every surface
[ ] One bold aesthetic direction stated explicitly in the output
```

Fix every failing item before reporting done.

## Outbound checkpoint

Local work needs no approval. Outbound here (pushing to a branch, opening a PR, publishing the design system, or deploying a preview to an external URL): stop, present exactly what would go out, and get the operator's explicit "yes" first (global consent law).

## References

- [references/visual-craft-detail.md](../../references/visual-craft-detail.md) -- fluid scale snippet, font shortlist,
  OKLCH anatomy and palette steps, elevation token conventions, motion duration table,
  M3 spring tokens, prefers-reduced-motion CSS block.
- [references/anti-generic-checklist.md](../../references/anti-generic-checklist.md) -- full tells + countermeasures.
- [OKLCH CSS function - MDN](https://developer.mozilla.org/en-US/docs/Web/CSS/color_value/oklch)
- [OKLCH in CSS: consistent, accessible color palettes - LogRocket](https://blog.logrocket.com/oklch-css-consistent-accessible-color-palettes)
- [Fluid Type Scale Calculator](https://www.fluid-type-scale.com/)
- [Material 3 Motion: Easing and duration tokens](https://m3.material.io/styles/motion/easing-and-duration/tokens-specs)
- [Claude Cookbook: Prompting for frontend aesthetics](https://platform.claude.com/cookbook/coding-prompting-for-frontend-aesthetics)
- [Why your AI keeps building the same purple gradient website](https://prg.sh/ramblings/Why-Your-AI-Keeps-Building-the-Same-Purple-Gradient-Website)
