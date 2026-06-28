---
name: ux-flows
description: >-
  This skill should be used when the user asks to "map the user flows", "define
  the information architecture", "list the screens we need", "build a screen
  inventory", "figure out what components we actually need", "design the
  navigation structure", "enumerate user goals before building screens", "create
  a flow diagram", "define entry and exit points for a feature", "produce a
  screen-state inventory", "derive a component list from the flows", or "prevent
  over-building UI components". Produces the UX spec (flows + IA + screen-state
  list + minimal component inventory) that feeds create-plan and the component
  build order. No code output; this is the envision-first, principles-first gate
  before any screen is implemented. Complements but does not duplicate
  design:user-research (research informs goals; this skill operationalises them
  into flows, screens, and the component scope guard).
version: 0.1.0
---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# UX flows

Map user goals to flows, flows to screens and states, and states to the minimal
component set -- before a single screen is built. This spec is the input to
`create-plan` and defines the component inventory scope: build only what the
flows require.

## Step 1: Detect existing flows, navigation, and routes

Never invent structure. Grep first:

```bash
# Existing navigation definitions (Compose Nav, SwiftUI NavigationStack, React Router)
grep -rn "NavHost\|NavigationStack\|createBrowserRouter\|Routes\|Route " \
  --include="*.kt" --include="*.swift" --include="*.tsx" . | head -40

# Feature entry points (screens / pages already named)
grep -rn "Screen\|Page\|Route\|Destination" \
  --include="*.kt" --include="*.swift" --include="*.tsx" . \
  | grep -v "test\|Test\|spec\|Spec" | head -40

# Existing flow or IA docs
find . -iname "*flow*" -o -iname "*ia*" -o -iname "*sitemap*" \
  -o -iname "*navigation*" | grep -v ".git" | head -20
```

Record what exists. Mark any unknown destination `unknown`. Do not invent route
names, tab labels, or screen names; ask if the detection returns nothing useful.

## Step 2: Enumerate primary user goals (jobs-to-be-done)

One line per goal: "As a [actor], I want to [action] so that [outcome]."

```
G1. Guest -> Browse product catalogue -> find what to buy
G2. Authenticated user -> Complete checkout -> receive confirmation
G3. Authenticated user -> Track order -> know delivery status
```

Keep the list to the scope the operator confirmed. No padding with edge cases at
this stage.

## Step 3: Map each goal to a flow

One table per goal. Entry is where the user starts; terminal nodes are Success,
Error, Empty, or Loading. Name sub-states (partial load, pagination, etc.) when
the feature warrants it -- "Loaded" alone is not sufficient.

```
Flow G1 -- Browse catalogue
  Entry: App launch (unauthenticated)
  1. Home screen [Loading | Empty | Loaded]
  2. Category filter -> filtered list [Empty | Loaded]
  3. Product detail [Loading | Loaded | Error: unavailable]
  Success: user taps "Add to cart"
  Error:   network failure -> inline retry
  Empty:   no results -> zero-state with CTA
```

## Step 4: Define the information architecture

Produce a flat hierarchy list derived from the flows. Indent for depth; do not
exceed three levels without explicit operator approval (deep hierarchies hurt
findability per NN/G IA principles).

```
Root navigation
  Home
  Catalogue
    Category (dynamic)
    Search results
  Product detail
  Cart
  Checkout
    Address entry / Payment / Confirmation
  Orders > Order detail
  Account > Profile / Settings
```

Note the navigation pattern detected (bottom tabs, drawer, stack-only, hybrid)
and confirm it matches existing platform conventions from Step 1. If nothing
exists yet, state the proposed pattern and rationale.

## Step 5: Produce the screen list with state inventory

One row per screen. Every distinct visual state the flows require must appear
here. A state missing here becomes a missing UI state later.

| Screen | States | Entry points | Exit points |
|---|---|---|---|
| Home | Loading, Empty, Loaded | App launch, Deep link | Catalogue, Search, Product |
| Category | Loading, Empty, Loaded, Error | Home, Nav tab | Product detail, Filter |
| Product detail | Loading, Loaded, Error: unavailable | Catalogue, Deep link | Cart, Back |
| Cart | Empty, Loaded | Product detail, Nav tab | Checkout, Continue |
| Checkout / Payment | Default, Processing, Error | Address | Confirmation |

Replace with actual screens; add rows as needed.

## Step 6: Extract the minimal component inventory (scope guard)

Scan the screen list and extract only the components the flows actually require.
This list is the build scope; nothing outside it gets built until a new flow
demands it. Organise by Atoms / Molecules / Organisms / Navigation.

```
Atoms:     Button (primary, secondary, destructive), TextInput (default, error),
           Badge (count, status), Skeleton (list item, card)
Molecules: ProductCard, OrderRow, EmptyState (icon + headline + CTA), InlineError
Organisms: ProductGrid (with pagination), CartSummary, CheckoutForm
Nav:       BottomTabBar, StackHeader
```

STOP: if the operator's platform is KMP/cross-platform, note which components
are shared and which are platform-specific. Do not assume sharing scope without
confirmation.

## Output format

Deliver a `## UX Flows Spec` block in chat (Goals, Flows, IA, Screen + State
Inventory, Component Inventory, Open questions), or write it to
`docs/ux/flows-<feature>.md` if the operator prefers a file. Do not generate
screens, components, or code at this stage.

For the full output template and exhaustive examples, see
[references/ux-flows-detail.md](references/ux-flows-detail.md).

## Outbound checkpoint

Local work needs no approval. Outbound here (posting the spec to Figma, a Confluence page, or a Linear issue): stop, present exactly what would go out, and get the operator's explicit "yes" first (global consent law).

## References

- Nielsen Norman Group, "Information Architecture vs. Sitemaps":
  https://www.nngroup.com/articles/information-architecture-sitemaps/
- Nielsen Norman Group, "IA Study Guide" (findability, scent, flat vs. deep
  hierarchies, card sorting, tree testing):
  https://www.nngroup.com/articles/ia-study-guide/
- Nielsen Norman Group, "User Journeys vs. User Flows" (video, 2023):
  https://www.nngroup.com/videos/user-journeys-vs-user-flows/
- Nielsen Norman Group, Information Architecture topic index:
  https://www.nngroup.com/topic/information-architecture/
- ux-flows examples, templates, and screen/component inventory formats:
  [references/ux-flows-detail.md](references/ux-flows-detail.md)
