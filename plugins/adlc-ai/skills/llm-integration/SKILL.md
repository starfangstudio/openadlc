---
name: llm-integration
description: >-
  Covers the full production lifecycle for wiring an LLM into an app: SDK setup,
  streaming, retries, model routing, cost budgeting, prompt caching, and graceful
  degradation. Use this skill when the user asks to "integrate Claude into my app",
  "add streaming responses", "handle LLM errors and retries", "route between cheap
  and expensive models", "add a fallback when the model is overloaded", or "add
  prompt caching to reduce API costs".
version: 0.1.0
---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# LLM integration

Wire an LLM into an app or service to production quality: provider setup, request
lifecycle, model routing, cost budgeting, prompt caching, and graceful degradation.

**Scope boundary:** this skill governs the HTTP/SDK plumbing and operational patterns.
For exact SDK call shapes, model IDs, pricing, streaming event types, tool-use protocol,
structured outputs, and prompt-caching specifics, DEFER to the built-in `claude-api`
skill. Do not hardcode model IDs or prices here; they rot.

## Step 1: Detect first

Never assume what is already present. Grep before writing anything.
For the full grep battery (SDK deps, API client, retry utilities, secret loading), see
[references/llm-integration-detail.md](../../references/llm-integration-detail.md).

Record: SDK in use (or `unknown`), existing retry utility, secret-loading pattern,
and whether a streaming client is already wired. Match what exists; mark gaps `unknown`
and ask before inventing.

## Step 2: Provider and SDK setup

Use the Anthropic SDK unless the project has an established provider. Invoke the
`claude-api` skill for the exact SDK init call, auth pattern, and any SDK version
constraints. The SDK handles connection pooling and base retry (default `max_retries=2`);
do not layer a duplicate retry on top of that.

Key setup checklist:
- [ ] API key loaded from environment / secret store; never committed.
- [ ] SDK client instantiated once (singleton / DI-provided); not per-request.
- [ ] Request timeout set explicitly (30 s is a safe default for non-streaming; set to
  stream-first-byte for streaming calls so the connection does not hang silently).
- [ ] Logging: log request ID, input token count, output token count, stop reason,
  latency. Never log prompt content or user data in plain text.

## Step 3: Request lifecycle

### Streaming

Stream for any user-facing text generation. Streaming cuts perceived latency by
displaying the first token within ~200 ms vs. waiting for the full response.

Invoke `claude-api` for the streaming event loop. At the app layer:
- Connect a streaming coroutine / async iterator to the UI state.
- Cancel the stream (and the upstream request) if the user navigates away.
- Flush a `[DONE]` or terminal event to close the UI loading state.

### Timeouts, retries, and backoff

The SDK retries 429 (rate limit) and 529 (overloaded) automatically with exponential
backoff. Override the default only if you need tighter SLAs.

For application-level retries beyond the SDK defaults, use exponential backoff with
jitter (start 1 s, cap 60 s, jitter ±30%). Limit retries to 3 total attempts. After
the limit, propagate to the fallback (Step 5) or return a structured error to the UI.

Distinguish error types before deciding to retry:
- `overloaded_error` (529): transient; retry with backoff.
- `rate_limit_error` (429): your quota; back off longer or queue.
- `authentication_error` (401): never retry; surface immediately.
- `invalid_request_error` (400): your bug; never retry; fix the prompt.

### Idempotency

LLM calls are not inherently idempotent. If a retry must not produce a duplicate
side-effect (e.g., a saved record), generate a stable request ID before the first
attempt and check whether the result was already persisted before re-calling.

## Step 4: Model routing

Route by task complexity. For the routing table and function contract, see
[references/llm-integration-detail.md](../../references/llm-integration-detail.md).

## Step 5: Cost and latency budget

Set a budget per feature before shipping, not after. Enforce `max_tokens` in the
request; log actuals per call; alert when a single call exceeds 2x the budget.
Use prompt caching for any context that repeats across requests (system prompt,
retrieved documents, tool schemas).

Fallback minimum (usable without opening the reference): per-request token budget
= expected input tokens + `max_tokens` (the output cap you pass in the request).
Log actual `input_tokens` + `output_tokens` from the response against that number.

For full cost-budget formulas, cache TTL details, and the keep-warm pattern, see
[references/llm-integration-detail.md](../../references/llm-integration-detail.md).

## Step 6: Graceful degradation and fallback

Every AI feature must have a defined fallback. Choose one:

- **Simplified response:** return a canned or rule-based answer.
- **Queue for retry:** store the request and complete it asynchronously.
- **UI degradation:** hide the AI surface; show a "temporarily unavailable" state.

Implement a circuit breaker: after N consecutive failures, open the circuit and route
directly to fallback without attempting the API. Reset after a probe interval.

Fallback minimum (usable without opening the reference): N = 5 consecutive failures
opens the circuit; reset by probing again after 30 s. Tune both from real failure
data once you have it.

For the circuit-breaker flow diagram, see
[references/llm-integration-detail.md](../../references/llm-integration-detail.md).

## Step 7: Verify

Run four checks (smoke call, token/cost count, streaming first-token timing, error-path
classification) before calling the integration done. Do not ship without a passing smoke
call and a logged usage block. For the exact test recipes and log shapes, see
[references/llm-integration-detail.md](../../references/llm-integration-detail.md).

## Outbound checkpoint

Local work needs no approval (including local dev calls against synthetic data). Outbound here (shipping a feature that sends user-generated content such as text, images, audio, or metadata to a third-party model API, via a production deployment, a beta/TestFlight/Play Internal Testing build reaching real user data, or a CI step calling the live API with real data): stop, present exactly what data would leave (fields, purpose, provider, retention policy if known), and get the operator's explicit "yes" first (global consent law).

## References

- Built-in `claude-api` skill: exact SDK calls, model IDs, pricing, streaming event
  shapes, tool-use protocol, structured output, prompt caching syntax, and token
  counting. Load it for any of those specifics rather than duplicating them here.
- [references/llm-integration-detail.md](../../references/llm-integration-detail.md): grep battery, routing
  table, budget formulas, circuit-breaker flow, and verify recipes.
- Anthropic streaming docs: https://docs.anthropic.com/en/docs/build-with-claude/streaming
- Anthropic prompt caching docs: https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching
- Anthropic SDK Python error handling: https://github.com/anthropics/anthropic-sdk-python/discussions/1341
- Anthropic fine-grained tool streaming: https://docs.anthropic.com/en/docs/agents-and-tools/tool-use/fine-grained-tool-streaming
