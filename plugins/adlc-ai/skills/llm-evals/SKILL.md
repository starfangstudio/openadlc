---
name: llm-evals
description: >-
  This skill should be used when the user asks to "write evals for this LLM feature",
  "set up an eval suite before shipping", "add golden-set tests for the prompt", "test
  this AI feature before release", "build an eval harness", "add LLM-as-judge scoring",
  "regression-gate a prompt change", "measure quality variance across runs", "calibrate
  a judge against human labels", "add eval assertions for structured output", "set up
  eval CI for the AI pipeline", or "verify this RAG feature doesn't regress". Builds
  a minimal, runnable eval suite -- golden/labeled set, assertion tiers (exact,
  structured, semantic, LLM-judge), N-run variance, cost+latency tracking, and CI
  regression gate -- before any LLM feature or prompt change ships.
version: 0.1.0
---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# LLM evals

Build a runnable eval suite that produces a deterministic pass/fail + variance signal
BEFORE shipping an LLM feature and BEFORE merging any prompt or model change. Evals
are AI engineering's equivalent of unit tests: write them first, gate on them always.

## Step 1: Detect first

Inspect before creating anything:

```bash
# Existing eval files
find . -type f \( -name "*.eval.*" -o -name "*_eval*" -o -name "evals.*" \) \
       -not -path "*/node_modules/*" -not -path "*/.git/*" | head -20
# Eval framework already installed
cat package.json pyproject.toml requirements*.txt 2>/dev/null | \
  grep -Ei 'deepeval|braintrust|promptfoo|langsmith|evalite' | head
# Existing golden sets / labeled fixtures
find . -name "golden*" -o -name "fixtures*" -o -name "testdata*" | head -10
# Prompt files and model call sites
grep -rn --include="*.ts" --include="*.py" --include="*.kt" \
  'createMessage\|anthropic\|openai\|model=' . 2>/dev/null | head -20
```

Record: framework in use (or `unknown`), any existing golden set, model call sites,
assertion style. Mark anything you cannot determine `unknown` and ask; never invent.

## Step 2: Define the golden/labeled set (the eval floor)

**The 3-evals-first rule:** write at least 3 eval cases before writing or shipping any
prompt. Real cases outperform synthetic ones; mine production logs or design sessions.

For the golden-set file shape and coverage targets (tags, min case counts, growth
guidance), see [references/llm-evals-detail.md](references/llm-evals-detail.md).

## Step 3: Pick assertion types (pyramid, cheapest first)

Run assertions in order; skip expensive tiers when cheaper ones already fail.

**Tier 1 -- Exact / structural (sub-millisecond, always run)**
- Exact match for closed-form answers (classification label, JSON field value).
- JSON schema validation for all structured outputs.
- Regex / `contains` for required field presence.

**Tier 2 -- Semantic (fast, run when Tier 1 passes)**
- Embedding cosine similarity >= 0.85 against pinned reference answer (pin the
  embedding model; do NOT use the same model under test).
- ROUGE / BERTScore for summarization features.

**Tier 3 -- LLM-as-judge (slowest, run on survivors of Tier 1+2)**
Reserve for open-ended rubrics: helpfulness, tone, instruction-following, faithfulness.
See Step 4 for judge setup.

## Step 4: LLM-as-judge -- calibration + injection guard

Calibrate the judge against 50-100 human-labeled examples before shipping; target
>= 85% agreement. High-variance disagreements indicate a rubric that needs tightening.

For the calibration procedure, the injection-safe Python pattern, and the third-party
judge wrapping convention, see [references/llm-evals-detail.md](references/llm-evals-detail.md).

## Step 5: N-run variance -- reliability, not single-shot

Never report a single-run pass as done. Run each eval case N >= 5 times.
Gate on `pass_rate >= 0.8` AND `variance <= 0.05` for the case to count as stable.
High variance (> 0.1) means the prompt is under-specified; fix before shipping.

For the computation snippet, see [references/llm-evals-detail.md](references/llm-evals-detail.md).

## Step 6: Cost and latency in the eval

Every eval run must log `case_id`, `pass`, `score`, `latency_ms`, `input_tokens`,
`output_tokens`, and `cost_usd` per run. Aggregate `total_cost_usd`, `p50_latency_ms`,
`p99_latency_ms` per suite. Flag `WARN` if cost exceeds budget or p99 exceeds SLA.
A 10x cost spike signals an unintended prompt change.

For the log schema and aggregation example, see [references/llm-evals-detail.md](references/llm-evals-detail.md).

## Step 7: Regression-gate prompt and model changes

Pin the metric definition in version control alongside the prompt. Any prompt edit,
model swap, or system-message change triggers a full eval run against the golden set.
A case that previously passed and now fails is a regression; the PR is blocked until
fixed or the case is explicitly retired.

For the CI runner command, see [references/llm-evals-detail.md](references/llm-evals-detail.md).

## Step 8: Verify (pass/fail, not "looks right")

The eval runner MUST emit a machine-readable result with case counts, pass rate,
variance, budget usage, and a `RESULT: PASS` or `RESULT: FAIL` line. No claimed
"pass" without this output. Fix failures before merging.

For the required output format, see [references/llm-evals-detail.md](references/llm-evals-detail.md).

## Outbound checkpoint

Local work needs no approval. Outbound here (posting eval results to an external eval platform, pushing eval data containing user PII to any remote, publishing benchmark numbers publicly): stop, present exactly what would go out, and get the operator's explicit "yes" first (global consent law).

## References

- [references/llm-evals-detail.md](references/llm-evals-detail.md) -- golden-set shapes, coverage
  targets, injection guard patterns, N-run computation, log schema, CI command, and the
  required eval output format.
- [references/llm-evals.md](references/llm-evals.md) -- eval file shapes, LLM-judge
  calibration detail, injection guard patterns, and a runnable Python eval harness.
- DeepEval LLM-as-judge guide (2026): https://deepeval.com/guides/guides-llm-as-a-judge
- FutureAGI deterministic eval metrics (2026): https://futureagi.com/blog/deterministic-llm-evaluation-metrics-2026/
- Braintrust LLM evaluation metrics guide: https://www.braintrust.dev/articles/llm-evaluation-metrics-guide
- Maxim golden dataset construction guide: https://www.getmaxim.ai/articles/building-a-golden-dataset-for-ai-evaluation-a-step-by-step-guide/
- Optimization-based prompt injection attack to LLM-as-judge (arXiv 2403.17710): https://arxiv.org/abs/2403.17710
