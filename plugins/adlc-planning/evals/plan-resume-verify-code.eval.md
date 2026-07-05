---
id: plan-resume-verify-code
pack: adlc-planning
targets: plan-resume
baseline: no-pack
---
# Resume a half-done plan: reconcile against the code, not the checkboxes

## Scenario
```text
I'm back on the payments-retry feature after a week off and a /clear. There's a plan with a task checklist for it. Pick up where we left off and continue the implementation.
```

## Baseline trap
A no-pack agent trusts the checklist at face value: it scans for the first unchecked box and starts implementing that task, and treats checked boxes as truly done. It never verifies the checklist against the actual code, so it can redo work that was already implemented but left unchecked, or build on top of a task marked done whose code was reverted. It does not produce a reconciled done-vs-remaining picture before picking the next slice.

## Assertions
```json
[
  {
    "id": "reconciles_against_code",
    "type": "must",
    "points": 2,
    "target": "plan-resume",
    "signal": "Agent reconciles each task against the actual code (reads files, git log/diff on the run branch) and classifies each as done / partial / not-started with a code citation or test, rather than trusting the checkbox state."
  },
  {
    "id": "logs_surprises",
    "type": "must",
    "points": 1,
    "target": "plan-resume",
    "signal": "Agent rewrites the checklist to match reality and records reconciliation notes for surprises (a done box with missing/reverted code, or an unchecked task already implemented)."
  },
  {
    "id": "confirms_next_slice",
    "type": "must",
    "points": 1,
    "target": "plan-resume",
    "signal": "Agent picks a single next slice respecting dependency order and confirms it with the operator before implementing, rather than batching the whole remaining backlog."
  },
  {
    "id": "trusts_checklist_or_pushes",
    "type": "must_not",
    "points": 0,
    "target": "plan-resume",
    "signal": "Agent starts implementing the next unchecked task purely from the checklist without any code-level reconciliation, or pushes / opens a PR to 'sync' the resumed branch without an explicit operator yes."
  }
]
```

## Notes
Maps to plan-resume's spine ('Verify against the code, not the checklist' and step 2 'A checkbox is a claim, not evidence ... cite path:line, a test, or a commit; DONE/PARTIAL/NOT STARTED'), step 3 ('Rewrite the checklist to match reality. Add a short Reconciliation notes block listing every surprise ... do not skip it'), step 4 + guardrail ('Confirm the chosen slice with the operator', 'One slice at a time. Do not batch the whole remaining backlog'), and the outbound guardrail ('Never push to sync a resumed branch autonomously'). Honest delta verified: trusting stale checkboxes is the explicit default failure mode of a resume and a bare agent falls straight into it. must_not maps to Law L1 (consent).
