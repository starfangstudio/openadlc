---
name: web-performance
description: "This skill should be used when web performance is in scope, \"make the page faster\", \"improve Core Web Vitals\", \"fix LCP / INP / CLS\", \"the bundle is too big\", \"code-split this route\", \"lazy-load this component\", \"optimize images\", \"stop the layout shift\", \"fix the font flash (FOUT/FOIT)\", \"set a performance budget\", \"run Lighthouse\", \"measure web vitals in production\", or reviewing a change for speed. Framework-agnostic and detect-first across React, Vue, Svelte, and Angular: treat performance as a measurable bar (Core Web Vitals targets, a bundle budget, a failable check), not a vibe. Pairs with ssr-edge (what runs where), web-components (lazy boundaries), and adlc-design (image and font tokens)."
version: 0.1.0
---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# Web performance

Performance is a number, not a feeling. Set targets, measure against them, and fail the build when they regress. "It feels fast on my laptop" is not a passing bar; a laptop on fast wifi is the best case, real users are the median case.

## Step 1: Detect the stack first
Never impose tooling. Read `package.json` and the build config before prescribing anything:
- Framework and meta-framework: React / Next, Vue / Nuxt, Svelte / SvelteKit, Angular, Solid, Astro.
- Bundler: Vite, webpack, Rollup, esbuild, Turbopack. The bundle-analyzer and budget hooks differ per bundler.
- What renders where: SSR, SSG, CSR, or edge (see `ssr-edge`). The fastest byte is the one you never ship; server-rendered HTML beats a client round-trip for first paint.

Match the project's existing perf tooling. If a Lighthouse CI config or a budget file already exists, extend it, do not replace it.

## Step 2: Set the targets (Core Web Vitals)
The three Core Web Vitals are the user-facing bar. The pass rule is the **75th percentile** of real page views (at least 75% of views must hit "good"), so design for the median user, not your machine.

| Metric | What it measures | Good | Needs work | Poor |
| --- | --- | --- | --- | --- |
| **LCP** (Largest Contentful Paint) | Load speed: when the main content paints | **under 2.5s** | 2.5 to 4.0s | over 4.0s |
| **INP** (Interaction to Next Paint) | Responsiveness: input to visible response | **under 200ms** | 200 to 500ms | over 500ms |
| **CLS** (Cumulative Layout Shift) | Visual stability: unexpected movement | **under 0.1** | 0.1 to 0.25 | over 0.25 |

These are the targets the failable check (Step 7) enforces. Write them into the project's budget, not just this doc.

## Step 3: Set a bundle budget, then split and lazy-load
A budget is a hard number the build refuses to exceed. Pick concrete bytes (gzipped or brotli, the transfer size users actually pay):
- **Starting budget:** initial route JS under **~170 KB compressed**, total initial transfer under **~300 KB**. Tighten as you can; these are a ceiling, not a goal.
- **Code-split by route:** each route loads only its own code. Every meta-framework does this at the route boundary; lean on it (`next/dynamic`, Vue `defineAsyncComponent`, SvelteKit route chunks, Angular lazy routes, or a bare `import()`).
- **Lazy-load heavy, below-the-fold, or interaction-gated components:** modals, charts, rich editors, maps, anything not needed for first paint. Load on visibility or on interaction, not upfront (see `web-components` for the boundary).
- **Watch the big rocks:** date libraries, icon sets imported whole, moment-style mega-deps, duplicate React copies. Import members, not whole libraries; prefer a smaller dep or native APIs (`Intl`, `Temporal`).

The budget is meaningless without enforcement. Wire it into the bundler (webpack `performance.maxAssetSize`, a `vite-plugin-*` size check, or `bundlesize` / `size-limit` in CI) so a regression fails the build, not a reviewer's eyeball.

## Step 4: Image strategy (the usual LCP and CLS killer)
Images are typically the LCP element and a top CLS source. Fix both:
- **Reserve space:** always set `width` and `height` (or an `aspect-ratio`) on every `<img>`. The browser reserves the box before the pixels arrive, so nothing reflows. This is the single biggest CLS win.
- **Responsive sizes:** ship `srcset` + `sizes` so each device downloads a fitting resolution. Four widths (for example 400w, 800w, 1600w, 2400w) cover most real devices; more rarely helps.
- **Modern formats:** serve AVIF or WebP with a fallback via `<picture>` (AVIF, then WebP, then JPEG/PNG). They are far smaller than JPEG/PNG at equal quality.
- **Lazy below the fold, eager for the LCP image:** add `loading="lazy"` to below-the-fold images. Never lazy-load the LCP / hero image; instead mark it `fetchpriority="high"` (and consider a `<link rel="preload">`) so it paints sooner.

```html
<!-- LCP / hero image: eager, high priority, space reserved -->
<picture>
  <source type="image/avif" srcset="hero-800.avif 800w, hero-1600.avif 1600w" sizes="100vw">
  <source type="image/webp" srcset="hero-800.webp 800w, hero-1600.webp 1600w" sizes="100vw">
  <img src="hero-800.jpg" width="1600" height="900" fetchpriority="high" alt="...">
</picture>

<!-- Below the fold: lazy, space still reserved -->
<img src="card.webp" width="400" height="300" loading="lazy" alt="...">
```

If the framework has an image component (`next/image`, Nuxt `<NuxtImg>`, Astro `<Image>`), use it: it generates `srcset`, modern formats, and reserved dimensions for you. Do not hand-roll what the framework already does.

## Step 5: Font strategy (the silent CLS and FOIT source)
Web fonts cause invisible text (FOIT) or a reflow when the real font swaps in (a CLS spike). Two fixes, used together:
- **`font-display: swap`:** render text immediately in the fallback, swap to the web font when it loads. Kills FOIT; text is never invisible.
- **Metric-matched fallback:** swap alone moves text when metrics differ. Define an `@font-face` fallback over a system font and tune `size-adjust`, `ascent-override`, `descent-override`, and `line-gap-override` so the fallback occupies the exact same box as the web font. Zero reflow, zero font-driven CLS.

```css
@font-face {
  font-family: "Brand";
  src: url("/fonts/brand.woff2") format("woff2");
  font-display: swap;
}
/* Metric-matched fallback so the swap does not move text */
@font-face {
  font-family: "Brand Fallback";
  src: local("Arial");
  size-adjust: 107%;
  ascent-override: 90%;
  descent-override: 22%;
  line-gap-override: 0%;
}
/* body { font-family: "Brand", "Brand Fallback", sans-serif; } */
```

Do not eyeball the override percentages. Generate them: `next/font` computes them automatically (`next/font/google` or `next/font/local`), and the Capsize `createFontStack` helper does it for any stack. Also: `woff2` only, subset to the glyphs you use, self-host or `preconnect` to the font origin, and `preload` the one or two fonts above the fold.

## Step 6: Measure (lab and field)
Two kinds of data, both needed. Lab is reproducible and good for catching regressions; field is the truth about real users.
- **Lab (pre-merge):** run **Lighthouse** (CLI or `@lhci/cli`) or **PageSpeed Insights** against a built, production-like target. Throttle CPU and network so the number reflects a mid-range phone, not your machine.
- **Bundle (pre-merge):** run a **bundle analyzer** (`rollup-plugin-visualizer`, `webpack-bundle-analyzer`, `vite-bundle-visualizer`) to see what is in each chunk and catch a dependency that just doubled a route.
- **Field (production):** ship the **`web-vitals`** library and report real-user LCP, INP, and CLS to your analytics. Use `onLCP` / `onINP` / `onCLS`; the attribution build adds the element and timing that caused each bad value, so you fix the actual culprit.

```js
// Field measurement: report real-user vitals from production
import { onLCP, onINP, onCLS } from "web-vitals";

function report(metric) {
  navigator.sendBeacon("/analytics/vitals", JSON.stringify(metric));
}
onLCP(report);
onINP(report);
onCLS(report);
```

## Step 7: The failable check (the budget is a gate, not a hope)
Performance work is not done until a check passes or fails on its own. Wire at least one hard gate into CI:
- **CWV gate:** Lighthouse CI (`@lhci/cli autorun`) with assertions on the targets from Step 2. Example assertion: fail when LCP > 2.5s, INP/TBT over budget, or CLS > 0.1.
- **Bundle gate:** `size-limit` or `bundlesize` with the byte budget from Step 3, failing the build when a route's initial JS exceeds it.

```js
// lighthouserc.js: fail the build when a Core Web Vital regresses
module.exports = {
  ci: {
    assert: {
      assertions: {
        "largest-contentful-paint": ["error", { maxNumericValue: 2500 }],
        "cumulative-layout-shift": ["error", { maxNumericValue: 0.1 }],
        "total-blocking-time": ["error", { maxNumericValue: 200 }],
      },
    },
  },
};
```

A budget no check enforces is a wish. If nothing can fail, the work is not done.

## References
- What runs where, hydration cost, data fetching: `ssr-edge`. Lazy boundaries and the load-on-interaction pattern: `web-components`. Where derived state lives so re-renders stay cheap: `web-state`. The interaction and rendering tests that pair with the perf check: `web-testing`. Form responsiveness (INP under load): `web-forms`. Image and font tokens, responsive design intent: `adlc-design`. Keyboard and focus cost of lazy UI: `design-a11y`. Module boundaries that keep chunks clean: `software-design`.
