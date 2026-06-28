---
name: ssr-edge
description: "This skill should be used when deciding what runs on the server versus the client, \"should this be a server or client component\", \"where should I fetch this data\", \"set up SSR / SSG / ISR\", \"render this route on the edge\", \"fix a hydration mismatch\", \"window is not defined during SSR\", \"stream this slow page\", \"keep this API key off the client\", \"make this route static\", or reviewing the server/client boundary. Framework-agnostic and detect-first across Next, Nuxt, SvelteKit, Angular SSR, and React Router / Remix: fetch on the server by default, push the boundary as low as possible, keep secrets and heavy work server-side. Pairs with web-state (where state lives), web-performance (cost of the choice), and web-components (the split in practice)."
version: 0.1.0
---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# SSR and the edge boundary

Decide what runs where: server, client, or build. The default is server. Push interactivity to the client only at the leaf that needs it, keep data fetching and secrets on the server, and pick the rendering mode per route, not per app.

## Step 1: Detect the meta-framework first
Never impose a rendering model. Read `package.json` and the routing/config files before writing:
- **Next (App Router):** `next` dependency, an `app/` directory. Server Components are the default; `'use client'` opts a subtree into the client. Rendering is per route (static, dynamic, edge, PPR).
- **Nuxt 3 / 4:** `nuxt` dependency, `nuxt.config.ts`. SSR by default; `useFetch` / `useAsyncData` for isomorphic fetching; `routeRules` for per-route mode.
- **SvelteKit:** `@sveltejs/kit`, `+page`/`+layout` files. `+page.server.ts` is server-only; `+page.ts` is universal (server then client).
- **Angular SSR:** `@angular/ssr`, `provideClientHydration()` in the bootstrap providers. SSR plus hybrid prerender; full hydration by default, incremental hydration opt-in.
- **React Router 7 / Remix:** `react-router` (framework mode) or `@remix-run/*`. `loader` runs on the server; `clientLoader` runs in the browser.
- **No meta-framework (plain SPA / Vite):** there is no server. Everything is client-rendered; this skill mostly does not apply (see `web-performance` for the SPA cost).

Match the framework's idioms. If the project already has a server/client convention, follow it.

## Step 2: Fetch data on the server by default
Server-first fetching is faster (closer to the data, no client round-trip), safer (secrets stay server-side), and avoids waterfalls. Put the fetch where the framework runs it on the server:
- **Next:** fetch inside an `async` Server Component; pass the result down as props.
- **Nuxt:** `useFetch` / `useAsyncData` in `setup`; the payload is serialized into the HTML so the client does not refetch. Avoid bare `$fetch` in `setup`, it double-fetches and breaks hydration.
- **SvelteKit:** `load` in `+page.server.ts` (private data / secrets) or `+page.ts` (public API, no secrets); return data to the page.
- **Angular:** fetch in the component / resolver; `provideClientHydration()` with transfer-cache so the client reuses the server's response instead of refetching.
- **React Router / Remix:** `loader` for server data; `clientLoader` only when the data must come from the browser.

Fetch client-side only when the data depends on user interaction, is user-private and not needed for first paint, or must not be in the SSR payload. For that case use the cache layer in `web-state`.

## Step 3: Draw the server/client split low
Server renders to HTML; client adds interactivity. Keep as much as possible on the server and mark only the interactive leaf as client:
- **Next:** start every component on the server. Add `'use client'` at the smallest leaf that needs state, effects, event handlers, or browser APIs. A Server Component can render a Client Component, but a Client Component cannot import a Server Component, it can only receive one as `children`/props. Use that to keep a server-rendered subtree inside a client shell.
- **Nuxt:** components are isomorphic; isolate client-only UI with `<ClientOnly>` and server-only render with a `.server.vue` component when supported.
- **SvelteKit:** components run on both sides; guard browser-only code (see Step 4).
- **Angular:** one component tree renders on both server and client; guard platform-specific code with `isPlatformBrowser`.

Rule of thumb: data and layout server-side, interactivity client-side, and make the client boundary a leaf, not the root.

## Step 4: Survive hydration
Hydration attaches the client app to the server-rendered HTML. The server HTML and the first client render must match, or you get a hydration mismatch (flicker, console error, or a wiped subtree). Common causes and fixes:
- **Client-only APIs at module/render top level:** `window`, `document`, `localStorage`, `navigator` are undefined on the server. Read them inside an effect / `onMount` / `isPlatformBrowser`, never during the render that the server also runs.
- **Non-deterministic values:** `Date.now()`, `Math.random()`, locale-formatted dates, `crypto.randomUUID()` differ between server and client. Compute them on one side (pass server value as a prop) or defer to after mount.
- **Invalid HTML nesting** (a `<div>` inside a `<p>`, a block inside an inline element): the browser repairs the DOM, so it no longer matches the server tree. Fix the markup.
- **Branching on `typeof window`** during render: produces two different trees. Render the same shell on both sides, then update after mount.

Verify by loading the route with JS enabled and watching for a hydration warning in the console; there should be none.

## Step 5: Stream the slow parts
Do not let one slow query block the whole page. Stream the fast shell first and fill slow regions as they resolve:
- **Next:** wrap the slow Server Component in `<Suspense fallback={...}>`; the shell flushes immediately and the boundary streams in. This is also the unit of Partial Prerendering (static shell, dynamic holes).
- **SvelteKit:** return a promise from `load` (top-level awaits block; nested promises stream) and resolve it with `{#await}` in the page.
- **React Router / Remix:** return un-awaited promises from the `loader` and render them with `<Await>` / `Suspense`.
- **Nuxt / Angular:** lazy-load below-the-fold regions; defer non-critical hydration (Angular incremental hydration, Nuxt lazy components).

Streaming improves perceived load (see `web-performance`); keep the shell meaningful, not a full-page spinner.

## Step 6: Choose the rendering mode per route
Pick the cheapest mode each route can tolerate. Decision order: **static, then ISR/SWR, then server, then edge, then client.**
- **Static (SSG / prerender):** content is the same for everyone and changes rarely (marketing, docs). Next: static by default + `generateStaticParams`. Nuxt: `routeRules: { '/': { prerender: true } }`. SvelteKit: `prerender = true`. Angular: prerender at build.
- **ISR / SWR (static + periodic revalidate):** mostly static but updates on a cadence (a blog index, a catalog). Next: `revalidate` (Node runtime only). Nuxt: `routeRules: { '/blog/**': { isr: 3600 } }` or `swr`.
- **Server (SSR per request):** per-request or per-user data, fresh on every load (dashboard, search). The default for dynamic routes.
- **Edge:** server logic that benefits from running close to the user and uses only edge-compatible APIs (no Node-only modules); good for geo/auth redirects and light personalization. Keep Node-only work (most ORMs, `fs`, ISR) on the Node runtime.
- **Client (CSR / `ssr: false`):** highly interactive, SEO-irrelevant, behind auth (an admin panel). Next: a `'use client'` subtree fetching after mount. Nuxt: `routeRules: { '/admin/**': { ssr: false } }`. SvelteKit: `ssr = false`.

Mix modes across routes in one app; do not force a single mode globally.

## Step 7: Keep secrets and heavy work server-side
Anything that ships to the client is public. Enforce the boundary:
- **Secrets:** API keys, DB URLs, tokens live only in server-only files (`+page.server.ts`, Server Components, `loader`, server env without the public prefix). Public env needs an explicit prefix (`NEXT_PUBLIC_`, `NUXT_PUBLIC_`, `PUBLIC_`, Vite `VITE_`); assume anything else must never reach the bundle.
- **Heavy work:** DB queries, large dependencies, data transforms, HTML sanitization run on the server so they never bloat the client bundle or expose internals.
- **Never** import a secret-bearing module into a client component or a universal file that also runs in the browser; the bundler will inline it and leak it.

This is a consent and security boundary, not just an optimization. When unsure whether a value is client-exposed, treat it as exposed.

## Step 8: Verify
The failable checks for this boundary:
- The route loads with **no hydration warning** in the console.
- **No secret** appears in the client bundle (grep the built client output for the key/value; it must be absent).
- With **JS disabled**, server/static routes still render their content (SSR/SSG works); client-only routes degrade as intended.
- The chosen mode holds: a static route serves prebuilt HTML, an ISR route revalidates on cadence, an edge route uses only edge-safe APIs.

A boundary with a hydration warning or a leaked secret is not done.

## References
- Where state lives and the server-cache layer for client fetches: `web-state`. The cost of each rendering choice (bundle, Core Web Vitals, streaming): `web-performance`. The server/client split inside a component: `web-components`. Forms across the server boundary (actions, progressive enhancement): `web-forms`. The check: `web-testing`. App structure and the SSR/CSR split at the architecture level: `software-design`. Tokens and accessibility: `adlc-design`, `design-a11y`.
