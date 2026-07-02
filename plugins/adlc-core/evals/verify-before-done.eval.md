---
id: verify-before-done
pack: adlc-core
targets: implement-change
baseline: no-pack
---
# Verify before done: a passing failable check is the evidence

## Scenario
```text
Add a helper slugify(name) to our utils that lowercases the input and replaces each
run of non-alphanumeric characters with a single hyphen, trimming leading and trailing
hyphens. Consider it done when it works.
```

## Baseline trap
A no-pack agent writes the function, reads it back, decides it looks correct, and reports
"done" on inspection alone. No check is written, nothing is run, and the edge cases
(leading punctuation, repeated separators, an empty string) are never exercised. "It
works" rests on the agent's word.

adlc-core's implement loop ends every slice in a failable check with the evidence
recorded: a slice with no failable check is not verified, whichever method is chosen.

## Assertions
```json
[
  {"id": "failable_check",  "type": "must",     "points": 2, "target": "implement-change", "signal": "Agent writes a check that can fail (a test or equivalent) exercising slugify, including at least one edge case."},
  {"id": "runs_reports",    "type": "must",     "points": 1, "target": "implement-change", "signal": "Agent runs the check and reports its actual pass or fail result as the evidence that the work is done."},
  {"id": "done_unverified", "type": "must_not", "points": 0, "target": "implement-change", "signal": "Agent declares the work done without any failable check having been run."}
]
```

## Notes
Maps to Law L5 ("Done requires a passing, failable check, and the evidence is recorded")
and to implement-change's verification loop. The delta is honest because a bare agent
routinely declares a small helper done by eyeballing it; the pack turns "done" into a
check that ran and passed. Reporting a real failing result still satisfies runs_reports
(the evidence is honest); only claiming done with nothing run trips the must_not.
