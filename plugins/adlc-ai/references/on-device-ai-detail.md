<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
Consumed by the `on-device-ai` skill. Load on demand; do not load independently.

# On-device AI: implementation detail

---

## iOS toolchains

### Foundation Models framework (iOS 26+, preferred)

Apple's on-device LLM (~3B AFM 3 Core on A17+; 20B AFM 3 Core Advanced on M-class).
Zero-cost inference, offline, Swift-native, structured output via `@Generable`.

```swift
import FoundationModels

let session = LanguageModelSession()
let response = try await session.respond(to: "Classify this usage pattern: \(input)")
```

Minimum deployment target: iOS 26. Check `SystemLanguageModel.availability` before
calling; `.notAvailable` means fall through to cloud (Step 6 of the skill).

### Core ML (iOS 12+, custom/fine-tuned models)

Bring your own model (`.mlpackage`). Targets Neural Engine, GPU, or CPU automatically.
Use when Foundation Models cannot be fine-tuned enough for the task, or when min target
is below iOS 26.

```swift
import CoreML
let model = try MyModel(configuration: MLModelConfiguration())
let prediction = try model.prediction(input: MyModelInput(features: features))
```

Convert from PyTorch/ONNX with `coremltools`:

```python
ct.convert(..., minimum_deployment_target=ct.target.iOS17)
```

---

## Android toolchains

### Gemini Nano via ML Kit GenAI (Android 10+, flagship hardware)

System model managed by AICore; no download in your APK. Access via ML Kit GenAI APIs.
Requires: flagship-class SoC, 12 GB+ RAM, Gemini Nano v3+ installed (AICore).

Availability guard is mandatory; roughly 60-70% of 2026 devices with Android 10+ lack the
required silicon. Fall through to cloud when unavailable.

```kotlin
val genAI = GenerativeModel(GenerativeBackend.ON_DEVICE)
val availability = genAI.checkAvailability()
if (availability == Availability.AVAILABLE) {
    val response = genAI.generateContent(content { text(prompt) })
}
```

### LiteRT / LiteRT-LM (broad device support)

Formerly TensorFlow Lite. Use for custom/fine-tuned models or when Gemini Nano is
unavailable. `LiteRT-LM` wraps LiteRT with a text-generation API for SLMs.
Supports NNAPI, GPU delegate, and Hexagon DSP on Qualcomm chips.

```kotlin
val interpreter = LlmInference.createFromFile(context, modelPath)
val result = interpreter.generateResponse(prompt)
```

---

## Cross-platform runtimes (React Native / KMP)

**MLC LLM**: compiles models to native Metal (iOS) and OpenCL/Vulkan (Android).
Single model config; pre-quantized variants at `mlc-ai/binary` (q4f16, q4f32).
Llama 3.2 3B q4f16_1 achieves ~18-25 tok/s on Snapdragon 8 Gen 3.

**llama.cpp**: widest hardware coverage; CPU-first with optional GPU offload.
Best for lowest-common-denominator device support or when NPU access is blocked.

**ONNX Runtime Mobile**: bring your own ONNX model; supports CoreML EP (iOS) and
NNAPI EP (Android) execution providers for hardware acceleration.

---

## Quantization and model-size tradeoffs

Select quantization based on device RAM budget and quality floor:

| Precision | Model size (3B params) | Quality loss | Use when |
|---|---|---|---|
| fp16 | ~6 GB | None | iPads/Mac, not phone |
| q8_0 | ~3.1 GB | Minimal | High-end phones, quality-critical |
| q4_f16 (k-quant) | ~1.8 GB | Low | Default for flagship phones |
| q4_0 | ~1.6 GB | Moderate | Mid-range, tight RAM |
| q2_K | ~1.1 GB | High | Last resort; verify quality |

Never ship a quant without a pass/fail quality check against an unquantized baseline.

---

## Benchmark recipe (Step 5)

Run on a real device, not the simulator.

```bash
# iOS: measure via Xcode Instruments or an in-app timer
# Record: first-token latency (ms), tokens/s, peak memory (MB)

# Android: adb shell + dumpsys for memory; logcat timer
adb shell am start -n com.example/.BenchmarkActivity
adb logcat -s OnDeviceAI:D | grep -E 'first_token_ms|tokens_per_s|peak_mem_mb'
```

Acceptance criteria (adjust per task):
- First-token latency: under 800 ms on target device
- Sustained throughput: at least 8 tok/s (readable streaming)
- Peak memory: model size + 20% headroom fits in device RAM budget
- Quality gate: task accuracy within 5 pp of unquantized baseline

Do not claim done without logged numbers from a real device.
