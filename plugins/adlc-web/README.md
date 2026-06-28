<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
# adlc-web

The web frontend domain pack. Framework-agnostic and detect-first. Pairs with `adlc-design` (tokens, a11y, Figma).

## Skills
- `web-components`: typed, framework-agnostic components; detect the framework first (React / Vue / Svelte / Angular), then follow its idioms.
- `web-state`: state management (local, shared, server-cache); pick the lightest option that fits.
- `web-testing`: component + interaction + a11y testing (Testing Library, Playwright).
- `web-forms`: forms, validation, accessible error handling.
- `ssr-edge`: the SSR / SSG / edge boundary (what runs where, hydration, data fetching).
- `web-performance`: Core Web Vitals, bundle budget, code-splitting, image and font strategy.

## Agents
- `web-architect`: design the app structure (routing, data flow, the SSR/CSR split, component boundaries). Read-only, produces a plan.
- `web-reviewer`: review web changes (correctness, a11y, performance, framework idioms) before any outbound step.

## Status
Stable. Detect-first skills and agents for building, testing, and shipping web frontends across React, Vue, Svelte, and Angular.
