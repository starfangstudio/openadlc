---
name: ai-safety-guardrails
description: >-
  This skill should be used when the user asks to "make this AI feature safe to
  ship", "add guardrails to the LLM call", "prevent prompt injection", "defend
  against jailbreaking", "redact PII from model output", "stop the model from
  leaking my system prompt", "validate model output schema", "handle model
  refusals", "add rate limiting to an AI endpoint", "audit what user data we
  send to the model", "on-device vs cloud privacy decision", "comply with GDPR
  on AI features", or "red-team this AI feature". Covers input guardrails
  (prompt-injection and jailbreak defense, untrusted-content quarantine),
  output guardrails (PII redaction, content moderation, schema validation,
  secret-leak prevention), privacy (data minimisation, on-device vs cloud,
  retention), refusal/uncertainty handling, and abuse/rate-limiting. Ties to
  adlc-security (injection is an injection class) and to privacy concerns
  around user content sent to third-party model providers.
version: 0.1.0
---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# AI safety guardrails

Make an AI feature safe to ship to real users. Layered defense: input guardrails
block attacks before the model, output guardrails sanitize what the model
produces, privacy constraints bound what data reaches any model at all.

**Boundary:** this skill builds the guardrails in; the `ai-reviewer` agent audits
a diff afterward to check whether those guardrails are actually present and correct.
Use this skill to add defenses, use `ai-reviewer` to verify a change before it ships.

## Step 1: Detect first

Never assume. Inspect the feature before adding anything.

For detection commands, see [references/ai-safety-guardrails-detail.md](../../references/ai-safety-guardrails-detail.md).

Record: model provider, call sites, existing sanitization, data fields sent to
the model. Mark anything you cannot determine `unknown`, ask rather than guess.

## Step 2: Privacy -- bound what reaches the model

Decide the data tier before writing a single line of guardrail code:

1. **On-device capable?** Route there if the model handles the task. No data
   leaves the device. (Core ML, LiteRT, Gemini Nano, MLC LLM.) Mark the feature
   as on-device in privacy docs.
2. **Anonymizable?** Strip PII before the API call. Use placeholder tokens
   (`[USER_NAME]`, `[EMAIL]`); restore in the response if needed. Send only the
   fields the model actually needs for the task.
3. **Cloud API unavoidable?** Verify ZDR option is on, a signed DPA (GDPR/CCPA)
   is in place, and retention period is in the privacy policy. Never log raw
   model inputs/outputs without explicit user consent; log request IDs only.

STOP if the provider, retention policy, or DPA status is `unknown`. Shipping
user content to an unconfirmed third party violates GDPR Article 28.

## Step 3: Input guardrails

Apply in order before every model call. Each check is PASS / FAIL / unknown.

**I-1 Input length cap** -- enforce a max token/char limit before the API call;
return 400 on excess. Prevents token-stuffing and cost abuse.

**I-2 Schema/format validation** (structured inputs only) -- validate with
JSON Schema, Pydantic, or Zod. Reject malformed input before it reaches the model.

**I-3 Direct injection classifier** -- run a regex heuristic layer first (fast,
catches 60-70% of attempts), then an LLM classifier (NeMo Guardrails, Llama Guard 3)
on inputs that pass regex. System-prompt instructions alone do not stop intentional
attacks.

**I-4 Quarantine external/retrieved content** -- wrap any RAG chunks, fetched URLs,
or tool results in structural delimiters before injecting them into the prompt.
For the delimiter format, see [references/ai-safety-guardrails-detail.md](../../references/ai-safety-guardrails-detail.md).

**I-5 Multimodal content scan** -- pass images, audio, or documents through a
moderation API before feeding them to a multimodal model. Adversarial instructions
can be pixel-encoded and are invisible to human review.

## Step 4: Output guardrails

Apply to every model response before returning it to the caller.

**O-1 Schema validation** -- parse the response against the declared output schema.
Reject and surface a structured error if the model deviates. Do not pass malformed
model output to downstream code.

**O-2 PII redaction** -- scan output with a regex layer (email, phone, SSN, card patterns)
plus an NER model. Strip or replace matches; log the redaction event, never the raw value.

**O-3 Secret scan** -- grep output for API-key patterns, env-var names, JWT
prefixes (`sk-`, `Bearer `, `ghp_`, etc.). Never put secrets in system prompts;
if they appear in output, block the response.

**O-4 System-prompt echo block** -- detect if the output contains a verbatim
large fragment of the system prompt. Block and log. Respond to the user with a
generic "I can't share that" rather than the fragment.

**O-5 Content moderation** -- run a content classifier (Llama Guard 3, Perspective API,
or the provider's built-in filter) on every output. Block harmful, hateful, CBRN, or CSAM
content. Log the block reason; do NOT expose the reason code to the user.

**O-6 Refusal / uncertainty handling** -- when the model signals low confidence
or your classifier marks the output as risky, return a structured refusal.
For the response format, see [references/ai-safety-guardrails-detail.md](../../references/ai-safety-guardrails-detail.md).

**O-7 Agentic tool-call validation** -- if the model can invoke tools, validate
every tool name and argument against an allowlist before executing. Treat
model-generated tool calls as untrusted input.

## Step 5: Abuse and rate limiting

- Rate-limit per user/device at the API gateway (requests/minute, tokens/day); return 429 on excess.
- Track injection attempt velocity: N classifier failures within a window blocks the session
  and raises an alert. Tune N from red-team data.
- Log abuse signals (classifier hits, policy blocks, schema rejections) with request IDs
  to a security log, not the application log.

## Step 6: Verify -- red-team eval set

Run before shipping. A pass on every row is required to call the feature done.
For the full eval table and domain-specific case guidance, see [references/ai-safety-guardrails-detail.md](../../references/ai-safety-guardrails-detail.md).

## Outbound checkpoint

Local work needs no approval. Outbound here (enabling a cloud model API that receives real user content, a prod/Play Store/App Store/backend deploy sending user data to a model provider, publishing a privacy policy or DPA change, sending eval inputs to an external red-team or bug-bounty service): stop, present exactly what would go out, and get the operator's explicit "yes" first (global consent law).

## References

- [references/ai-safety-guardrails-detail.md](../../references/ai-safety-guardrails-detail.md) -- detection
  commands, I-4 delimiter format, O-6 refusal format, and the full red-team eval table.
- [references/ai-safety.md](../../references/ai-safety.md) -- injection/jailbreak taxonomy,
  the full input/output guardrail checklist, privacy decision tree, and the
  complete red-team eval set with adversarial examples.
- OWASP LLM Top 10 2025 (LLM01 Prompt Injection, LLM02 Sensitive Information
  Disclosure, LLM07 System Prompt Leakage):
  https://genai.owasp.org/llmrisk/llm01-prompt-injection/
- OWASP LLM Top 10 2025 PDF (all 10 risks):
  https://owasp.org/www-project-top-10-for-large-language-model-applications/assets/PDF/OWASP-Top-10-for-LLMs-v2025.pdf
- NeMo Guardrails (dialog and agentic rails): https://github.com/NVIDIA/NeMo-Guardrails
- Guardrails AI (composable output validators): https://www.guardrailsai.com/docs
- Llama Guard 3 (input/output content classifier):
  https://ai.meta.com/research/publications/llama-guard-3-meta-llama-guard-3/
- Datadog LLM guardrails best practices:
  https://www.datadoghq.com/blog/llm-guardrails-best-practices/
