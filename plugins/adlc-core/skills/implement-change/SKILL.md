---
name: implement-change
description: "This skill should be used when the user asks to \"implement\", \"build\", \"code\", or \"make\" a change, or to \"execute the plan/spec\". Drives implementation through a verification loop and stops to ask the operator for an explicit yes before anything goes remote."
version: 0.1.0
---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# Implement a change

Execute an approved plan with tight verification. All work is local; nothing goes to the internet without the operator's explicit yes.

## Preconditions
- **Context:** if a fresh `~/.openadlc/runs/<workspace>/<run-id>/context.md` from `load-context` exists for this work, read it before exploring; skip re-deriving anything it already covers and explore only what it leaves open.
- **Find the approved plan by run-id, not by glob.** Read the target run's `~/.openadlc/runs/<workspace>/<run-id>/plan/spec.md` and confirm `status:` is `approved`. Get the run-id from the operator, the active `~/.openadlc/runs/<workspace>/*` workspace, or the `run_id:` in spec.md frontmatter, never by globbing a feature-name path or matching a feature name. If the run-id is ambiguous (several active runs), ask which. If none is approved (or none exists), STOP and run `create-plan` first; do not implement against a `draft`. See [references/run-isolation.md](../../references/run-isolation.md).
- `Plans.md` (the slice checklist) lives beside `spec.md` at `~/.openadlc/runs/<workspace>/<run-id>/plan/`. The plan is out of the repo and never committed; the implementer reads it from that stable absolute path regardless of which worktree is checked out, so it does not need to travel in git (per [references/run-isolation.md](../../references/run-isolation.md)).
- **Work on the run branch `adlc/<run-id>` in EACH repo the domain touches** (each branched from that repo's `origin/<default>` at latest per run-isolation), never `main` or a shared branch, so the operator can see exactly what changed. The run-id is workspace-level: the same `adlc/<run-id>` branch name in every touched repo. Only the code change is committed; never commit the run workspace. Never modify a shared checkout out from under the operator. **Concurrency check:** if another run is in progress in this checkout (a live `adlc/*` branch, an active `~/.openadlc/runs/<workspace>/*` with no terminal state, or another worktree), do not share it; auto-create an isolated worktree per run-isolation and have the operator reopen there. A single run with no collision works on `adlc/<run-id>` in place.
- **Set the tracker item in-progress at the start (via the adapter).** Once the sub-issue is resolved and before the first slice, move the item to in-progress through the tracker adapter's `set_status` action ([references/tracker-adapters.md](../../references/tracker-adapters.md)): GitHub maps this to a `status: in progress` label or the Project status field, Jira transitions the sub-task. It is a local-only tracker write (no PR, no push), so the work is visibly claimed before building. Route through the adapter; do not hardcode GitHub-only semantics.

## Execution model: waves, not one-at-a-time

When the plan has a dependency graph (S5 format with `[parallel-safe]` / `[sequential]` tags), the `implementation-lead` agent runs this skill's loop across multiple slices concurrently using the **parallel-barrier** pattern (see [references/orchestration.md](../../references/orchestration.md)):

- Each wave dispatches all `[parallel-safe]` slices concurrently; git worktrees isolate slices that touch overlapping files. Slice worktrees nest as `adlc/<run-id>/<slice-id>` (per run-isolation).
- The barrier collects ALL slice results before the next wave starts.
- Each slice must return verbatim verify output AND pass an adversarial review before `implementation-lead` integrates it into `adlc/<run-id>` (never main).
- `[sequential]` slices and any slice without a dependency graph run one at a time.
- The outbound explicit-yes checkpoint applies to every dispatched agent; fan-out is never a permission escalation.

**Cross-repo merge sequencing (poly-repo product).** When a domain spans several repos, each touched repo gets its own `adlc/<run-id>` branch and its own PR, all linked to the same-domain sub-issue (the tracker + PR hierarchy in [references/run-isolation.md](../../references/run-isolation.md)). `implementation-lead` SEQUENCES the multi-PR merge in the plan's **cross-repo dependency order**: base/shared repos merge before their consumers (e.g. `shared-components` before `web-app`). This is the full orchestration; the fuel-machine coordinator drives it at scale. Outbound merges still need the operator's explicit yes.

When called directly (no lead coordinator), run slices one at a time per the loop below.

## Implementation method: ask SDD or TDD first
Before the first slice, **ask the operator which method to use** for this build; leave the choice to them, it is a mandatory step, not a default:
- **TDD (test-driven):** per slice, write the failable check first, watch it fail, write the smallest code that passes, then refactor.
- **SDD (spec-driven):** per slice, build to the plan's spec and acceptance criteria, then write the tests that pin the behavior. The spec drives; the tests lock it in.

Either way the slice still ends in a **failable check**, the acceptance-criteria check, and the review. The check generalizes by domain; it is not always a unit test:
- **Logic / API / data:** a unit or integration test.
- **UI from a design:** a fidelity + design-system check (the `adlc-design` pack's pixel / token / component comparison against the Figma baseline), since pixels resist classic test-first.
- **Config / IaC:** a plan / dry-run or smoke check that can fail.
- **Spike / throwaway, or docs-only:** say so in the slice; these do not pretend to be TDD or SDD.

A slice with no failable check is not verified, whichever method you pick.

## Loop (repeat per slice in Plans.md)

Copy this checklist:
```
Implement progress (slice <id>):
- [ ] TDD: write the failable check first and watch it fail. SDD: build to the spec, then write the check
- [ ] Make the smallest change that satisfies the slice and turns the check green; match surrounding conventions
- [ ] Refactor with the check green; fix root causes, not symptoms
- [ ] Format + lint
- [ ] Local commit (NO push)
- [ ] Tick the slice in Plans.md and record the verification evidence
```

1. **Lead with the check (TDD) or the spec (SDD).** TDD: write the slice's failable check first and watch it fail. SDD: build to the plan's spec and acceptance criteria, then write the check that pins the behavior. For a test plan on a non-trivial slice, use the `dev-test-planner` skill; for systematic edge enumeration, `test-scenario-expander`. Untested logic doesn't ship either way.
2. **Make it pass minimally, designed well.** Write the smallest code that satisfies the slice and turns the check green; prefer deleting lines over adding; match surrounding conventions. **Apply the core design skills as you write**: `software-design` (clear boundaries, the light domain/data/presentation/ui layering, no over-engineering), `design-principles` (SOLID), and `reusability`; clean up smells with `refactoring`. Stay within the plan's Scope; don't expand it. Refactor once it is green.
3. **Verify** with the slice's pass/fail command (from Plans.md). Address the root cause; never suppress errors. To verify behavior against acceptance criteria, the `validate-scenario` command runs one Gherkin-pinned scenario against the live app.
   - **VERIFY-REAL-RUN GATE (visual / behavioral criteria).** A visual or behavioral acceptance criterion is "met" ONLY after a real run with persisted evidence. A green build is not enough; a SwiftUI / preview / snapshot render is not enough. **Web:** dev-server smoke (the app actually served the screen) plus a saved screenshot under `~/.openadlc/runs/<workspace>/<run-id>/verify/`. **Native:** build **and install AND launch** on a sim/emulator, then a saved screenshot of the launched screen under that same `verify/` path. Cautionary example: the iOS home build passed verify with screenshots, yet the shipped, unsigned binary did not actually launch, build-green and the preview render both lied. If you cannot persist real-run evidence, the criterion is **not met**.
4. **Format/lint** with the project's formatter (resolve it first; do not assume).
5. **Commit locally** in small, focused commits with imperative messages. **Do not push.**
6. **Update the plan.** Tick the slice `[x]` in `Plans.md` and append the one-line verification evidence (command + result). This is what makes a later resume cheap; an un-ticked slice is treated as not-done.

> Language/stack note: the verify and format commands are project-specific. For Android, the `adlc-android` skills (`android-build-commands`, `android-compose-preview`) carry the exact gradlew invocations; resolve the real runner from the repo before running anything.

## HALT gates (stop and ask, do not improvise)
- A slice needs a **new dependency**, a module restructure, or a breaking change: surface it and ask first.
- **Three consecutive failed attempts** on the same slice: stop, report what you tried and the error, ask for direction. Do not thrash.
- A slice needs **a credential or access you don't have**: stop and ask; never fabricate or hardcode one.
- Reality **invalidates the plan** (a slice no longer makes sense): stop and run `iterate-plan` to revise `spec.md` first; do not silently drift from the approved plan.
- **Cannot reach the target UI screen** via the plan's mocks + fast route: stop and ask. Never loop trying to navigate the live app to a deep screen; that burns hours and tokens for nothing.

## When the slice is done
- Run the `review-change` skill (fresh-context adversarial review).
- **Persist the verdict every run.** Write the review verdict to `review-<lens>-<UTC-timestamp>.md` in the run workspace (`~/.openadlc/runs/<workspace>/<run-id>/`, one file per review lens), BLOCK or APPROVE. Posting back stays gated, but the persisted verdict is not optional; never leave the review as only a commit message. A teammate, CI, or a fresh agent must be able to read it from the run workspace.
- Fix blocking findings, re-verify.
- **If you offer a fix-and-re-review loop, state the three loop-control declarations up front first** so the operator knows the iterations before saying yes, per [references/loop-control.md](../../references/loop-control.md): **default cap** (the exit criterion's N), **hard ceiling** (cannot be exceeded; project may lower, never raise), **exit criterion** (a fixed cap, or "until converged" with a hard definition). Default is one pass; each round ends in a one-screen summary of what it found.
- Then, and only then, stop and present the pre-flight report (exactly what would go out) and ask the operator for an explicit yes before any remote action.

## Guardrails
- One slice at a time (direct use); parallel waves only via the `implementation-lead` coordinator.
- If stuck, stop and report the specific blocker; never open a partial/unverified PR.

## References
- Run isolation (run-id selection, run branch `adlc/<run-id>`, slice worktrees, concurrency): [references/run-isolation.md](../../references/run-isolation.md)
- Parallelism doctrine (parallel-barrier, adversarial-verify panel, fan-out, git worktree isolation, consent invariant): [references/orchestration.md](../../references/orchestration.md)
- Tracker adapters (`create_issue`, `link_child`, `set_status`, `assign`; per-tracker GitHub / Jira mappings): [references/tracker-adapters.md](../../references/tracker-adapters.md)
- Loop control (cap, ceiling, exit criterion declared up front): [references/loop-control.md](../../references/loop-control.md)
