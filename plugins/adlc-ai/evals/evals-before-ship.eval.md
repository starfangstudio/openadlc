---
id: evals-before-ship
pack: adlc-ai
targets: llm-evals, prompt-engineering
baseline: no-pack
---
# Evals gate an LLM feature before it is called done

## Scenario
```text
Here's a prompt that classifies an incoming support email as billing, technical, or account. Ship it once it works.
```

## Baseline trap
A no-pack agent writes or tweaks the classification prompt, runs it once against one or two hand-picked emails, sees plausible labels, and declares it done. No golden/labeled set is built, no schema or exact-match assertions are written, edge and ambiguous inputs are never exercised, and there is no repeatable RESULT: PASS/FAIL gate. 'It works' rests on eyeballing one run. The pack's llm-evals Step 2 3-evals-first rule requires at least three eval cases before shipping any prompt, Step 8 requires a machine-readable RESULT: PASS or RESULT: FAIL line as the evidence, and prompt-engineering Step 9 forbids a prompt change without a regression test ('looks right' is not a passing bar).

## Assertions
```json
[
  {
    "id": "writes_eval_cases",
    "type": "must",
    "points": 2,
    "target": "llm-evals",
    "signal": "Agent builds at least three labeled eval cases (a golden/labeled set) for the classifier, including at least one edge or ambiguous input, before declaring the feature shippable."
  },
  {
    "id": "runnable_gate",
    "type": "must",
    "points": 1,
    "target": "llm-evals",
    "signal": "Agent runs the eval suite and reports a machine-readable pass/fail result (a RESULT: PASS or RESULT: FAIL line with case counts) as the evidence that the work is done."
  },
  {
    "id": "regression_pairing",
    "type": "must",
    "points": 1,
    "target": "prompt-engineering",
    "signal": "Agent stores the prompt paired with a runnable regression test (an eval file the prompt ships with) rather than declaring it done on a single eyeballed run."
  },
  {
    "id": "done_on_eyeball",
    "type": "must_not",
    "points": 0,
    "target": "llm-evals",
    "signal": "Agent declares the classifier ready to ship without any eval case having been written and run."
  }
]
```

## Notes
Maps to llm-evals Step 2 (the 3-evals-first rule: at least 3 eval cases before shipping any prompt) and Step 8 (the runner MUST emit RESULT: PASS/FAIL; no claimed pass without it), plus prompt-engineering Step 9 (a prompt change without a regression test is a blind deploy; 'looks right' is not a passing bar). Trap is honest because a bare agent routinely calls a small classifier prompt done after one eyeballed run; the pack turns 'ship it once it works' into an eval set that ran and produced a pass/fail. Writing the eval file itself is not the banned behavior; only declaring done with nothing written and run trips the must_not. Revised: tightened the regression_pairing signal from the softer 'treats as a versioned artifact' phrasing to the observable 'stores the prompt paired with a runnable regression test / eval file', which is what prompt-engineering Step 9 concretely requires.
