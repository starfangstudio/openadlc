---
name: web-components
description: "This skill should be used when building or refactoring a web UI component, \"create a component\", \"build this button/card/modal\", \"make a typed component\", \"where should this component's state live\", \"turn this Figma frame into a component\", \"make this reusable\", or reviewing component structure. Framework-agnostic and detect-first across React, Vue, Svelte, and Angular: write small, typed, accessible, token-driven components with a clear props-in / events-out contract. Pairs with web-state (shared state), web-testing (the check), and adlc-design (tokens, a11y, Figma)."
version: 0.1.0
---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# Web components

Build small, typed, accessible components that match the project's framework, not your favorite one. Composition over configuration; a clear contract over cleverness.

## Step 1: Detect the framework first
Never impose a stack. Read `package.json` and an existing component before writing:
- React / Next, Vue / Nuxt, Svelte / SvelteKit, Angular, Solid, or plain web components.
- The component conventions in use (file layout, naming, styling approach, state library). Match them.

If the repo has a design system or component library, reuse it (see `adlc-design` and Code Connect) before building anything new.

## Step 2: Define the contract
A component is a typed boundary: **props in, events out, slots/children for composition.**
- **Props (in):** typed, minimal, named for intent. Prefer a few well-named props over a god-object. Controlled vs uncontrolled: decide who owns the state and document it.
- **Events (out):** typed callbacks / emits for everything the parent must react to. Do not reach up; emit.
- **Slots / children:** pass children for layout flexibility rather than a boolean for every variant.

Keep one responsibility per component. If props sprawl past 5 to 7, or it does two jobs, split it.

## Step 3: Write it idiomatically (per framework)
- **React:** function component + hooks; typed props (a TS interface); derive state, do not duplicate it; memoize only a measured hot path.
- **Vue:** SFC with `<script setup>`, typed `defineProps` / `defineEmits`; computed over watchers.
- **Svelte:** typed props (`$props()` runes or `export let`); reactive declarations; minimal stores.
- **Angular:** standalone component; typed `@Input()` / `@Output()`; `OnPush` change detection.

Composition over inheritance everywhere. No business logic in the component; call into the domain (see `software-design`).

## Step 4: Style from tokens, not hardcodes
Use the design system's tokens and the project's idiomatic styling (CSS modules, Tailwind, scoped styles, CSS-in-JS). Never hardcode a hex, font, or spacing value (see `adlc-design` and `design-tokens`). Cover the states the design defines: hover, focus, disabled, loading, empty, error.

## Step 5: Accessibility is part of "done"
Semantic HTML first (`button`, `a`, `label`, `nav`); ARIA only to fill a real gap, never to paper over the wrong element. Keyboard reachable and operable; visible focus; a label for every control. See `design-a11y`.

## Step 6: Verify
The failable check is a component test (see `web-testing`): it renders, the props drive the output, the events fire, and the a11y smoke check passes. A component with no test is not done.

## References
- Shared / server state: `web-state`. The check: `web-testing`. Tokens, a11y, Figma: `adlc-design`, `design-a11y`. Design boundaries: `software-design`.
