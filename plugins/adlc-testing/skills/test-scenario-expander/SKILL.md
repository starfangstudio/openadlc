---
name: test-scenario-expander
description: "This skill should be used when the user asks to \"expand this feature into test scenarios\", \"what test cases do I need for X\", \"enumerate edge cases\", \"find the boundary cases\", \"list error paths to test\", \"what am I missing in my tests\", or \"turn this spec/acceptance criteria into a test matrix\". Systematically derives test scenarios from a feature using equivalence partitioning, boundary value analysis, and error-path enumeration, then emits a coverage matrix. Analysis-only; writes no tests and runs nothing."
version: 0.1.0
---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# Test scenario expander

Turn one feature description into a complete, non-redundant set of test scenarios. Apply three black-box techniques in order, equivalence partitioning (EP), boundary value analysis (BVA), then error/exception paths, and emit a coverage matrix. This produces the *scenario list*; it does not write test code or run anything.

## Inputs

Work from whatever the user provides: a spec, acceptance criteria, a function signature, a UI flow, or a ticket. Before expanding, restate in one line: the **unit under test**, its **inputs** (with types/ranges if known), its **outputs/effects**, and any **stated rules**. Mark anything not given as `unknown`: never invent a range, limit, or error behavior. If a critical bound is unknown (e.g. max length, valid range), list it as an **open question** rather than guessing a number.

## Workflow

1. **Identify the variables.** For each input and each relevant piece of state, name it and its domain (type + valid range/format).
2. **Partition (EP).** Split every variable's domain into equivalence classes, sets where all values are expected to behave identically. Cover **both valid and invalid** partitions. One representative value per class. A value belongs to exactly one class.
3. **Boundaries (BVA).** For every *ordered* partition (numbers, dates, lengths, counts), test the edges. Use **3-value BVA** by default: the boundary, one below, one above (`min-1, min, min+1` and `max-1, max, max+1`). Drop to 2-value (`boundary` + `just past it`) only when the user asks for a lighter pass. BVA applies on top of EP, it does not replace it.
4. **Combine inputs deliberately.** Do not take the full cross-product. Default to **each-choice** (every partition of every variable appears in at least one scenario). Escalate to **pairwise** only when interactions between inputs are likely to matter (call it out when you do). State which strategy you used.
5. **Error & exception paths.** Enumerate the non-happy paths the formal techniques miss (checklist below), these are first-class scenarios, not afterthoughts.
6. **Emit the coverage matrix** (format below), then the open questions.

## Equivalence partitioning checklist

For each variable, derive classes for:
- **Valid** values (often 1+ classes, e.g. "free tier" vs "paid tier" if they behave differently).
- **Invalid** values: out of range, wrong type, malformed format.
- **Empty / absent**: null, missing field, empty string, empty collection.
- **Categorical** inputs: one class per enum/branch, plus one "unrecognized value" class.

## Boundary checklist (the bugs live here)

- Numeric ranges: `min-1, min, min+1, max-1, max, max+1`; also `0`, negatives, and the type's max (overflow).
- Collections/strings: length `0, 1, max, max+1`; also whitespace-only and Unicode/multi-byte if length is character- vs byte-counted.
- Time: start/end of period, leap day, DST transition, timezone edges, "now" exactly on a deadline.
- Pagination/indexing: first page, last page, empty page, off-by-one at page edges.

## Error & exception path checklist

- **Input failures:** validation rejection, injection-shaped input, oversized payload.
- **Dependency failures:** downstream timeout, 4xx/5xx, malformed/partial response, dependency unavailable.
- **State/concurrency:** stale read, double-submit / idempotency, race on shared state, retry after partial success.
- **Auth/permission:** unauthenticated, authenticated-but-unauthorized, expired/revoked token.
- **Resource/environment:** disk/quota full, network drop mid-operation, cancellation/interruption.
- **Lifecycle (UI/mobile):** rotation/recreation, backgrounding, process death + restore, slow network spinner.

## Output: coverage matrix

Emit one table. One row per scenario. Group rows by technique. Keep it deduplicated, if a single scenario exercises a boundary *and* an error path, list it once and tag both.

```
## Test scenarios: <unit under test>
Combination strategy: <each-choice | pairwise | full>, <one-line why>

| # | Technique | Variable / condition | Input(s) | Expected result | Priority |
|---|-----------|----------------------|----------|-----------------|----------|
| 1 | EP-valid  | tier = paid          | ...      | ...             | P1       |
| 2 | BVA       | qty = max+1          | ...      | rejected, error | P1       |
| 3 | Error     | downstream 500       | ...      | retried then surfaced | P2 |

## Open questions
- <unknown bound / undefined behavior the spec must answer before these are testable>
```

Priority: P1 = happy path + high-risk boundaries/errors; P2 = remaining invalid classes; P3 = low-likelihood combinations. Do not pad the matrix, over-enumeration is noise. Collapse redundant rows; if two scenarios test the same class, keep the higher-priority one.

## Validator → fix loop

Before presenting, self-check and fix any miss:
- Every variable has **at least one valid and one invalid** partition (or an explicit note why invalid is impossible).
- Every ordered partition has boundary rows on **both** edges.
- Empty/null/absent is covered for every nullable or collection input.
- At least one dependency-failure and one auth/permission scenario exist (or a note why N/A).
- Each-choice is satisfied: every partition appears in ≥1 row.
- No invented numbers: every concrete bound traces to the spec or sits in Open questions.

## Scope

Analysis only: this skill lists scenarios. It does not write test code, pick a framework, or run anything, hand the matrix to the project's test-writing workflow. For Android, the resulting tests follow `android-testing.md` (favor fast unit tests; test real edge cases, not impossible states).

## References

- ISTQB Certified Tester Foundation Level (CTFL) Syllabus v4.0, §4 Black-Box Test Techniques (equivalence partitioning, boundary value analysis, error guessing), https://www.istqb.org/certifications/certified-tester-foundation-level
- ISTQB Glossary (equivalence partition, boundary value, each-choice/pairwise coverage), https://glossary.istqb.org/
