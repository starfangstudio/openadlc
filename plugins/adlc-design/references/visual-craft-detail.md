<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
Consumed by the `visual-craft` skill. Load on demand; do not load independently.

## Detection commands

Run these in the project root during the "Detect first" step:

```bash
# Token files: Style Dictionary source, CSS custom properties, Compose tokens, Swift tokens
find . -type f \( -name "*.json" -o -name "*.tokens.json" -o -name "design-tokens*" \) \
  | grep -vE "node_modules|build|dist" | head -20

# Existing CSS / Tailwind config (color, font, spacing, radius, shadow)
find . -type f \( -name "tailwind.config*" -o -name "*.css" -o -name "*.scss" \) \
  | grep -vE "node_modules|build" | head -10

# Compose theme / Material tokens
grep -rn "MaterialTheme\|ColorScheme\|Typography\|Shape" --include="*.kt" . | head -20

# SwiftUI theme / token usage
grep -rn "Color\.\|Font\.\|\.padding\|cornerRadius" --include="*.swift" . | head -20

# Font families already in use
grep -rn "font-family\|fontFamily\|FontFamily" --include="*.css" \
  --include="*.kt" --include="*.swift" --include="*.tsx" . | head -20
```

## Typography detail

### Fluid type scale snippet

Generate exact values at https://www.fluid-type-scale.com/, then wire them as custom properties:

```css
/* Minimum 1.2 ratio at smallest breakpoint, 1.333 at widest */
--text-base:    clamp(1rem, 0.9565rem + 0.2174vi, 1.125rem);
--text-display: clamp(3rem, 2.5rem + 2.5vi, 5rem);
```

Rule: never hard-code px sizes per breakpoint. All sizes are `clamp()` references or token aliases.

### Distinctive font shortlist (alternatives to Inter/Roboto/Arial)

Propose one of these (or a client-approved alternative) when the project uses a generic sole typeface:

- Display: Fraunces, Playfair Display, DM Serif Display, Syne, Cabinet Grotesk
- Utility/body: Plus Jakarta Sans, Outfit, DM Sans, IBM Plex Sans, Nunito Sans
- Mono accent: JetBrains Mono, Fira Code (use sparingly as a typographic detail)

Do not swap the active typeface without operator approval.

## OKLCH color detail

### Anatomy

`oklch(L% C H)`: L = 0-100% lightness, C = 0-0.4 chroma (0.4 is max), H = 0-360 hue.

### Building a perceptually uniform palette

1. Space lightness ramps in equal L steps (~10-12% apart).
2. Accessible text pairs: L delta >= 50 for WCAG 2.2 AA (4.5:1 contrast), >= 60 for AAA.
3. Neutral grays: same H as brand primary, C < 0.05. Grays harmonize without hue shift.
4. High-chroma peak sits at L 40-60; taper C toward both extremes.

### Purple/indigo hue range to flag

Hue H roughly 270-310 with no brand rationale. Propose an alternative hue derived from the product context before changing anything.

## Elevation tokens

Minimum three named tiers (CSS custom property names are conventions, not mandated identifiers):

```
--elevation-surface   (resting layer: cards, panels)
--elevation-raised    (interactive: buttons, chips)
--elevation-floating  (overlays: dialogs, tooltips, menus)
```

Shadow color rule: tint toward the brand primary hue. Example for a teal primary (H ~185):

```css
--elevation-raised: 0 2px 8px oklch(20% 0.05 185 / 0.25);
```

Generic tell: uniform `box-shadow: 0 1px 3px rgba(0,0,0,0.1)` on every surface. Flag it.

## Motion detail

### Duration reference

| Category | Range |
|---|---|
| Micro-interactions (hover, toggle, ripple) | 200-400ms |
| Full-screen transitions, modals | 400-500ms |

### Spring / M3 easing tokens

Prefer Material 3 `emphasized` easing (`cubic-bezier(0.2, 0, 0, 1)`) or a true spring
(e.g., Framer Motion `spring({ stiffness: 300, damping: 30 })`).

Flag immediately: `cubic-bezier(0.68,-0.55,0.27,1.55)` (elastic bounce) applied broadly.
Reserve elastic easing for semantically playful moments (games, celebrations).

### prefers-reduced-motion block (ship with the first animation)

```css
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}
```
