---
name: test-architecture-conformance
description: "This skill should be used when the user asks to \"check our tests follow the pyramid\", \"are we over-testing?\", \"review test architecture\", \"is this test at the right level?\", \"audit the test suite shape\", \"find duplicated tests across layers\", or \"do these tests use arrange/act/assert?\". Audits a test suite or a diff against the practical test pyramid (lots of unit, some integration, very few E2E), the arrange/act/assert structure, and over-testing anti-patterns (ice-cream cone, cross-layer duplication, implementation-coupled tests). Read-only analysis that produces a findings report; it does not rewrite tests."
version: 0.1.0
---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# Test architecture conformance

Audit tests against the practical test pyramid and flag over-testing. Read-only: produce a report, never rewrite tests in this skill.

## Scope

Run on either a **diff** (new/changed tests in a PR) or a **whole suite** (periodic health check). Confirm which with the operator if ambiguous, then proceed.

## Procedure

1. **Locate tests.** Find test files and their layer. Use the project's conventions; common signals:
   - Unit: `src/test/`, `*Test.kt`, `*.test.ts`, `test_*.py` exercising one class/function with collaborators faked.
   - Integration: tests that touch a DB, real HTTP, filesystem, framework wiring, or multiple modules.
   - E2E / UI: tests that drive the whole app through its outer interface (browser, full app boot, device).
2. **Count the shape.** Tally tests per layer. The healthy shape is a pyramid: many unit, some integration, **very few** E2E. Compute rough proportions.
3. **Check each test for AAA structure** (see Checks below).
4. **Hunt over-testing** (see Checks below), this is the primary value of the skill.
5. **Emit the report** in the exact format below. Do not edit test files.

## Checks

### Pyramid shape
- FLAG **ice-cream cone**: E2E/UI tests outnumber or rival unit tests. "Push your tests as far down the test pyramid as you can."
- FLAG a test sitting **too high**: an edge case / conditional branch verified only through an E2E or integration test when a unit test would give the same confidence faster. Recommend pushing it down.
- FLAG a **gap**: behavior that crosses an integration boundary (DB, serialization, real HTTP) covered only by unit tests with everything faked, green units, real-world breakage.

### Over-testing (cross-layer duplication)
- FLAG the **same edge cases / conditional logic re-asserted at a higher layer** when lower-level tests already cover them. "You don't test all the conditional logic and edge cases that your lower-level tests already cover in the higher-level test again." Recommend deleting the higher-level duplicate.
- FLAG **redundant E2E variants** that differ only in data already covered by a unit/integration parametrized test.

### Arrange / Act / Assert
- FLAG tests with no clear arrange → act → assert (or given/when/then) separation, hard to read, usually doing too much.
- FLAG tests asserting **more than one condition / behavior**. "Test one condition per test." Multiple unrelated asserts = split it.
- FLAG **implementation-coupled** tests: asserting internal call sequences, private state, or mock-interaction order instead of observable behavior. "Test for observable behaviour instead. Don't reflect your internal code structure within your unit tests." Ask: "if I enter x and y, is the result z?"

## Report format

Emit exactly this structure. One row per finding. If a category is clean, write "None found."

```
## Test architecture conformance: <diff | full suite>

### Pyramid shape
Unit: <n>  Integration: <n>  E2E/UI: <n>   → shape: <pyramid | top-heavy | hourglass | ...>
<one-line verdict>

### Findings
| # | Severity | Category            | Location (file:test) | Issue | Recommendation |
|---|----------|---------------------|----------------------|-------|----------------|
| 1 | high     | over-testing        | …                    | …     | delete / push down / split |

### Summary
- Push down: <count>   Delete duplicate: <count>   Split (AAA / multi-assert): <count>   Decouple from impl: <count>   Coverage gap: <count>
- Top recommendation: <one sentence>
```

Severity guide: **high** = misleading confidence or a coverage gap that hides real bugs; **medium** = slow/brittle duplication or wrong-layer placement; **low** = readability (AAA, naming).

## Guardrails
- Read-only. This skill **reports**; it does not modify tests. If the operator wants fixes applied, that is a separate change that goes through the normal implement → verify → review loop.
- Do not invent a target ratio. The pyramid is about relative proportions ("lots / some / very few"), not a fixed percentage. Judge shape, not an arbitrary quota.
- Deleting tests is a real recommendation here, but only when a lower-level test already covers the exact condition. Never recommend deleting a higher-level test that adds genuine integration confidence.

## References
- Ham Vocke, "The Practical Test Pyramid", martinfowler.com, https://martinfowler.com/articles/practical-test-pyramid.html (pyramid proportions, "push tests down", delete cross-layer duplicates, one condition per test, test observable behaviour, ice-cream-cone anti-pattern).
- Martin Fowler, "TestPyramid" (bliki): https://martinfowler.com/bliki/TestPyramid.html
