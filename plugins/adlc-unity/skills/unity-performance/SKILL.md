---
name: unity-performance
description: >-
  This skill should be used when the user asks to "optimize the game for mobile", "reduce
  draw calls", "fix frame rate drops on low-end devices", "profile the game", "reduce GC
  allocations", "fix GC spikes", "implement object pooling", "batch draw calls", "reduce
  build size", "optimize textures", "set up addressables for memory", "hit 30 fps on
  low-end Android", "reduce battery drain", "connect Unity Profiler to device", "take a
  Memory Profiler snapshot", "find a memory leak", "reduce instantiate/destroy in the game
  loop", "enable SRP Batcher", "set up GPU instancing", "reduce managed heap usage", or
  "profile the auto-battler/Stairway on device". Covers the full mobile performance stack:
  draw-call batching, object pooling, GC/allocation avoidance, Addressables memory
  discipline, Profiler + Memory Profiler workflow, texture compression, and build-size
  stripping for Unity 6 URP on Android/iOS.
version: 0.1.0
---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# Unity performance

Hit mobile F2P frame and memory budgets on low-end devices. Every step below follows the
detect-first rule: inspect the project's actual settings before changing anything.

## Step 1: Detect target devices and current frame budget

Never assume target hardware or current headroom. Inspect first: check minimum API level,
Graphics APIs, current `Application.targetFrameRate`, and URP Asset SRP Batcher flag.
For the exact shell commands, see
[references/unity-performance-detail.md](references/unity-performance-detail.md).

Record: minimum device tier, frame rate cap, SRP Batcher state, GPU Resident Drawer state.
Mark anything undetermined `unknown` and ask; never invent device targets.

Set baselines before changing anything: take a Profiler capture on the worst-case gameplay
moment on the lowest supported device. Record frame time ms, draw call count, GC.Alloc per
frame, and texture memory. For frame budget and draw call budget tables, see
[references/unity-performance-detail.md](references/unity-performance-detail.md).

## Step 2: Draw-call batching

Check the current batching method and apply the correct one. Do not layer multiple methods
without reason; they interact. Decision logic: SRP Batcher first (URP default), then GPU
Instancing for identical moving meshes, Static Batching for non-moving geometry, and Sprite
Atlas for UI/sprites. Disable Static Batching if GPU Resident Drawer is active (they
conflict in Unity 6).

For the full batching decision tree, per-method verification steps, and GPU Resident Drawer
interaction notes, see [references/unity-performance-detail.md](references/unity-performance-detail.md).

## Step 3: Object pooling

No `Instantiate`/`Destroy` in `Update`, `FixedUpdate`, or any per-frame callback. Every
spawnable object (units, projectiles, hit effects, UI popups) must be pooled.

Use Unity 6's built-in `UnityEngine.Pool.ObjectPool<T>` for simple cases. Pre-warm during
scene load, size to peak concurrency + 20% headroom, log a warning when a pool expands at
runtime (never throw). For the typed pool pattern with code sample and lifecycle rules, see
[references/unity-performance-detail.md](references/unity-performance-detail.md).

Verify: after one full gameplay session, Profiler -> Memory module shows a flat "GC
Allocated" graph with no per-frame spikes from spawns.

## Step 4: GC and allocation avoidance

No per-frame managed allocations in the hot path. Check the CPU Profiler's "GC Alloc"
column for any non-zero entries inside `Update`/`FixedUpdate`/render callbacks.

Key patterns: pre-allocate `List<T>`, cache `WaitForSeconds`, replace string interpolation
with `TextMeshPro.SetText` overloads, remove LINQ from hot paths, use `Span<T>`/`stackalloc`
for frame-local scratch space, and annotate lockstep sim jobs with `[BurstCompile]`.

For the full allocation pattern table with problem/fix pairs, see
[references/unity-performance-detail.md](references/unity-performance-detail.md).

## Step 5: Addressables memory discipline

Every `AsyncOperationHandle` must be released with `Addressables.Release(handle)` when the
owning system unloads. Leaked handles keep their AssetBundle in memory indefinitely.

- Group assets by lifetime (scene-local vs. persistent core); never mix them in one group.
- Avoid asset churn: releasing then immediately re-loading the same bundle triggers a full
  unload/reload cycle. Track reference counts at the system level.
- Monitor: Window -> Asset Management -> Addressables -> Event Viewer.
- Verify after each scene transition: Memory Profiler snapshot comparison shows no leaked
  texture or mesh objects from the previous scene.

## Step 6: Profiler and Memory Profiler workflow

Connect the Profiler to a device, capture on the worst-case frame, then triage in order:
frame time spikes (CPU Hierarchy), GC spikes (Record Allocations), draw calls (Rendering
module + Frame Debugger), texture memory (Memory Profiler snapshot comparison).

For the adb forward command, iOS connection steps, the 4-step triage sequence, and the
snapshot comparison procedure, see
[references/unity-performance-detail.md](references/unity-performance-detail.md).

## Step 7: Texture compression and build size

Use ASTC 6x6 for Android API 23+ and iOS; ASTC 4x4 for characters/UI; ETC2 as legacy
Android fallback (without ASTC the device decompresses to RGBA32, doubling memory).

Build stripping: Managed Stripping Level High (IL2CPP) + Strip Engine Code + Shader
Stripping via a Variant Collection + Vorbis for music / ADPCM for short SFX.

For the full compression table and stripping step sequence, see
[references/unity-performance-detail.md](references/unity-performance-detail.md).

Verify: compare build size before and after. Report delta to the user.

## Verify: pass/fail criteria

A change is done only when all criteria pass on the lowest supported device: frame time
within budget, zero per-frame GC allocs in the hot path, draw calls within tier budget,
no leaked objects between scene transitions, and build size within the operator's target.

For the exact numbered checklist, see
[references/unity-performance-detail.md](references/unity-performance-detail.md).

Do not report a fix as done based on code review alone; always run the profiler check.

## Outbound checkpoint

Local work needs no approval. Outbound here (uploading a build to the Play Store, App Store, Firebase App Distribution, or any CI/CD artifact store): stop, present exactly what would go out, and ask the operator for an explicit "yes" first.

## References

- [references/unity-performance-detail.md](references/unity-performance-detail.md) -- full detail: device
  detection commands, frame/draw-call budget tables, batching decision tree, pool code
  sample, allocation pattern table, profiler workflow, texture compression table, build
  stripping steps, and pass/fail checklist.
- [references/unity-performance.md](references/unity-performance.md) -- mobile perf checklist (legacy
  reference; superseded by unity-performance-detail.md for items above).
- Unity Manual: Draw Call Batching -- https://docs.unity3d.com/Manual/DrawCallBatching.html
- Unity Manual: SRP Batcher -- https://docs.unity3d.com/Manual/SRPBatcher.html
- Unity Manual: GPU Resident Drawer (URP, Unity 6) -- https://docs.unity3d.com/6000.0/Documentation/Manual/urp/gpu-resident-drawer.html
- Unity Manual: Addressables Memory Management -- https://docs.unity3d.com/Packages/com.unity.addressables@2.4/manual/MemoryManagement.html
- Unity Manual: CPU Profiler -- https://docs.unity3d.com/Manual/ProfilerCPU.html
- TheGamedev.Guru: Unity Draw Call Batching Ultimate Guide (2026) -- https://thegamedev.guru/unity-performance/draw-call-optimization/
