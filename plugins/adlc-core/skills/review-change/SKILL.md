---
name: review-change
description: "This skill should be used when the user asks to \"review\" a change, diff, or PR, or before merging/shipping. Orchestrates an independent, fresh-context review of the current diff against the plan and returns a prioritized gap report."
version: 0.1.0
---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# Review a change

Run an independent review in a **fresh context** so the reviewer isn't biased by the reasoning that produced the change. The implementer should not grade its own work.

Review runs in **two places, both real**: **embedded** inside implement-change (the per-slice review that is never skipped) and **standalone** (this skill, the dedicated diff-vs-plan pass before the outbound consent checkpoint). The embedded pass catches drift slice by slice; the standalone pass judges the whole change as one contract. Neither replaces the other.

## When to use which review surface
- **review-change** (this skill): a local, uncommitted-or-committed diff against its plan, before the outbound consent checkpoint. The default for ADLC implementation work.
- **`/adlc-pr-review`**: an existing PR (confidence-scored; publishing comments needs the operator's explicit yes). In a poly-repo product the run has one PR per touched repo, so this runs **per repo**, each review run-id-tagged and dedup'd (`pr-review-publisher`, per [references/run-isolation.md](references/run-isolation.md)).
- **built-in `/code-review`**: a quick correctness-only pass with no plan anchoring.
Use this skill for "review my change"; reach for the others only when the user names a PR or asks for code-quality-only.

## Workflow

1. **Establish the baseline, per repo.** Get the *full* diff of the run branch, not just uncommitted work: `git diff origin/<default>...HEAD` (the run is on `adlc/<run-id>`, branched from the repo default per [references/run-isolation.md](references/run-isolation.md)) since implement-change commits each slice locally, so a bare `git diff` is empty. When the domain spans several repos (poly-repo product), take the diff in **each touched repo** on its `adlc/<run-id>` branch and review them per repo. Identify the plan it should satisfy by run-id: `~/.openadlc/runs/<workspace>/<run-id>/plan/spec.md` + `Plans.md` (the out-of-repo workspace; select by the run-id, not a feature-name glob).
2. **Delegate to a fresh reviewer.** For Android changes, delegate to the `android-reviewer` subagent. For a general correctness pass, run the built-in `/code-review`. Give the reviewer only the diff + the plan + what counts as a finding (never the reasoning that produced the change).
3. **Fan out by dimension, then pipeline adversarial verification.** Spawn five concurrent reviewers, each scoped to one dimension and given only the diff + the plan. The lenses run **concurrently**, not in sequence:
   - **Correctness**: logic bugs, missing edge cases, broken contracts.
   - **Security**: auth, input parsing, I/O, secrets, permissions.
   - **Performance**: hot paths, allocations, blocking calls, unnecessary work.
   - **UI fidelity (compliance)**: when the change touches UI, does the result match the design intent and any layout intent the plan carried (spacing, states, copy, components, responsive behavior)? Treat fidelity as a **compliance** concern, not taste: a stated UI requirement that ships wrong is a blocking gap, the same as a broken contract.
   - **Design & style**: `software-design` boundaries (the domain/data/presentation/ui layering, no leaks), SOLID (`design-principles`), code smells (`refactoring`), duplication vs `reusability`, plus conventions, naming, and dead code.
   As each dimension returns, immediately spawn a skeptic for each of its findings (do not wait for the other dimensions). The skeptic asks: Is it actually reachable? Does the existing code already handle it? Is the cited line correct? Drop findings where the skeptic succeeds; only surviving findings proceed to the report. The next dimension's findings are verified the same way, in parallel, as they arrive. See [references/orchestration.md](references/orchestration.md) (fan-out, pipeline, adversarial-verify panel).
4. **Check against the plan, not taste.** Verify every requirement is implemented, the listed Validation/edge cases have tests, and nothing outside Scope changed.
5. **Collect findings** in three tiers:
   - **Blocking**: breaks correctness or a stated requirement. Must be fixed before the outbound consent checkpoint.
   - **Suggestions**: real improvements, not dealbreakers.
   - **Positive**: what's genuinely right (specific, not generic praise).
6. **Write the report to disk.** Save the gap report to this run's `~/.openadlc/runs/<workspace>/<run-id>/review-<lens>-<UTC-timestamp>.md` (the out-of-repo workspace per run-isolation; never committed, never a bare `review.json` / `review-<date>.md`), with `path:line` references and a one-line verdict (ready / needs work), so the pre-outbound consent report can cite it and a later session can audit what was reviewed. Also return it in-conversation.

## Discipline
- A reviewer asked to find gaps will always find some. **Flag only gaps that affect correctness or the stated requirements**: do not chase style or invent defensive code/tests for impossible cases. Over-engineering is a failure mode.
- Reviewing evidence (test output, build result, screenshots) beats re-running everything by hand, ask the implementer to attach it.
- Blocking findings loop back to `implement-change`; re-review after fixes. Only a clean (or accepted-suggestions-only) review proceeds to the outbound consent checkpoint.

## References
- [references/run-isolation.md](references/run-isolation.md): run-id plan selection, run branch, per-run review path, PR-review dedup.
- [references/orchestration.md](references/orchestration.md): fan-out, parallel-barrier, adversarial-verify panel.
