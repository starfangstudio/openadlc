<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
Consumed by the `ux-flows` skill. Load on demand; do not load independently.

---

## Step 2: Goal enumeration example

One line per goal: "As a [actor], I want to [action] so that [outcome]."

```
G1. Guest -> Browse product catalogue -> find what to buy
G2. Authenticated user -> Complete checkout -> receive confirmation
G3. Authenticated user -> Track order -> know delivery status
```

---

## Step 3: Flow table example

One table per goal. Entry = where the user starts; terminal nodes = Success, Error, Empty, or Loading.

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

"Loaded" alone is not sufficient; name sub-states (partial load, pagination loading, etc.) when the feature warrants it.

---

## Step 4: Information architecture example

Flat hierarchy list derived from flows. Indent for depth; do not exceed three levels without explicit operator approval.

```
Root navigation
  Home
  Catalogue
    Category (dynamic)
    Search results
  Product detail
  Cart
  Checkout
    Address entry
    Payment
    Confirmation
  Orders
    Order detail
  Account
    Profile
    Settings
```

Note the navigation pattern detected (bottom tabs, drawer, stack-only, hybrid) and confirm it matches platform conventions from Step 1.

---

## Step 5: Screen + state inventory table

One row per screen. Every distinct visual state the flows require must appear here.

| Screen | States | Entry points | Exit points |
|---|---|---|---|
| Home | Loading, Empty, Loaded | App launch, Deep link | Catalogue, Search, Product |
| Category | Loading, Empty, Loaded, Error | Home, Nav tab | Product detail, Filter |
| Product detail | Loading, Loaded, Error: unavailable | Catalogue, Search, Deep link | Cart, Back |
| Cart | Empty, Loaded | Product detail, Nav tab | Checkout, Continue shopping |
| Checkout / Address | Default, Validation error | Cart | Payment |
| Checkout / Payment | Default, Processing, Error | Address | Confirmation |
| Confirmation | Success | Payment | Orders, Home |

Replace with actual screens; add rows as needed. A state that appears in the flow but is missing here will become a missing UI state later.

---

## Step 6: Component inventory example

Scan the screen list and extract only what the flows require. This is the build scope.

```
Component inventory (derived from flows above)
  Atoms
    Button (primary, secondary, destructive)
    TextInput (default, error, disabled)
    Badge (count, status)
    Skeleton (list item, card)
  Molecules
    ProductCard (image, title, price, CTA)
    OrderRow (id, status, date)
    EmptyState (icon, headline, body, CTA)
    InlineError (message, retry action)
  Organisms
    ProductGrid (ProductCard list + pagination)
    CartSummary (line items + totals)
    CheckoutForm (TextInput group + validation)
  Navigation
    BottomTabBar (Home, Catalogue, Cart, Orders, Account)
    StackHeader (title, back, actions)
```

For KMP/cross-platform: note which components are shared (Compose Multiplatform or React cross-target) and which are platform-specific (SwiftUI-only, Android-only). Do not assume sharing scope without confirmation.

---

## Output format template

Deliver this block in chat or write to `docs/ux/flows-<feature>.md`:

```
## UX Flows Spec -- <feature / product name>

### Goals
[G1 ... Gn]

### Flows
[Flow per goal, Step 3 format]

### Information Architecture
[Hierarchy list, Step 4 format]

### Screen + State Inventory
[Table, Step 5 format]

### Component Inventory (scope guard)
[Atoms / Molecules / Organisms / Navigation, Step 6 format]

### Open questions
[Any unknown marked in Steps 1-6 that blocks proceeding]
```
