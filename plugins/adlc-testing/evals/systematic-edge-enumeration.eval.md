---
id: systematic-edge-enumeration
pack: adlc-testing
targets: test-scenario-expander
baseline: no-pack
---
# Systematic EP / BVA / error-path enumeration, not a shallow happy-path list

## Scenario
```text
Our order form has a quantity field: a whole number the user can set from 1 to 99. On submit it reserves stock by calling the inventory service. What test cases do I need for the quantity field?
```

## Baseline trap
A no-pack agent produces a short, happy-path-heavy list: a couple of valid quantities (say 1, 5, 99) and maybe 'too big' and 'zero', with no systematic method. It typically misses the three-value boundaries on both edges (0 and 2 around the min, 98 and 100 around the max), non-integer / non-numeric / empty inputs, and the dependency and error paths (the inventory service timing out or returning 5xx, a double-submit / idempotency race). test-scenario-expander applies equivalence partitioning, then 3-value boundary analysis on both edges, then an explicit error and dependency path pass, and emits a deduplicated coverage matrix, calling out any bound it cannot confirm as an open question rather than inventing it.

## Assertions
```json
[
  {
    "id": "both_edge_boundaries",
    "type": "must",
    "points": 2,
    "target": "test-scenario-expander",
    "signal": "The scenarios include three-value boundary cases on BOTH edges of the 1-99 range (values around the min such as 0, 1, 2 and around the max such as 98, 99, 100), not just a couple of interior valid values."
  },
  {
    "id": "invalid_and_empty",
    "type": "must",
    "points": 1,
    "target": "test-scenario-expander",
    "signal": "The scenarios include invalid-partition and empty/absent inputs for the field (for example a non-integer or non-numeric value, and an empty or missing quantity), not only valid numbers."
  },
  {
    "id": "dependency_error_path",
    "type": "must",
    "points": 1,
    "target": "test-scenario-expander",
    "signal": "The scenarios include at least one dependency-failure or error path for the inventory-service call (for example a timeout or 5xx, or a double-submit / idempotency case), as a first-class scenario."
  },
  {
    "id": "invents_a_bound",
    "type": "must_not",
    "points": 0,
    "target": "test-scenario-expander",
    "signal": "Agent invents a concrete limit or behavior the prompt did not state (for example a max-length or a specific retry count) and presents it as fact instead of listing it as an open question."
  }
]
```

## Notes
Maps to test-scenario-expander's workflow steps Partition (EP checklist: valid and invalid classes plus 'Empty / absent'), Boundaries ('3-value BVA by default: the boundary, one below, one above' on every ordered partition, both edges), and Error & exception paths ('Dependency failures: downstream timeout, 4xx/5xx ...' and 'State/concurrency: double-submit / idempotency'), plus the Inputs rule 'Mark anything not given as unknown: never invent a range, limit, or error behavior ... list it as an open question'. The must_not guards that no-invented-bound rule, the pack's correctness-honesty surface here (fabricating an untested-but-asserted limit) rather than an outbound one. Honest trap: a bare agent asked 'what test cases do I need' routinely returns a shallow interior-value list and skips both-edge boundaries and dependency/error paths. The scenario states the 1-99 range so BVA has real edges to find but does not name EP/BVA or list the edge values, so it does not leak the answer.
