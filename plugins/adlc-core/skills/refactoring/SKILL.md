---
name: refactoring
description: "This skill should be used when the user asks to \"refactor this\", \"clean up this code\", \"reduce this code smell\", \"this function is too long/complex\", \"improve readability without changing behavior\", or wants safe restructuring guidance. Covers the common code smells and their refactorings, done in safe small steps under tests. Language-agnostic."
version: 0.1.0
---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# Refactoring

Refactoring is changing structure **without changing behavior**, to lower the cost of the next change. It is not rewriting and not adding features, keep those separate.

## Rules of the road
- **Tests are the safety net.** Refactor only with the relevant behavior covered (or add a characterization test first). Keep the suite green between every step.
- **Small steps, commit often.** Each step is independently reversible and leaves the code working. No "big bang" rewrites disguised as refactors.
- **Behavior is invariant.** If output changes, it's a feature/fix, do it in a separate commit, not mixed into the refactor.
- **Refactor toward the change** (Beck): make the messy area easy to modify, then make the easy modification.

## Smell → refactoring
| Smell | Refactoring |
|---|---|
| Long method / deep nesting | Extract Method; guard clauses / early return; decompose conditional |
| Large class / god object | Extract Class; move responsibilities to where the data is |
| Duplicated knowledge | Extract Method/Function; pull up, **but apply the rule of three** (see `reusability`) |
| Long parameter list | Introduce Parameter Object; preserve whole object |
| Primitive obsession | Introduce a value type (e.g. `Money`, `Email`) over raw `String`/`Int` |
| Feature envy (method uses another object's data more than its own) | Move Method to that object |
| Shotgun surgery (one change touches many files) | Consolidate the responsibility into one module |
| Switch/when on a type, repeated | Replace Conditional with Polymorphism / Strategy, *once variants are real* |
| Comments explaining bad code | Extract + rename so the code says it; delete the comment |
| Dead code / speculative generality | Delete it. Unused flexibility is a liability. |

## Workflow
1. Confirm the area is covered by tests; if not, add a characterization test that pins current behavior.
2. Pick one smell. Apply the smallest refactoring. Run tests. Commit.
3. Repeat. Stop when readability/change-cost is good enough, **don't gold-plate**.
4. Hand off to `review-change` if the diff is non-trivial.

## References
- Martin Fowler, "Refactoring" (2nd ed.): catalog at https://refactoring.com/catalog/
- Refactoring.Guru: code smells + refactorings, https://refactoring.guru/refactoring
