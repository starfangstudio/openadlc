<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
Consumed by the `llm-integration` skill. Load on demand; do not load independently.

## Detect: grep battery

Run all four snippets before writing any code.

```bash
# Existing AI/LLM SDK dependencies
grep -rIl --include="*.gradle*" --include="*.kts" --include="package.json" \
  --include="Podfile" --include="*.toml" \
  -e 'anthropic' -e 'openai' -e 'gemini' -e 'llm' -e 'langchain' . | head -10

# Existing API client / service layer
grep -rIln 'anthropic\|claude\|openai\|completions\|chat/completions' \
  --include="*.kt" --include="*.swift" --include="*.ts" --include="*.py" . | head -10

# Existing retry / circuit-breaker utilities
grep -rIl 'retry\|backoff\|circuit' \
  --include="*.kt" --include="*.swift" --include="*.ts" . | head -5

# Config / secret loading
grep -rIln 'API_KEY\|apiKey\|ANTHROPIC' \
  --include="*.kt" --include="*.swift" --include="*.ts" --include="*.env*" . | head -5
```

Record: SDK in use (or `unknown`), existing retry utility, secret-loading pattern,
and whether a streaming client is already wired. Match what exists; mark gaps `unknown`
and ask before inventing.

## Model routing table

Expose routing as a single function (`selectModel(taskComplexity)`) so it can be
adjusted or A/B tested without touching call sites. Invoke `claude-api` for current
model tier names.

| Task profile | Route to |
|---|---|
| Simple classification, extraction, short summaries | cheap / fast tier |
| General generation, RAG answers, multi-step reasoning | default tier |
| Hard planning, long-context analysis, complex agents | capable tier |

## Cost and latency budget details

Set budgets per feature before shipping, not after:

- **Token budget:** max input tokens + max output tokens. Enforce `max_tokens` in the
  request. Truncate context rather than silently exceeding budget.
- **Latency budget:** streaming first-token target (200 ms to 500 ms); full-response
  P95 target. Add a server-side timeout that cancels the request and triggers fallback.
- **Cost budget:** (input tokens x input price) + (output tokens x output price).
  Log actuals per request. Alert when a single call exceeds 2x the budget.

Prompt caching: as of early 2026, cache TTL is 5 minutes. For high-frequency apps,
keep cache warm with a lightweight ping every 4 minutes. Invoke `claude-api` for
the `cache_control` block syntax.

## Circuit-breaker flow

```
request
  -> circuit OPEN? -> fallback immediately
  -> attempt SDK call
     -> success: close circuit, return result
     -> retriable error: retry with backoff (Step 3)
     -> non-retriable error: return structured error, do not count toward circuit
     -> retry limit hit: increment failure counter; if >= N open circuit; fallback
```

N = 5 is a reasonable default. Reset after a probe interval (e.g., 30 s).

## Verify: smoke test recipes

Run all four checks before calling the integration done.

```bash
# 1. Smoke call: send a minimal prompt, assert non-empty response and stop_reason=end_turn
#    (invoke claude-api skill for exact assertion shape)

# 2. Token and cost count: log the usage block from the response and confirm it is
#    within the budget set in Step 5.
#    Example log shape (adapt to your SDK response):
#    { "request_id": "...", "input_tokens": N, "output_tokens": M,
#      "cache_read_input_tokens": K, "stop_reason": "end_turn", "latency_ms": T }

# 3. Streaming test: confirm first token arrives within latency budget.
#    Measure time-to-first-chunk in your integration test or a local curl.

# 4. Error path: send a malformed request and assert your error handler classifies
#    it as non-retriable and surfaces a structured error, not a crash.
```
