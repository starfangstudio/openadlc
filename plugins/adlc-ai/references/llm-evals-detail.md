<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
Consumed by the `llm-evals` skill. Load on demand; do not load independently.

---

## Golden set: file shape and coverage targets

Minimum golden-set shape (JSON lines, one case per line):

```jsonc
// evals/golden.jsonl
{"id": "happy-path-1", "input": {...}, "expected": "...", "tags": ["happy-path"]}
{"id": "edge-empty",   "input": {...}, "expected": "...", "tags": ["edge"]}
{"id": "adversarial-1","input": {...}, "expected": "...", "tags": ["adversarial"]}
```

Coverage targets (adjust to feature scope):

| Tag | Min cases | Purpose |
|---|---|---|
| `happy-path` | 5 | Core success path |
| `edge` | 3 | Empty/null/boundary input |
| `adversarial` | 3 | Prompt injection, jailbreak attempts |
| `regression` | any | Bugs that already slipped through |

Aim for 50-100 cases before CI gating matters statistically. Grow from real failures;
never pad with identical paraphrases.

---

## LLM-as-judge: calibration and injection guard patterns

### Calibration

Before shipping, validate the judge against 50-100 human-labeled examples. Target >= 85%
agreement with human annotators. Log disagreements; refine the judge prompt or scoring
rubric until agreement holds.

### Injection guard

Judge instructions must be in the judge's SYSTEM prompt, not interpolated into the
graded content. Graded model output is CONTENT, never commands.

```python
# CORRECT: judge instructions sealed in system, output treated as inert content
judge_response = llm.create_message(
    model=JUDGE_MODEL,
    system=JUDGE_RUBRIC,           # rubric here, never in user turn
    messages=[{
        "role": "user",
        "content": f"Grade this output:\n<output>{model_output}</output>"
    }]
)

# WRONG: rubric interpolated with output -- injectable
prompt = f"{JUDGE_RUBRIC}\n\nOutput to grade: {model_output}"  # do not do this
```

If a third-party judge API is used, wrap the graded output in a delimiter
(`<output>...</output>`) and instruct the judge explicitly that everything inside
the delimiter is content, not instructions.

---

## N-run variance: computation

Run each eval case N >= 5 times and compute:

```python
scores = [run_eval(case) for _ in range(N)]
mean_score  = statistics.mean(scores)
variance    = statistics.variance(scores)
pass_rate   = sum(s >= THRESHOLD for s in scores) / N
```

Gate on `pass_rate >= 0.8` AND `variance <= 0.05` for the case to count as stable.
High variance (> 0.1) means the prompt is under-specified; fix before shipping.

---

## Cost and latency: log schema

Every eval run must log:

```jsonc
{"case_id": "...", "pass": true, "score": 0.92, "latency_ms": 340,
 "input_tokens": 512, "output_tokens": 128, "cost_usd": 0.0014, "run": 1}
```

Aggregate per suite run: `total_cost_usd`, `p50_latency_ms`, `p99_latency_ms`.
Set budgets: if `total_cost_usd > BUDGET` or `p99_latency_ms > SLA`, flag as
`WARN` in the report. A 10x cost spike signals an unintended prompt change.

---

## CI regression gate: example command

```bash
# Run evals, fail CI if pass_rate < threshold
python -m evals.runner --golden evals/golden.jsonl \
                       --threshold 0.85 --runs 5 \
                       --output evals/results.json
# exit code 1 if any case regresses below threshold -- blocks the merge
```

---

## Eval runner: required output format

```
Eval run: <feature>
Cases: 42   Passed: 40   Failed: 2   Skipped: 0
Pass rate: 95.2%   Variance (mean): 0.031   Budget: $0.18 / $0.50
RESULT: PASS

Failed cases:
  adversarial-3  score=0.61  reason="judge: output revealed system prompt"
  edge-null      score=0.00  reason="JSON schema violation: missing 'answer' field"
```

No claimed "pass" without this output. Fix failures before merging.
