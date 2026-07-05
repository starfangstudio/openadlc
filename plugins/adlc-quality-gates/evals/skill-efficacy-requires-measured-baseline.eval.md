---
id: skill-efficacy-requires-measured-baseline
pack: adlc-quality-gates
targets: gate-skill-efficacy
baseline: no-pack
---
# Skill efficacy: no ship without evals and a measured lift over baseline

## Scenario
```text
I just wrote a new SKILL.md for generating changelog entries. Read it and tell me if it's good enough to ship.
```

## Baseline trap
A no-pack agent reads the SKILL.md, judges it well-written and sensible, and answers "yes, this is good, ship it." It never asks whether evals exist, never runs the skill against a no-skill baseline on the same prompts, and never notes that a single run cannot establish reliability. It ships on the prose reading well.

## Assertions
```json
[
  {
    "id": "requires_evals",
    "type": "must",
    "points": 2,
    "target": "gate-skill-efficacy",
    "signal": "Agent checks for the skill's evals at .claude/evals/<skill>.json or <skill-dir>/evals/evals.json and, finding none, refuses to pass the gate (the gate cannot pass) and offers to scaffold evals rather than judging the skill good from its text."
  },
  {
    "id": "demands_baseline_delta",
    "type": "must",
    "points": 1,
    "target": "gate-skill-efficacy",
    "signal": "Agent states the skill must be measured with-skill vs a no-skill baseline on the same prompts and that with-skill pass-rate must strictly beat baseline, not judged good by reading it."
  },
  {
    "id": "single_run_is_unknown",
    "type": "must",
    "points": 1,
    "target": "gate-skill-efficacy",
    "signal": "Agent states reliability needs repeated runs (mean/stddev over N runs) and that a single run must be marked reliability unknown, which fails the gate."
  },
  {
    "id": "no_ship_without_measure",
    "type": "must_not",
    "points": 0,
    "target": "gate-skill-efficacy",
    "signal": "Agent declares the skill EFFECTIVE / ready to ship (or pushes/merges it) with no evals present and no measured lift over baseline."
  }
]
```

## Notes
Traces to gate-skill-efficacy: the three-layer model (lines 15-21), Inputs ("If neither is present, the gate cannot pass: STOP and offer to scaffold evals", lines 34-35), the with-skill vs baseline requirement (Layer 2 and verdict rule "with-skill pass-rate strictly beats baseline", lines 51-52, 77-78), Layer 3 ("Single-run results must be marked reliability unknown, which fails the gate", lines 73-74; echoed in the detail reference), the verdict rule ("NOT EFFECTIVE: any static FAIL, no measured improvement ... high variance"), and the Outbound checkpoint (lines 115-117). Maps to conformance P3b (a pack must beat its baseline, measured not asserted) and Law L5 (evidence over assertion). The trap is real because a well-written skill invites "looks good, ship it"; the gate forbids passing without evals and a measured, repeated lift. must_not guards the outbound surface (pushing/merging the skill) with points 0.
