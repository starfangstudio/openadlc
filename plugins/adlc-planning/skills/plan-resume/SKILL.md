---
name: plan-resume
description: "This skill should be used when the user asks to \"resume the plan\", \"pick up where we left off\", \"continue the implementation\", \"what's left to do\", \"reconcile the plan with the code\", or comes back to a partially-done feature after a break or a /clear. Reconciles the spec/Plans against the actual codebase to produce a trustworthy done-vs-remaining picture, then hands the next slice to implementation."
version: 0.1.0
---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# Resume a plan

Re-establish ground truth on a half-finished plan, then continue. The danger is trusting stale checkboxes: a task marked done may have been reverted, and an unchecked task may already be implemented. **Verify against the code, not the checklist.**

## Workflow

Copy this checklist and track progress:
```
Resume progress:
- [ ] Located the run by run-id (plan/spec.md, plan/Plans.md) and its branch adlc/<run-id>
- [ ] Reconciled each task: code-verified done / partial / not-started
- [ ] Rewrote the checklist to match reality; logged surprises
- [ ] Confirmed the next slice with the operator
- [ ] Handed off to implement-change (one slice)
```

- **Precondition:** if a fresh `~/.openadlc/runs/<workspace>/<run-id>/context.md` from `load-context` exists for this work, read it before reconciling; skip re-deriving anything it already covers and explore only what it leaves open.

1. **Locate the run by run-id.** Select the run by its `run_id` (`spec.md` frontmatter), never by globbing the run workspace or feature-name match. Read the plan (`~/.openadlc/runs/<workspace>/<run-id>/plan/spec.md`) and task breakdown (`~/.openadlc/runs/<workspace>/<run-id>/plan/Plans.md`) from the stable out-of-repo path; the code lives on branch `adlc/<run-id>` in EACH repo the run touches. If no run exists, this is not a resume, stop and route to `create-plan`. Never reconstruct a plan from memory. The run-id is workspace-level; `<workspace>` resolution, out-of-repo workspace, run-id, branch, and the four workspace shapes (single / monorepo / poly-repo product / undeclared parent): the `references/run-isolation.md` reference in the **adlc-core** pack.

2. **Reconcile each task against the code (every repo the run touches).** A checkbox is a *claim*, not evidence. For every task, classify it from what the repo actually shows, cite `path:line`, a test, or a commit:
   - **DONE**: code exists AND its validation check passes. Verify, don't assume.
   - **PARTIAL**: started but incomplete (stub, failing/missing test, TODO, half-applied diff). Note exactly what remains.
   - **NOT STARTED**: no trace in the code.
   Use `git log`/`git diff origin/<default>...HEAD` (the run branch `adlc/<run-id>` against that repo's default) and the working tree to see what actually landed. For a poly-repo run, reconcile the `adlc/<run-id>` branch in EACH member repo the plan names, and check the recorded cross-repo merge order still holds (base/shared repos before their consumers). Flag tasks marked done whose code is absent or reverted, and unchecked tasks that are already implemented.

3. **Rewrite the checklist to match reality.** Update `~/.openadlc/runs/<workspace>/<run-id>/plan/Plans.md` (out of the repo, never committed) so status reflects the code (see Status conventions). Add a short **Reconciliation notes** block listing every surprise (claimed-done-but-missing, done-but-unchecked, scope drift, conflicts with `main`). This block is the value of the resume, do not skip it.

4. **Pick the next slice.** Choose the lowest-risk unblocked task respecting dependency order; never pick a task whose prerequisites are PARTIAL/NOT STARTED. Re-derive whether the original plan still holds, if the code diverged enough that remaining steps are wrong, stop and route back to `create-plan` to re-plan the tail. Confirm the chosen slice with the operator.

5. **Hand off.** Pass the single confirmed slice to `implement-change`. This skill reconciles and routes; it does not write feature code itself.

## Status conventions

Markdown checkboxes, spec-kit style, keep them greppable:
```
- [x] T1  Done + verified (cite path:line / passing test)
- [~] T2  PARTIAL, <what remains>
- [ ] T3  Not started
- [ ] T4  [P] Parallel-safe (no dependency on a sibling task)
- [ ] T5  [BLOCKED: needs T2]  Depends on an unfinished task
```
`[P]` marks tasks with no ordering dependency (safe to do in any order); `[BLOCKED: …]` names the prerequisite. Mark `[x]` only after the task's validation check passes, a written-but-unverified task stays `[~]`.

## Guardrails
- Verify before trusting: a stale checklist is the default failure mode of a resume. One code citation per DONE claim.
- One slice at a time. Do not batch the whole remaining backlog into a single change.
- 🚦 **Outbound needs the operator's explicit yes.** Reconciling and editing `Plans.md` are local; do them freely. Anything outbound (push, PR open/update, comments, deploys): finish locally, present a clear report of exactly what would go out, and wait for the operator's explicit per-action "yes". Never push to "sync" a resumed branch autonomously.
- If artifacts are missing or contradictory and can't be reconciled from the code, stop and report the specific gap, don't invent the missing history.

## References
- Run isolation (run-id, out-of-repo run workspace `~/.openadlc/runs/<workspace>/<run-id>/`, run branch `adlc/<run-id>`): the `references/run-isolation.md` reference in the **adlc-core** pack.
- GitHub spec-kit: Spec-Driven Development: spec → plan → `tasks.md`, `[P]` parallel markers, checkpoint validation between phases. https://github.com/github/spec-kit (see `spec-driven.md`).
- Peer skills: `create-plan` (produces `spec.md` / `Plans.md`), `implement-change` (executes one slice), `review-change` (reviews it). Reconcile against the loop in `CLAUDE.md`.
