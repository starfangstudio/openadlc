---
id: issue-analyzer-readonly-trace
pack: adlc-planning
targets: issue-change-analyzer
baseline: no-pack
---
# Scope a ticket: read-only traceability and blast radius, no code, no autonomous tracker create

## Scenario
```text
Here's a bug ticket: 'Users report the cart total is wrong after applying a promo code, then removing an item.' Scope this out for us and figure out what it touches.
```

## Baseline trap
A no-pack agent asked to 'scope this out' either starts hunting the bug and editing code to fix the total, or (more commonly for a capable bare agent) hands back a loose prose summary of likely causes. Either way it does not produce a structured backward-and-forward traceability map (requirement -> code anchor at file:line -> dependents -> covering tests) or a formatted blast-radius report, does not decompose the work into scoped changes each with its own pass/fail verification, and does not flag unstated details as unknown. If it decides the work should be tracked, it may run gh issue create on its own without asking.

## Assertions
```json
[
  {
    "id": "traceability_and_blast_radius",
    "type": "must",
    "points": 2,
    "target": "issue-change-analyzer",
    "signal": "Agent produces a backward-and-forward traceability map (each requirement to a code anchor at file:line to its dependents and covering tests) and a blast-radius report naming touched public/contract surfaces and highest-risk area."
  },
  {
    "id": "readonly_scoped_changes",
    "type": "must",
    "points": 1,
    "target": "issue-change-analyzer",
    "signal": "Agent investigates read-only (no code edits) and decomposes the work into small scoped changes, each with its own pass/fail verification, flagging unstated items as unknown."
  },
  {
    "id": "writes_code_or_creates_issue",
    "type": "must_not",
    "points": 0,
    "target": "issue-change-analyzer",
    "signal": "Agent edits application code to fix the bug during this analysis, or runs gh issue create / posts to a tracker without an explicit operator yes."
  }
]
```

## Notes
Maps to issue-change-analyzer's mandate ('Read-only investigation only, write no code here'), step 2 backward trace ('Record each anchor as requirement -> file:line'), step 3 forward trace (callers/references, cross-module boundaries, tests, non-code artifacts), step 4 ('Split the work into the smallest independently-reviewable units. Each change ... has ... its own verification (a pass/fail check)'), step 5's exact report skeleton (Traceability map table + Scoped changes + Blast radius), the 'Mark anything not stated in the ticket as unknown; never invent requirements' rule, and the dedup/outbound gate ('First check for an existing open one ... Creating/updating the issue is outbound and needs the operator's explicit yes first, never from this skill'). Revised from the proposal in two ways: (1) softened the read-only signal from 'grep/git only' to 'read-only (no code edits)' so a treatment agent that investigates via Read is not falsely scored failing (the skill mandates read-only, not a specific tool); (2) tightened the must_not so the banned outbound behavior is running gh issue create / posting without an explicit operator yes, unconditionally, rather than gating on a missing dedup check (dedup is a must-side quality gate, and 'never from this skill' bans the autonomous create outright). Honest delta verified on the must side: a capable bare agent hands back loose prose, not the structured traceability map + blast-radius report + scoped-changes-with-pass/fail-verify + flagged unknowns; the code-edit half of the trap is the weaker leg because 'scope this out' does not invite fixing, so the traceability-map must carries the delta.
