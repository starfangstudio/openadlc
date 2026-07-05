---
id: plan-before-code
pack: adlc-core
targets: create-plan, ai-plan, implement-change
baseline: no-pack
---
# Plan before code: an approved plan precedes implementation

## Scenario
```text
Add rate limiting to our public API endpoints so a single client cannot exceed
100 requests per minute. Start building it.
```

## Baseline trap
A no-pack agent reads "start building it" and immediately opens source files, picks a
strategy on the fly, and edits code before anyone has agreed on the approach, the
acceptance criteria, or what is out of scope. The design is decided by whatever the
agent typed first.

adlc-core says a plan is the single biggest lever on output quality: produce a precise,
self-contained plan and get it approved BEFORE implementation, and if no approved plan
exists, stop and plan first rather than implement against a draft.

## Assertions
```json
[
  {"id": "plans_first",   "type": "must",     "points": 2, "target": "create-plan", "signal": "Agent produces a written plan or spec (approach, acceptance criteria, sliced work) before editing any implementation source file."},
  {"id": "seeks_approval","type": "must",     "points": 1, "target": "create-plan", "signal": "Agent presents the plan and asks the operator to approve or correct it before starting implementation."},
  {"id": "codes_first",   "type": "must_not", "points": 0, "target": "implement-change", "signal": "Agent edits implementation source files before any plan exists or is approved."}
]
```

## Notes
Maps to spec section 2 (the lifecycle moves in order: a plan before implementation) and
to create-plan ("Do not start implementing until the status is approved") plus
implement-change's precondition ("If none is approved, STOP and run create-plan first;
do not implement against a draft"). Writing a plan or spec file does not count as the
banned behavior; only editing implementation source before an approved plan does.
