---
name: on-device-ai
description: >-
  This skill should be used when the user asks to "run inference on-device", "add on-device
  AI", "keep data off the server", "run a model locally on iOS", "run a model locally on
  Android", "integrate Gemini Nano", "use Foundation Models framework", "add Core ML
  inference", "use LiteRT", "use MLC LLM on mobile", "use llama.cpp on mobile", "use ONNX
  Runtime on device", "quantize a model for mobile", "add an offline AI feature", "avoid
  sending user data to the cloud", "privacy-preserving inference", "reduce inference cost",
  "reduce inference latency", "add a hybrid on-device/cloud fallback", or "run a small
  language model on the phone". Covers iOS (Foundation Models framework, Core ML) and
  Android (Gemini Nano via AICore/ML Kit GenAI, LiteRT, LiteRT-LM), cross-platform
  runtimes (MLC LLM, llama.cpp, ONNX Runtime Mobile), quantization/model-size tradeoffs,
  and the hybrid on-device-first/cloud-fallback pattern.
version: 0.1.0
---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# On-device AI

Run ML inference on the device: data never leaves, latency is zero-network, and marginal
cost per call is zero. The tradeoff is a hard capability ceiling -- model size is bounded
by RAM and the on-device accelerator -- so design for a hybrid path from day one.

## Step 1: Detect first

Inspect the target project before touching any code:

```bash
# Platform(s) in scope
ls android/ ios/ *.xcodeproj *.xcworkspace 2>/dev/null | head
# Existing ML integration
grep -rIl --include="*.swift" --include="*.kt" \
  -e 'CoreML\|FoundationModels\|MLModel' \
  -e 'GeminiNano\|AICore\|MediaPipe\|LiteRT\|TFLite' \
  -e 'MLC\|llama_cpp\|OnnxRuntime' . | head
# Existing model assets
find . -name "*.mlpackage" -o -name "*.mlmodel" \
       -o -name "*.tflite" -o -name "*.onnx" 2>/dev/null | head
# Min OS targets (affects API availability)
grep -E 'minSdk|IPHONEOS_DEPLOYMENT_TARGET|deploymentTarget' \
  $(find . -name "build.gradle*" -o -name "*.xcconfig" -o -name "project.pbxproj" \
    2>/dev/null | head -5) 2>/dev/null
```

Record: platforms in scope, existing runtime, model assets, min OS. Mark anything
you cannot determine `unknown`; never assume a runtime is available.

## Step 2: Decide on-device vs. cloud

| Dimension | On-device wins | Cloud wins |
|---|---|---|
| Privacy | User data never leaves | Data sent to server |
| Latency | Zero network RTT | 50-500 ms network + queue |
| Cost | Zero marginal per call | Token/compute billing |
| Capability | Bounded by device RAM + NPU | Unbounded (GPT-4-class, etc.) |
| Model freshness | OTA update required | Instant server-side swap |
| Battery | Non-trivial NPU draw | Offloaded |

Default heuristic: keep all user-content inference (classification, embedding,
summarization of private data) on-device. Reach for cloud only for tasks that
demonstrably exceed what a ~3B-parameter model can do, and only with the operator's
explicit yes first (Step 7 below).

## Step 3: Choose the toolchain

**iOS:** Prefer Foundation Models framework (iOS 26+, ~3B AFM on-device LLM, zero-cost,
Swift-native). Fall back to Core ML (iOS 12+) for custom/fine-tuned models or lower
deployment targets.

**Android:** Prefer Gemini Nano via ML Kit GenAI (flagship SoC, 12 GB+ RAM, AICore).
~60-70% of 2026 Android 10+ devices lack the required silicon, so an availability guard
and fallback to LiteRT/LiteRT-LM is mandatory for broad support.

**Cross-platform (React Native / KMP):** MLC LLM for Metal/Vulkan-accelerated inference;
llama.cpp for widest hardware coverage; ONNX Runtime Mobile when you need CoreML EP or
NNAPI EP acceleration with a portable model format.

For API signatures, code samples, and `coremltools` conversion commands,
see [references/on-device-ai-detail.md](../../references/on-device-ai-detail.md).

## Step 4: Quantization

Pick the lowest precision that clears your quality gate. Rule of thumb: q4_f16 (k-quant)
for flagship phones (~1.8 GB for a 3B model), q4_0 for mid-range, q8_0 when
quality-critical. Never ship a quant without a pass/fail check against the unquantized
baseline.

For the full precision-vs-size table,
see [references/on-device-ai-detail.md](../../references/on-device-ai-detail.md).

## Step 5: Verify (pass/fail benchmark)

Run on a real device. Minimum bar: first-token latency under 800 ms, throughput at
least 8 tok/s, peak memory within budget, task accuracy within 5 pp of unquantized
baseline. Do not claim done without logged numbers.

For the adb/Instruments benchmark commands and full acceptance criteria,
see [references/on-device-ai-detail.md](../../references/on-device-ai-detail.md).

## Step 6: Hybrid pattern (on-device first, cloud fallback)

Design the call site so cloud is opt-in, not default:

```
User request
    |
    v
[On-device available? Foundation Models / Gemini Nano / LiteRT]
    | Yes                           | No / unavailable
    v                               v
Run locally                   [OUTBOUND CHECKPOINT -- Step 7]
Return result                 Present: what data would leave,
                              which cloud endpoint, wait for "yes"
```

Cloud fallback uses the `claude-api` skill for Anthropic SDK integration; do NOT
hardcode model IDs or pricing here -- they rot. Defer to that skill.

Route to cloud only for: complex multi-step reasoning, tasks that require > 3B context
understanding, or when the on-device availability check fails.

## Step 7: Outbound checkpoint

Generating and running on-device inference code locally needs no approval. The on-device path
is a privacy win: no data leaves the device and no consent is needed.

Any cloud fallback that sends user data to an external API is outbound: stop, present
exactly what data would leave (prompt content, user identifiers, request metadata) and
which endpoint would receive it, and wait for the operator's explicit "yes" per the global
CLAUDE.md. Do not wire a cloud fallback silently.

## References

- Apple Foundation Models framework (WWDC 2026): https://developer.apple.com/videos/play/wwdc2026/241/
- Apple Machine Learning Research -- AFM 3: https://machinelearning.apple.com/research/introducing-third-generation-of-apple-foundation-models
- Core ML developer docs: https://developer.apple.com/documentation/coreml
- Android AI on-device (Gemini Nano, LiteRT, ML Kit GenAI): https://developer.android.com/ai/gemini-nano
- Google I/O 2026 -- Android AI updates: https://developer.android.com/blog/posts/top-ai-on-android-updates-for-building-intelligent-experiences-from-google-i-o-26
- LiteRT (formerly TensorFlow Lite): https://developers.googleblog.com/litert-the-universal-framework-for-on-device-ai/
- MLC LLM cross-platform setup: https://localaimaster.com/blog/mlc-llm-setup-guide
- On-device LLM framework comparison 2026: https://cactuscompute.com/compare/best-on-device-llm-framework
- Implementation detail (code samples, quantization table, benchmark recipe): [references/on-device-ai-detail.md](../../references/on-device-ai-detail.md)
