<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
# Anti-generic UI checklist

Reference for the `visual-craft` skill. Load on demand; do not duplicate into the skill body.

---

## The generic-AI-UI tells (fail any = fix before shipping)

| Tell | What it looks like | Fix |
|---|---|---|
| Default font | Inter, Roboto, Arial, system-ui on EVERY element | Pick one distinctive display face; pair with a narrower utility face |
| Purple/indigo-on-white | Background `#6366f1` or gradient `from-purple-500 to-indigo-600` with no brand rationale | Derive palette from the product's identity; OKLCH-lock the hue |
| Three-card grid | Centered `grid-cols-3`, equal size, equal spacing, hero icon above heading | Use asymmetry, vary card weight; break the grid with at least one outlier |
| Uniform shadow | `box-shadow: 0 1px 3px rgba(0,0,0,0.1)` on every elevated surface | Define elevation as 3-4 named tokens (surface/raised/floating/overlay); tint shadow toward brand hue |
| Elastic bounce | `cubic-bezier(0.68,-0.55,0.27,1.55)` on every transition | Use spring physics or M3 easing tokens; bounce only where it adds semantic meaning |
| Flat color ramps | HSL palette with identical saturation steps | OKLCH: fix L steps (~10-12%), let C vary by context |
| Oversized rounded everything | `rounded-2xl` / `border-radius: 16px` on every component | Reserve large radii for one tier (e.g. cards); buttons/inputs get tighter radii |
| Emoji as icons | Unicode emoji in place of proper icon set | Use a consistent icon system (SF Symbols / Material Symbols / Lucide); never mix |
| Gradient hero text | `background-clip: text` rainbow gradient heading | One high-contrast heading color; gradient text only if brand mandates it |
| Cards inside cards | `.card > .card > .card` nesting | Flatten; use whitespace + border/shadow to separate, not wrapper boxes |

---

## Distinctive font shortlist (non-defaults, verified 2025)

Pair one **display** + one **utility**; never use both at similar sizes.

| Display (personality) | Good utility pair | Notes |
|---|---|---|
| Playfair Display | DM Sans | Editorial / luxury |
| Syne | Space Grotesk | Techy, geometric |
| Fraunces | Figtree | Organic, warm |
| Cabinet Grotesk | Instrument Sans | Clean modern, not Inter |
| Bebas Neue (display only) | Outfit | Bold, high-impact |
| Libre Baskerville | Source Sans 3 | Trustworthy, longform |
| DM Serif Display | DM Mono | Minimal, type-led |

Rules:
- Display face: headings only (display + h1 + h2 at most).
- Utility face: body, labels, UI copy.
- Size jump between display and body: 3x minimum (e.g. 14px body / 48px+ display).

---

## OKLCH palette construction

**Syntax:** `oklch(L% C H)` where L is 0-100%, C is 0-0.4 (100% = 0.4), H is 0-360deg.

### Step-by-step for a brand palette

1. Pick the brand hue (H) from the primary color. Lock it.
2. Build a 9-step lightness ramp: `L = 10, 20, 30, 40, 50, 60, 70, 80, 90`. Each step is perceptually equal distance.
3. Set chroma: high in the 40-60 range, taper toward 0 at extremes (near-white/near-black read clean with low chroma).
4. Accessible pair rule: L delta >= 50 for WCAG AA (4.5:1 text), L delta >= 60 for AAA. Verify with a contrast tool; do not assume.
5. For neutral grays: same H, C < 0.05. This gives "cool" or "warm" grays that harmonize with the brand without shifting hue visually.

**Relative color shorthand (CSS):**
```css
--surface: oklch(96% 0.01 var(--brand-h));
--on-surface: oklch(from var(--surface) calc(l - 0.60) c h);
```

---

## Fluid type scale formula

Derived from the modular-scale + clamp pattern. Requires: min/max viewport (px), body min/max size (px), scale ratio.

```css
/* Generator: https://www.fluid-type-scale.com/ */
/* Example: 16px body at 320px vp, 18px body at 1280px vp, ratio 1.333 (Perfect Fourth) */
--text-base: clamp(1rem, 0.9565rem + 0.2174vi, 1.125rem);
--text-lg:   clamp(1.333rem, 1.2739rem + 0.2956vi, 1.5rem);
--text-xl:   clamp(1.777rem, 1.698rem  + 0.3939vi, 2rem);
--text-2xl:  clamp(2.369rem, 2.264rem  + 0.5251vi, 2.667rem);
--text-3xl:  clamp(3.157rem, 3.018rem  + 0.6996vi, 3.556rem);
```

Rules:
- Body floor: **16px minimum** (never smaller; accessibility + readability).
- Scale ratio at smallest viewport: 1.2 (Minor Third) keeps mobile hierarchy compact.
- Scale ratio at largest viewport: 1.333 or 1.5; display headings diverge more on wide screens.
- Use `vi` (inline-axis) not `vw` for proper i18n; fall back to `vw` if container-query unit (`cqi`) support is insufficient.

---

## Spring motion parameters

### Recommended micro-interaction range
- Duration: **200-400ms**
- Stiffness: 300-500 (snappy without overshoot)
- Damping: 25-35 (near-critically damped; minimal bounce)
- Mass: 1

### M3 Expressive spring tokens (as of 2025)
Token pattern: `md.sys.motion.spring.<speed>.<type>` where speed = fast/default/slow, type = spatial/effects.
- **Fast spatial**: small element moves, icon swaps (~150-200ms effective)
- **Default spatial**: component enter/exit (~250-350ms effective)
- **Slow spatial**: full-screen transitions (~400-500ms effective)
- **Effects**: color/opacity change; use standard easing (emphasized-decelerate for enter, emphasized-accelerate for exit)

Reference: [M3 Easing and duration tokens](https://m3.material.io/styles/motion/easing-and-duration/tokens-specs)

### prefers-reduced-motion (mandatory)
```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
```
Never gate the reduced-motion fallback on a feature flag. It ships with the first animation.

---

## References

- [OKLCH CSS function - MDN](https://developer.mozilla.org/en-US/docs/Web/CSS/color_value/oklch)
- [OKLCH in CSS: consistent, accessible color palettes - LogRocket](https://blog.logrocket.com/oklch-css-consistent-accessible-color-palettes)
- [Fluid Type Scale Calculator](https://www.fluid-type-scale.com/)
- [Material 3 Easing and duration tokens](https://m3.material.io/styles/motion/easing-and-duration/tokens-specs)
- [Material 3 Motion overview](https://m3.material.io/styles/motion/overview/how-it-works)
- [Why your AI keeps building the same purple gradient website](https://prg.sh/ramblings/Why-Your-AI-Keeps-Building-the-Same-Purple-Gradient-Website)
- [Design Systems for AI Coding: Stop Getting Purple Gradients](https://www.braingrid.ai/blog/design-system-optimized-for-ai-coding)
- [Claude Cookbook: Prompting for frontend aesthetics](https://platform.claude.com/cookbook/coding-prompting-for-frontend-aesthetics)
