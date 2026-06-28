---
name: web-state
description: "This skill should be used when deciding where state lives or wiring state in a web app, \"manage state\", \"add a store\", \"where should this state go\", \"share state between components\", \"fetch and cache server data\", \"this prop is drilling too deep\", \"should I use Redux/Zustand/Pinia\", \"add React Query / TanStack Query / SWR\", \"my state is out of sync\", or reviewing a state layer. Framework-agnostic and detect-first across React, Vue, Svelte, and Angular: split state into local, shared, and server-cache, then pick the lightest tool for each. Pairs with web-components (the contract), web-testing (the check), and software-design (boundaries)."
version: 0.1.0
---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# Web state

Most state bugs are a placement problem, not a library problem. Put each piece of state in the right bucket first; the tool follows. The split most builds get wrong: treating server data as app state.

## Step 1: Detect the framework first
Never impose a stack. Read `package.json` before writing:
- The framework: React / Next, Vue / Nuxt, Svelte / SvelteKit, Angular, Solid.
- What is already wired: a store library (Redux Toolkit, Zustand, Pinia, NgRx) and a server-cache library (TanStack Query, SWR, RTK Query, Apollo). Match what exists before adding anything.

If a tool already covers a bucket, use it. Do not add a second state library to do the same job.

## Step 2: Sort the state into three buckets
Every piece of state is one of these. Name the bucket before you write a line.
- **Local:** used by one component (and maybe its children). A modal's open flag, an input's value, a hover state. Lives in the component.
- **Shared (app) state:** client-owned data several distant components need. Theme, auth session, a cart, a wizard's cross-step answers. Lives in a store or context.
- **Server-cache:** data the server owns and can change without you. Lists, profiles, anything from an API. It is a **cache of remote truth, not app state.** Lives in a server-cache library.

The question that sorts it: **who owns this data?** If the server owns it, it is server-cache, full stop.

## Step 3: Keep it local; lift only when truly shared
Default to the smallest scope. Lifting state too early is the most common mistake here.
- Start local. Lift to shared **only** when two components that are not parent-and-child both need it.
- Lifting one level to a common parent (passing props down) is fine and is not "shared state". Reach for a store only when prop-passing crosses many levels or unrelated branches.
- **Derive, do not store.** If a value can be computed from existing state, compute it. Never keep a second copy in sync by hand. Duplicated state is the bug.

## Step 4: Pick the tool per bucket (per framework)
Lightest option that fits. Do not pull in a heavy store for a flag.

**React**
- Local: `useState`; `useReducer` when transitions are complex or interdependent.
- Shared: `Context` for low-frequency values (theme, locale, auth). For complex or high-frequency shared state, **Zustand** (light) or **Redux Toolkit** (large, structured). Context is not a state manager; it re-renders all consumers, so do not run a hot store through it.
- Server-cache: **TanStack Query** or **SWR**. Do not copy fetched data into `useState` or a store.

**Vue**
- Local: `ref` / `reactive` in the component.
- Shared: **Pinia** (setup stores: `ref` + `computed` + actions). `provide` / `inject` for static, low-frequency values.
- Server-cache: **TanStack Query (Vue)**.

**Svelte**
- Local: `$state` / `$derived` runes in the component.
- Shared: `$state` exported from a `.svelte.js` / `.svelte.ts` module, or a store. (Stores are not deprecated in Svelte 5; runes are the default for new code.)
- Server-cache: **TanStack Query (Svelte)**, or SvelteKit `load` plus invalidation.

**Angular**
- Local: **signals** (the default for component state in Angular 19+).
- Shared: a service holding signals, provided at the right injector scope. **NgRx** only for large, structured app state.
- Server-cache: a service over `HttpClient`; use **RxJS** where it earns its keep (async streams, websockets, debounced input). Signals for the value, RxJS for the stream.

## Step 5: Never duplicate server data into app state
This is the rule that prevents the most bugs.
- The server-cache library **is** your store for remote data: it owns caching, background refetch, loading and error states, and invalidation. Read from it directly; do not mirror it.
- Need a tweaked view of server data (filtered, sorted, joined)? **Derive** it at read time. Do not write the derived copy back into a store.
- Client state and server-cache can coexist (for example Zustand for UI, TanStack Query for data). They stay separate; neither holds the other's data.

## Step 6: Verify
The failable check (see `web-testing`): drive the state through its transitions and assert the UI reflects it, with **no manually-synced duplicate**. A test that proves a server refetch updates the screen without a hand-written copy is the one that catches this category. State you cannot exercise in a test is not done.

## References
- The component contract (props in, events out): `web-components`. The check: `web-testing`. Forms and their validation state: `web-forms`. Server data at the SSR / hydration boundary: `ssr-edge`. Re-render and bundle cost of a store choice: `web-performance`. Domain boundaries and where logic lives: `software-design`. Tokens and a11y: `adlc-design`, `design-a11y`.
