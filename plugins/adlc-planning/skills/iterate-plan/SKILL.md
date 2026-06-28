---
name: iterate-plan
description: "This skill should be used when the user asks to \"revise the plan\", \"update the plan\", \"the scope changed\", \"requirements changed\", \"re-plan\", \"adjust spec.md\", \"the plan is out of date\", or otherwise needs an already-approved plan and its spec.md reconciled after new facts, scope changes, or discoveries land mid-implementation. Keeps spec.md the single authoritative source of truth."
version: 0.1.0
---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# Iterate Plan

**Law: change `spec.md` first, then re-derive `Plans.md`. Never change plan behavior without updating the spec.**

Revise an approved plan when scope or facts change without silently drifting. Every behavior change either cites the spec or updates it.

## When to use

- A new fact, constraint, or discovery invalidates part of the approved plan.
- Scope grew or shrank mid-implementation.
- Implementation drifted from what `spec.md` says (code and spec disagree).
- The user explicitly asks to revise/re-plan/update the spec.

Do NOT use for the first plan of a feature, use the create-plan skill for that.

## Inputs to locate first

Read these before changing anything. Select the run by its `run_id` (from `spec.md` frontmatter), never by globbing or feature-name match. If the run-id is unknown, ask; never invent it. The plan lives in the out-of-repo run workspace at the stable absolute path `~/.openadlc/runs/<workspace>/<run-id>/` (workspace-level run-id; `<workspace>` = the product name for a poly-repo product, else the single repo's name); run layout, run-id rules, and `<workspace>` resolution: the `references/run-isolation.md` reference in the **adlc-core** pack.

- `~/.openadlc/runs/<workspace>/<run-id>/plan/spec.md`: the authoritative spec (current target state, not history).
- `~/.openadlc/runs/<workspace>/<run-id>/plan/Plans.md`: the slice checklist beside it.
- Any code already written against the plan (on branch `adlc/<run-id>`).

(create-plan and plan-resume use exactly `spec.md` + `Plans.md` under `~/.openadlc/runs/<workspace>/<run-id>/plan/`. This skill uses the same names; there is no separate `plan.md`/`tasks.md`.)

## Procedure

1. **State the delta in one line.** "Was X, now Y, because Z." Get the user to confirm this is the change before editing. If the trigger is drift (code vs spec disagree), name which one is wrong.

2. **Decide spec vs plan.** Classify the change:
   - **Behavior / requirement / acceptance-criteria change** → edit `spec.md` first, then re-derive the Plans.md slices.
   - **Pure implementation/tactics change** (same observable behavior) → edit the plan only; cite the spec section it still satisfies.
   Never change the plan's behavior without updating `spec.md`: that is drift.

3. **Edit `spec.md` to the new target state.** Rewrite the affected sections to describe what the system does *now/should do*, not a changelog. Keep it consolidated and clean. Record the rationale in a short `## Clarifications` or `## Decisions` note (date + the "because Z"), not inline history scattered through the doc.

4. **Re-derive the Plans.md slices from the edited spec.** Edit `~/.openadlc/runs/<workspace>/<run-id>/plan/Plans.md` in place (out of the repo, never committed). For each spec change, update the dependent slices. Explicitly mark:
   - **Added**: new work the change introduces.
   - **Changed**: steps whose approach shifts.
   - **Obsolete**: slices the change kills (delete them; prefer removing lines over leaving dead ones).
   - **Done-but-now-wrong**: already-written code the change invalidates (flag for rework).
   If the change shifts which **repos** a domain touches or the **cross-repo dependency order** (e.g. a domain now also touches `shared-components`, which must merge before `web-app`), update the spec's per-domain repo list and merge order and re-derive the affected slices to match. Plans stay one per domain; sub-issue and PR hierarchy follow the `references/run-isolation.md` reference in the **adlc-core** pack.

5. **Consistency pass (validator → fix loop).** Re-read `spec.md` and `Plans.md` together and check:
   - Every slice traces to a spec requirement; no orphan slices.
   - Every spec requirement has a covering slice; no uncovered requirements.
   - No slice contradicts another or the spec.
   If any check fails, fix and re-run this step until all pass.

6. **Present the revision report (see format) and STOP.** This is a non-trivial change to approved work, get explicit "yes" before continuing implementation.

## Revision report format

```
## Plan revision

Delta: <was X, now Y, because Z>
Classification: spec change | plan-only change

### spec.md edits
- <section>: <what changed>

### Plans.md slice changes
- Added:    <slices>
- Changed:  <slices>
- Obsolete: <slices removed>
- Rework:   <already-written code now invalidated>

### Open questions
- <unknowns, or "none">
```

## CRITICAL gates

- The spec is authoritative. If a behavior change does not appear in `spec.md`, it does not exist, update the spec.
- STOP after the revision report and wait for explicit approval before resuming implementation.
- This skill edits local files only. It NEVER pushes, opens/updates a PR, or posts anywhere. Any outbound action needs the operator's explicit yes first.
- Mark anything unverified as `unknown`. Do not invent requirements or rationale.

## References

- Run isolation (run-id, out-of-repo run workspace `~/.openadlc/runs/<workspace>/<run-id>/`, plan selection by run-id): the `references/run-isolation.md` reference in the **adlc-core** pack.
- GitHub Spec Kit: specs as living artifacts; Spec → Plan → Tasks → Implement, with `/speckit.clarify` and `/speckit.analyze` validation gates: https://github.com/github/spec-kit
