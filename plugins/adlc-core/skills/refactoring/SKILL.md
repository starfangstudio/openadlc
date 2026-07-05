---
name: refactoring
description: "This skill should be used when the user asks to \"refactor this\", \"clean up this code\", \"reduce this code smell\", \"this function is too long/complex\", \"split this file\", \"rename this everywhere\", \"improve readability without changing behavior\", \"restructure this module\", or wants safe restructuring guidance. Covers the behavior-preserving transformation discipline: the test-green-between-steps loop, IDE/codemod tooling for safe renames and extracts, module and repo-boundary moves, and when NOT to refactor. Language-agnostic (examples in TypeScript/Kotlin)."
version: 0.2.0
---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# Refactoring

Refactoring is changing structure **without changing behavior**, to lower the cost of the next change. It is not a rewrite and not a feature, keep those in separate commits. This skill is the *transformation discipline*: how to move code safely once you have decided to. The *extract-or-not* judgment (should this become shared at all) lives in the `reusability` skill, cross-reference it before extracting duplication.

## The discipline (non-negotiable)
- **Tests are the safety net, kept green between every step.** Refactor only over covered behavior. If the area is not covered, add a characterization test that pins current behavior *first* (see below). A refactor with no green test between steps is a rewrite with extra confidence, not a refactor.
- **One transformation per step, commit each.** Each step is independently reversible and leaves the suite green. No "big bang" restructure disguised as a refactor.
- **Behavior is invariant.** If any observable output, signature contract, or side effect changes, it is a feature or a fix: separate commit, separate review. Do not smuggle it into the refactor diff.
- **Refactor toward the change** (Beck): make the messy area easy to modify, *then* make the easy modification.
- **Prefer the tool over the hand-edit.** An IDE rename or a codemod is safer than a manual find-replace. See Automated tooling below.

## The loop (run per transformation)
```
Refactor step (<what>):
- [ ] Suite green BEFORE the step (baseline). If not covered, add a characterization test first
- [ ] Apply ONE refactoring (prefer an IDE/codemod command over hand-editing)
- [ ] Re-run the SAME verify command. Green? keep. Red? revert this step, do not "fix forward"
- [ ] Format + lint
- [ ] Local commit, imperative message ("Extract validateEmail from parseUser")
```
Verify command is project-specific, resolve the real runner from the repo, do not assume. Scope it tight so the loop is fast:
- **JS/TS:** `npx vitest run path/to/file.test.ts` (or `jest --findRelatedTests <file>`)
- **Kotlin/JVM:** `./gradlew :module:test --tests "com.pkg.ClassTest"`
- **Python:** `pytest path/to/test_file.py -q`
- **Go:** `go test ./pkg/...`

Red after a step means the step, not the code, is wrong: `git checkout -- .` this step and retry smaller. Never disable a failing test to make a refactor "pass".

## Characterization test (when coverage is missing)
Do not refactor uncovered logic blind. Pin what it does *now* (bugs included), then refactor under it.
```ts
// Snapshot current behavior across representative inputs before touching the code.
test.each([
  ["", 0], ["a", 1], ["a,b,c", 3], [" a , b ", 2],
])("countItems(%j) === %i (current behavior)", (input, expected) => {
  expect(countItems(input)).toBe(expected);
});
```
If a case surprises you, that is a latent bug: note it, but keep the refactor behavior-preserving. Fix the bug in a *later* commit.

## Smell -> refactoring
| Smell | Refactoring |
|---|---|
| Long method / deep nesting | Extract Method; guard clauses / early return; decompose conditional |
| Large class / god object | Extract Class; move responsibilities to where the data is |
| Duplicated knowledge | Extract Function; pull up. Apply the rule of three and the wrong-abstraction test **via `reusability` first** |
| Long parameter list | Introduce Parameter Object; preserve whole object |
| Primitive obsession | Introduce a value type (`Money`, `Email`) over raw `String`/`Int` |
| Feature envy (uses another object's data more than its own) | Move Method to that object |
| Shotgun surgery (one change touches many files) | Consolidate the responsibility into one module |
| Repeated switch/when on a type | Replace Conditional with Polymorphism / Strategy, *once the variants are real* |
| Comment explaining bad code | Extract + rename so the code says it; delete the comment |
| Dead code / speculative generality | Delete it. Unused flexibility is a liability |

## Worked example (Extract Method + guard clause)
Before, a long method mixing validation, branching, and work:
```ts
function grantAccess(user: User, resource: Resource): Result {
  if (user.isActive) {
    if (user.roles.includes("admin") || resource.owner === user.id) {
      audit.log(user.id, resource.id);
      return { ok: true, token: mintToken(user, resource) };
    } else {
      return { ok: false, reason: "forbidden" };
    }
  } else {
    return { ok: false, reason: "inactive" };
  }
}
```
After, guard clauses flatten nesting and one intention-revealing extract names the rule. Same inputs, same outputs:
```ts
function grantAccess(user: User, resource: Resource): Result {
  if (!user.isActive) return { ok: false, reason: "inactive" };
  if (!canAccess(user, resource)) return { ok: false, reason: "forbidden" };
  audit.log(user.id, resource.id);
  return { ok: true, token: mintToken(user, resource) };
}

function canAccess(user: User, resource: Resource): boolean {
  return user.roles.includes("admin") || resource.owner === user.id;
}
```
Each edit (invert the `isActive` guard, then extract `canAccess`) is its own step with the suite green in between.

## Automated tooling (the safe default)
Manual restructuring of anything beyond one file is where refactors silently break. Reach for a tool first:
- **IDE structural refactors** (semantic, cross-file, undoable): VS Code / TypeScript LSP `Rename Symbol` (F2), `Extract to function/constant/method`; IntelliJ / Android Studio `Refactor > Rename` (Shift-F6), `Extract Method` (Cmd-Alt-M), `Move`, `Change Signature`; Xcode `Editor > Refactor > Rename`. These update every reference and import, a project-wide grep-replace does not.
- **Codemods for a repeat pattern across many files** (define the transform once, apply everywhere): TypeScript/JS `jscodeshift` or `ts-morph`; Python `libcst` codemods; polyglot `comby` or `ast-grep` (`sg`) for structural search-replace; framework `npx @<framework>/upgrade` codemods for API migrations.
- **Rule:** run the codemod, then run the verify loop over the *whole* touched set, and read the diff before committing. A tool that touches 200 files still needs a green suite and a human-read diff.

## When NOT to refactor (stop and skip)
- **No test coverage and no time to add a characterization test.** Refactoring blind is how behavior drifts silently. Add coverage first or leave it.
- **Mid-feature or on a hot path to a deadline.** Land the behavior change, refactor in a follow-up. Do not mix the two diffs.
- **Code slated for deletion or rewrite.** Do not polish a module that is about to be replaced.
- **"Refactor" that changes behavior.** That is a feature/fix, route it through `implement-change`, not here.
- **Churn with no payoff** (renaming to personal taste, restyling stable code no one is about to touch). Refactor toward a real, imminent change, not for its own sake. Don't gold-plate.

## Boundary and repo-scale moves
Moving a symbol *across* a module or package boundary is still a refactor, but the blast radius is larger:
- Use the IDE `Move` refactor so imports update automatically; a hand-move leaves dangling imports.
- Keep the public surface stable during the move: if a symbol is exported, leave a re-export shim at the old path in the same commit, delete it in a follow-up once callers migrate. Splits the ripple into reviewable steps.
- In a poly-repo product a cross-repo move is a coordinated change, not one refactor: it needs a plan (base repo exports before consumers import). Stop and route it through `create-plan` / `implement-change`, do not free-hand it.

## Handoff
- Extraction is about to create shared/reused code: consult `reusability` for the extract-or-not call and API shape before you extract.
- Non-trivial refactor diff: hand to `review-change` (fresh-context adversarial review) before the outbound checkpoint.
- Refactoring is a *step inside* implementation: `implement-change` calls this skill after a slice goes green.

## References
- Martin Fowler, *Refactoring* (2nd ed.), catalog: https://refactoring.com/catalog/
- Refactoring.Guru, code smells + refactorings: https://refactoring.guru/refactoring
- Extract-or-not judgment and the wrong-abstraction test: `reusability` skill.
