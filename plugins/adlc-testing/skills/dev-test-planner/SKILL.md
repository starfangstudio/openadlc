---
name: dev-test-planner
description: >-
  This skill should be used when the user asks to "plan tests for this change",
  "what tests do we need", "design a test strategy", "how should we test this",
  "write a test plan", "what should the test pyramid look like here", or "which
  tests should I run for this module". Wraps the built-in testing-strategy skill
  to produce a pyramid-shaped, plan-anchored test plan plus the exact
  module-scoped commands to run it. Does NOT execute the suite or push anything.
version: 0.1.0
---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# Dev test planner

Turn an approved change into a **pyramid-shaped test plan** and the **exact,
module-scoped commands** that prove it. Planning only, this skill never runs the
full suite blind and never pushes or posts anything.

## What this wraps
This is a thin wrapper over the built-in **`engineering:testing-strategy`** skill.
Invoke that engine for the strategy-by-component-type analysis and the
test-pyramid framing. This skill adds only the ADLC delta:

- **Pyramid weighting is a gate, not a suggestion**: most coverage at the unit
  layer, fewer integration tests, a thin top of end-to-end tests.
- **Module-scoped commands**: every plan ends with the precise command to run the
  affected module's tests, never the whole repo.
- **Plan-anchored coverage**: every requirement and named edge case in the
  approved plan maps to at least one test.

## Workflow
1. **Establish the baseline.** Identify the change and the plan it must satisfy
   (the approved `spec.md` / plan, or the change description if none exists, say
   which). Identify the module(s) the diff touches.
2. **Run the engine.** Delegate to `engineering:testing-strategy` for the
   strategy-by-component-type breakdown and pyramid framing.
3. **Apply the pyramid gate** (below) to weight the plan correctly.
4. **Rank by risk** (below). Score each behavior likelihood x impact and test the
   highest-risk first; record what you are deprioritizing.
5. **Map coverage to the plan.** Every requirement and every named edge case
   (empty / boundary / error / loading) gets at least one test that asserts
   behavior, not implementation detail.
6. **Resolve the run commands** (below) for the touched module(s).
7. **Return the test plan** in the format below.

## Pyramid gate
Weight tests bottom-heavy. Reject a plan that inverts the pyramid (mostly E2E).

```
        /  E2E  \         Few, critical user journeys only
       / Integration \     Some, module boundaries, I/O, contracts
      /    Unit Tests  \   Many, fast, isolated, business logic
```

- **Unit (most)**: pure logic, branching, error paths, edge cases. Fast, no I/O.
- **Integration (some)**: module boundaries, DB / network / serialization,
  consumer contracts.
- **E2E (few)**: only business-critical end-to-end journeys; slow, high-confidence.

Cover: business-critical paths, error handling, edge cases, security boundaries,
data integrity. Skip: trivial getters/setters, framework code, one-off scripts.

## Risk-based prioritization
The pyramid says what *level* a test sits at; risk says what to test **first**. Score
each behavior on **likelihood** (will it break?) and **impact** (how bad if it does?),
each Low/Med/High. Risk = likelihood x impact; test the highest first.

| Raises likelihood | Raises impact |
|---|---|
| New / high-churn code, low existing coverage, complex or concurrent logic | Money, auth, PII, data loss or corruption, irreversible or silent failure |

Then **decide what NOT to test.** List the low-risk behaviors you are deprioritizing
(trivial pass-throughs, framework glue, already-covered paths) so the trade-off is
explicit: if testing is cut for time, this is the list that gets dropped, not a
high-risk path silently skipped.

## Module-scoped run commands
Always scope to the touched module, never run the whole suite for a focused
change. Resolve the project's actual runner first; defaults below.

| Stack | Module-scoped command |
|---|---|
| Android (Gradle) | `./gradlew :<module>:testDebugUnitTest` |
| JS / TS (Jest) | `npx jest <path-or-pattern>` |
| Python (pytest) | `pytest <path/to/test_file.py>` |
| Go | `go test ./<package>/...` |
| Rust (Cargo) | `cargo test -p <crate>` |

Running tests locally needs **no** approval, run them freely to verify. Only
pushing, opening a PR, or posting results elsewhere requires the operator's
explicit yes first.

## Test plan format
Emit exactly this. Keep it tight.

```
## Test plan: <change>
Module(s): <touched modules>   Plan: <spec ref | "change description (no spec)">

### Coverage (requirement → test)
- <requirement / edge case> → <unit|integration|e2e>: <test name / assertion>
- ...

### Pyramid check
Unit: <n>  Integration: <n>  E2E: <n>, <PASS bottom-heavy | INVERTED: rebalance>

### Deprioritized (not testing now)
- <low-risk behavior>: <why: trivial | framework glue | already covered by ...>

### Gaps
- <uncovered requirement or edge case, or "none">

### Run it
`<module-scoped command>`
```

## References
- Built-in `engineering:testing-strategy` (wrapped engine).
- Test pyramid: Martin Fowler, https://martinfowler.com/articles/practical-test-pyramid.html
