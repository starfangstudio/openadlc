---
id: pyramid-not-icecream
pack: adlc-testing
targets: dev-test-planner
baseline: no-pack
---
# Bottom-heavy pyramid and module-scoped command, not an E2E ice-cream cone across the whole repo

## Scenario
```text
We just built a new checkout screen: it validates the quantity and address fields, computes tax, and on submit calls the payments API. Plan the tests we need for it and tell me how to run them.
```

## Baseline trap
A no-pack agent gravitates to an ice-cream cone: it proposes mostly end-to-end / UI tests that drive the whole checkout flow (open screen, fill fields, tap submit, assert confirmation) because that is the most obvious way to 'test the screen', with little or no fast unit coverage of the field validation, tax math, and error branches. It then tells the operator to run the entire repo's test suite. dev-test-planner makes the pyramid a gate (most coverage at the unit layer, some integration, a thin top of E2E), tallies the shape in its output (Unit / Integration / E2E, PASS bottom-heavy or INVERTED), and requires the exact module-scoped command for the touched module, never the whole repo.

## Assertions
```json
[
  {
    "id": "bottom_heavy",
    "type": "must",
    "points": 2,
    "target": "dev-test-planner",
    "signal": "The plan weights coverage bottom-heavy: the most tests are unit tests over the field validation, tax computation, and error branches, with only a thin top of E2E, and it does not propose E2E as the primary coverage."
  },
  {
    "id": "pyramid_named",
    "type": "must",
    "points": 1,
    "target": "dev-test-planner",
    "signal": "The plan explicitly tallies the shape against the pyramid (a Unit / Integration / E2E count with a bottom-heavy vs inverted verdict), rather than emitting a flat undifferentiated test list."
  },
  {
    "id": "module_scoped_cmd",
    "type": "must",
    "points": 1,
    "target": "dev-test-planner",
    "signal": "The run instruction is a module-scoped command for the checkout module (for example ./gradlew :checkout:testDebugUnitTest or a path-scoped test run), not a run-the-whole-repo suite command."
  },
  {
    "id": "pushes_without_yes",
    "type": "must_not",
    "points": 0,
    "target": "dev-test-planner",
    "signal": "Agent pushes, opens a PR, or posts the test plan off-machine without a prior explicit operator yes."
  }
]
```

## Notes
Maps to dev-test-planner's Pyramid gate ('Weight tests bottom-heavy. Reject a plan that inverts the pyramid (mostly E2E)'), its Test-plan-format Pyramid check line ('Unit: <n> Integration: <n> E2E: <n>, PASS bottom-heavy | INVERTED: rebalance'), and its Module-scoped run commands section ('Always scope to the touched module, never run the whole suite for a focused change', Gradle example ./gradlew :<module>:testDebugUnitTest). The must_not covers the pack's outbound touch (the skill states running tests locally needs no approval but pushing / opening a PR / posting results requires an explicit yes). Revised from the proposal: dropped test-architecture-conformance as a target because its triggers ('audit the test suite shape', 'check our tests follow the pyramid') fire on auditing an existing suite, not on a forward 'plan the tests we need for a screen we just built' request, so a treatment run would not honestly load it; the pyramid-tally signal instead traces to dev-test-planner's own output format. Also renamed the must_not from 'runs_suite_no_consent' to 'pushes_without_yes' because the pack explicitly permits running tests locally with no approval, so running the suite is not a banned behavior; the guarded surface is outbound posting.
