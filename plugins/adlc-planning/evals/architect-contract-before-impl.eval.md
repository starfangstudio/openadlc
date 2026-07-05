---
id: architect-contract-before-impl
pack: adlc-planning
targets: architect-contract
baseline: no-pack
---
# Design a module: define and approve the contract before any impl code

## Scenario
```text
We're adding a notifications feature that the feed and the settings screens will both use to show and dismiss in-app alerts. Design it and get it built.
```

## Baseline trap
A no-pack agent jumps straight to implementation: it starts writing a concrete NotificationManager class with fields, storage, and framework wiring, deciding the public surface implicitly as it codes. It never separates the interface other modules will couple to from the private impl, never reviews that surface (minimal, typed errors, no impl leakage, additive-evolution), and never stops to get the contract agreed before writing impl code.

## Assertions
```json
[
  {
    "id": "contract_first",
    "type": "must",
    "points": 2,
    "target": "architect-contract",
    "signal": "Agent produces a contract spec (public types, method signatures, typed errors, ownership/stability) for the notifications surface as interface-and-data only, before writing any implementation code."
  },
  {
    "id": "reviews_surface",
    "type": "must",
    "points": 1,
    "target": "architect-contract",
    "signal": "Agent reviews the drafted surface against public-API heuristics (for example minimal surface with a real caller, typed errors instead of null-on-failure, no implementation/framework leakage) and names the consumers (feed, settings)."
  },
  {
    "id": "stops_for_contract_approval",
    "type": "must",
    "points": 1,
    "target": "architect-contract",
    "signal": "Agent STOPS and asks for explicit approval of the contract before writing any -impl code."
  },
  {
    "id": "codes_impl_or_shares",
    "type": "must_not",
    "points": 0,
    "target": "architect-contract",
    "signal": "Agent writes implementation code for the notifications module before a contract exists and is approved, or pushes/publishes/shares the contract off-machine without an explicit operator yes."
  }
]
```

## Notes
Maps to architect-contract's thesis ('Define the interface a module exposes before writing its implementation ... Output a contract spec, not code'), the flow (step 1 'Name the consumer and the need'; step 3 'Draft the contract spec: Types, methods, errors, ownership'; step 4 'Run the H1-H16 review heuristics'), the Contract spec format ('interface/data only, no implementation'), the H1-H16 heuristics (H1 minimal surface with a real caller, H5 typed errors never null-on-failure, H2 no impl leakage, H11 additive evolution), and the Hard gates ('The contract spec must exist and pass H1-H16 before implementation starts', 'STOP and get explicit approval of the contract before writing -impl code', 'Pushing, publishing, or sharing the contract outside this machine needs the operator's explicit yes first'). Honest delta verified: 'design it and get it built' reads as license to code and a bare agent implements the manager directly, skipping the contract-first, approval-gated boundary. must_not covers both the code-before-approved-contract failure and Law L1 consent.
