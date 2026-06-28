---
name: gate-traceability-check
description: "This skill should be used when the user asks to \"check traceability\", \"build a traceability matrix\", \"RTM\", \"requirement to test coverage\", \"which requirements have no tests\", \"are all requirements implemented and tested\", \"trace requirements to code\", or wants a requirement -> code -> test traceability gate before merge or release. Produces a coverage report flagging untested requirements, orphan code, and orphan tests."
version: 0.1.0
---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# Gate: Requirement -> Code -> Test Traceability Check

Build a traceability matrix that links every requirement to the code that implements it and the tests that verify it, then flag the gaps. This is a read-only quality gate: it reports, it does not edit code or push anything.

## When to run
Run before merging a non-trivial change or cutting a release, or whenever the user asks "is everything tested?" / "what's missing coverage?".

## Inputs (resolve before building the matrix)
Ask only for what is missing; infer the rest from the repo.
- **Requirement source**: where requirements/IDs live: a spec doc, ticket tracker (Jira/Linear/GitHub issues), acceptance criteria, or a `requirements/` dir. Each requirement needs a stable ID (e.g. `RQ-001`). If none exist, derive provisional IDs from headings/criteria and say so.
- **Code surface**: modules/files implementing the change (the diff under review, or named features).
- **Test surface**: test directories and the command that runs them.

## Procedure
1. **Enumerate requirements.** List every requirement with its ID and a one-line description. Mark `unknown` rather than inventing a requirement.
2. **Forward trace (requirement -> code -> test).** For each requirement, locate the implementing code (grep for the feature, follow the diff) and the test(s) that exercise it. Prefer linking by explicit reference (ticket ID in commit/test name, code comment) over guessing.
3. **Backward trace (code/test -> requirement).** For each touched code unit and each test, identify which requirement it serves. Anything that maps to nothing is an orphan.
4. **Classify each row** using the status values below.
5. **Emit the matrix and the gate verdict** in the exact format below.

## Status values
- `COVERED`: requirement has implementing code AND a test that verifies it.
- `UNTESTED`: requirement has code but no test (forward-trace gap).
- `UNIMPLEMENTED`: requirement has neither code nor test.
- `ORPHAN-CODE`: code unit maps to no requirement (built without a requirement).
- `ORPHAN-TEST`: test maps to no requirement (verifies nothing tracked).

## Report format (output exactly this shape)
```
## Traceability Matrix

| Req ID | Requirement | Code (file/symbol) | Test (id/name) | Status |
|--------|-------------|--------------------|----------------|--------|
| RQ-001 | <one line>  | path:symbol        | test name      | COVERED |
| RQ-002 | <one line>  | path:symbol        |, | UNTESTED |
| RQ-003 | <one line>  |, |, | UNIMPLEMENTED |

## Orphans
- ORPHAN-CODE: path:symbol: no requirement found
- ORPHAN-TEST: test name: no requirement found

## Gate verdict: PASS | FAIL
- Requirements: N total · X COVERED · Y UNTESTED · Z UNIMPLEMENTED
- Orphans: A code · B test
```

## CRITICAL gate rule: stop and report
- The gate is **FAIL** if any requirement is `UNTESTED` or `UNIMPLEMENTED`. Report FAIL plainly; do not soften it. List the exact gaps the user must close.
- Orphans are **warnings**, not automatic failures: surface every `ORPHAN-CODE`/`ORPHAN-TEST` for human judgment (could be dead code, an untracked requirement, or a scaffolding test).
- This skill **never edits code, writes tests, or pushes/posts anything**. It produces the report and stops. Any outbound action (committing fixes, updating a ticket, posting the matrix to a PR) is a separate step that must route through the operator's explicit consent.

## Verification of the gate itself
Before reporting `COVERED`, confirm the linked test actually runs and exercises that code path, run the named test (or the suite) and confirm it passes. A test that does not run is not coverage; downgrade to `UNTESTED` and note it.

## Heuristics for linking
- Trust explicit links first: requirement/ticket ID in a test name, commit message, or code comment.
- Then structural proximity: test file mirroring a source file (`Foo.kt` <-> `FooTest.kt`).
- Then behavioral match: a test whose assertions match the requirement's acceptance criteria.
- When a link is a guess, mark the cell with `?` and explain in the verdict notes rather than asserting `COVERED`.

## References
- Jama Software: How to Create and Use a Requirements Traceability Matrix (RTM): https://www.jamasoftware.com/requirements-management-guide/requirements-traceability/how-to-create-and-use-a-requirements-traceability-matrix-rtm/ (forward/backward traceability; orphan requirements, untested requirements, orphaned tests).
