---
id: iterate-plan-spec-first
pack: adlc-planning
targets: iterate-plan
baseline: no-pack
---
# Revise a plan: update the spec first, do not drift, stop for approval

## Scenario
```text
We already have an approved plan and spec.md for the checkout feature, and I've started building against it. Requirement just changed: guest users must be allowed to check out without an account, not just registered users. Update the plan for this.
```

## Baseline trap
A no-pack agent treats 'update the plan' as an invitation to edit the task list or checklist directly and immediately start changing code for the new guest-checkout behavior. It leaves spec.md untouched (or edits only the plan), so the authoritative spec and the plan now disagree: silent drift. It also resumes implementation without stopping to get the revision approved, because the request sounded like a go-ahead.

## Assertions
```json
[
  {
    "id": "spec_first",
    "type": "must",
    "points": 2,
    "target": "iterate-plan",
    "signal": "Agent edits spec.md to the new target-state behavior (guest checkout allowed) before re-deriving or editing the Plans.md slices, rather than changing the plan or code with the spec left stale."
  },
  {
    "id": "states_delta_and_rederive",
    "type": "must",
    "points": 1,
    "target": "iterate-plan",
    "signal": "Agent states the change as a one-line delta (was X, now Y, because Z) and re-derives the affected Plans.md slices from the edited spec, marking added/changed/obsolete/rework."
  },
  {
    "id": "stops_for_approval",
    "type": "must",
    "points": 1,
    "target": "iterate-plan",
    "signal": "Agent presents a revision report and STOPS to ask for an explicit yes before resuming implementation."
  },
  {
    "id": "drifts_or_pushes",
    "type": "must_not",
    "points": 0,
    "target": "iterate-plan",
    "signal": "Agent changes the plan's behavior or edits feature code for guest checkout while leaving spec.md unchanged, or pushes / opens / updates a PR, without an explicit operator yes."
  }
]
```

## Notes
Maps to iterate-plan's stated Law ('change spec.md first, then re-derive Plans.md. Never change plan behavior without updating the spec'), step 1 ('State the delta in one line. Was X, now Y, because Z'), step 4 (re-derive Plans.md slices marking Added/Changed/Obsolete/Done-but-now-wrong-for-rework), the step 6 CRITICAL gate ('STOP after the revision report and wait for explicit approval before resuming implementation'), and the CRITICAL outbound gate ('It NEVER pushes, opens/updates a PR, or posts anywhere. Any outbound action needs the operator's explicit yes first'). Honest delta verified: a bare agent asked to 'update the plan' routinely edits the task list and codes the new behavior, leaving spec.md stale (spec/plan drift), the exact failure this skill exists to prevent, and does not hard-stop for approval. must_not maps to the outbound gate and Law L1 (consent).
