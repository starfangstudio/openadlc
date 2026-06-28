<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
# Unity Mobile Performance: Checklist + Profiler Workflow

Reference for the `unity-performance` skill. Pull this when you need the full tables and workflow steps.

---

## Frame budget targets (mobile F2P)

| Tier | Device class | Target frame time | Draw call budget | Texture memory budget |
|---|---|---|---|---|
| Low-end | Snapdragon 4xx / Mali G52 / 2 GB RAM | 33 ms (30 fps) | <100 | <150 MB |
| Mid | Snapdragon 7xx / Mali G77 / 4 GB RAM | 16.6 ms (60 fps) | <200 | <300 MB |
| High | Snapdragon 8xx / 8 GB RAM | 16.6 ms (60 fps) | <300 | <512 MB |

Battery: spike to 60 fps during intense moments; default to 30 fps on low-end via `Application.targetFrameRate`.

---

## Batching decision tree (URP / Unity 6)

```
Is your object static (never moves)?
  YES -> Enable Static Batching in mesh import + mark GameObject Static.
         Combines into one VBO at build time; cheapest option.
  NO  -> Are you rendering many identical meshes (units, projectiles, VFX particles)?
           YES -> Use GPU Instancing: enable "Enable GPU Instancing" on the material;
                  pass per-instance data via MaterialPropertyBlock (never set per-object
                  material properties directly -- that breaks instancing).
           NO  -> Does the object share a shader variant with other objects?
                    YES -> SRP Batcher handles it automatically (URP default).
                           Verify: Frame Debugger -> "SRP Batch" entries; Render Stats
                           overlay "Batches" count drops.
                    NO  -> Consolidate to fewer shader variants. Dynamic Batching is
                           deprecated in Unity 6; do not rely on it.
```

SRP Batcher note: it batches by **shader variant**, not by material. Many materials sharing one variant = one SRP batch. Minimize shader keyword combinations.

GPU Resident Drawer (Unity 6 URP): keep rendering data on the GPU to cut CPU-GPU transfers. Enable under URP Asset -> GPU Resident Drawer. **Disable static batching when using it** -- they conflict.

---

## Object pooling patterns

```csharp
// Minimal generic pool -- no per-frame alloc
public sealed class Pool<T> where T : Component
{
    private readonly Stack<T> _inactive = new();
    private readonly T _prefab;
    private readonly Transform _root;

    public Pool(T prefab, Transform root, int preWarm)
    {
        _prefab = prefab;
        _root = root;
        for (var i = 0; i < preWarm; i++) Return(Create());
    }

    public T Rent()
    {
        var obj = _inactive.Count > 0 ? _inactive.Pop() : Create();
        obj.gameObject.SetActive(true);
        return obj;
    }

    public void Return(T obj)
    {
        obj.gameObject.SetActive(false);
        obj.transform.SetParent(_root, false);
        _inactive.Push(obj);
    }

    private T Create() => Object.Instantiate(_prefab, _root);
}
```

Rules:
- Pre-warm pools during scene load, not mid-gameplay.
- Size to peak concurrency + 20% headroom; log a warning (never throw) when the pool expands at runtime.
- Never call `Instantiate`/`Destroy` inside `Update`, `FixedUpdate`, or any per-frame callback.

Unity 6 built-in alternative: `UnityEngine.Pool.ObjectPool<T>` (same semantics, no custom code needed for simple cases).

---

## GC / allocation avoidance

| Pattern | Bad (allocates) | Good (zero-alloc) |
|---|---|---|
| Per-frame list | `new List<T>()` in Update | `List<T>` field, `Clear()` each frame |
| String formatting | `$"Health: {hp}"` in Update | Cache string or use TextMeshPro's SetText overload |
| LINQ in hot path | `.Where().ToList()` | Manual loop over pre-allocated array |
| Foreach on dictionary | `foreach (var kv in dict)` | `dict.Keys`/`Values` foreach or index loop |
| Boxing | `object o = myStruct` | Generic constraints; `Span<T>` |
| Coroutine yield | `yield return new WaitForSeconds(x)` | Cache `WaitForSeconds`; or use `UniTask` |

`Span<T>` and `stackalloc`: use for short-lived buffers in hot paths (frame processing, deterministic sim step). Does not allocate on the managed heap.

Burst Compiler: annotate performance-critical jobs with `[BurstCompile]` (Unity Jobs system). Burst eliminates managed allocations and vectorizes math automatically. Mandatory for the deterministic simulation layer.

---

## Addressables: memory discipline

- Never load an asset without tracking its `AsyncOperationHandle`; release it with `Addressables.Release(handle)` when the scene/system that owns it unloads.
- Avoid asset churn: releasing then immediately reloading from the same bundle causes a full bundle unload/reload. Track reference counts at the system level.
- Group by lifetime: scene-local assets in their own label group; persistent game-wide assets in a "core" group loaded once at startup.
- Measure: Window -> Asset Management -> Addressables -> Event Viewer shows loads/releases per frame.
- Build: enable "Build Addressables on Player Build" only in CI; locally, update the catalog with "Update a Previous Build" to avoid full rebuilds.

---

## Texture compression + build size

| Platform | Format | Block size | Notes |
|---|---|---|---|
| Android (modern, API 23+) | ASTC 6x6 | 2.67 bpp | Default for most textures |
| Android (characters, UI) | ASTC 4x4 | 6 bpp | Higher quality where it matters |
| Android (legacy, < API 23) | ETC2 | 4–8 bpp | Fallback; set via texture override |
| iOS | ASTC 6x6 | 2.67 bpp | All iOS 9+ devices support ASTC |

Fallback: if the device lacks ASTC, Unity decompresses to uncompressed RGBA32 at load time, doubling memory and CPU load. Set compression override per-platform in the Texture Importer.

Build size discipline:
- Enable "Managed Stripping Level: High" (IL2CPP; test thoroughly -- stripping can remove reflection targets).
- Enable "Strip Engine Code" in Player Settings.
- Use texture atlases; avoid duplicate assets under different names (the Asset Database deduplication check: Window -> Analysis -> Asset Audit).
- Compress audio: MP3/Vorbis for music; ADPCM for short SFX.
- Remove unused shader variants: `Edit -> Project Settings -> Graphics -> Shader Stripping`; audit with the Shader Variant Collection workflow.

---

## Unity Profiler workflow (mobile capture)

### Connect to device

```
# USB cable attached; developer mode + USB debugging on
# Android: forward adb port if using Profiler over USB
adb forward tcp:34999 localabstract:Unity-<your.bundle.id>
# Then in Editor: Window -> Analysis -> Profiler -> set target to the device
```

For iOS: use Xcode Instruments for CPU/GPU simultaneously; Unity Profiler connects over Wi-Fi or USB via the Profiler module.

### Capture checklist

1. Enable modules: CPU Usage, GPU Usage, Memory, Rendering.
2. In CPU Usage module, enable "Record Allocations" (only while hunting GC; it adds overhead).
3. Play on-device for 60+ seconds covering the worst-case gameplay moment (wave peak in the auto-battler; densest obstacle screen in Stairway).
4. Save the capture (`Ctrl+S` / `Cmd+S` in Profiler window) before closing.

### Triage order

1. **Frame time spike** -- CPU Usage hierarchy, sort by "Time ms"; find the deepest hot frame.
2. **GC spikes** -- Memory module "GC Allocated" column; "GC.Alloc" marker in CPU hierarchy; fix per the allocation avoidance table above.
3. **Draw call count** -- Rendering module "Batches" column; Frame Debugger for breakdown.
4. **Texture memory** -- Memory Profiler (separate package: `com.unity.memoryprofiler`): Snapshot -> compare before/after a level load; look for leaked textures whose refcount stays > 0 after scene unload.

### Memory Profiler snapshot

```
# Install: Window -> Package Manager -> Unity Registry -> Memory Profiler
# Capture: Window -> Analysis -> Memory Profiler -> Capture -> Take Snapshot
# Compare two snapshots to find leaks between scenes
```

---

## References

- Unity Manual: Draw Call Batching -- https://docs.unity3d.com/Manual/DrawCallBatching.html
- Unity Manual: SRP Batcher -- https://docs.unity3d.com/Manual/SRPBatcher.html
- Unity Manual: GPU Resident Drawer (URP, Unity 6) -- https://docs.unity3d.com/6000.0/Documentation/Manual/urp/gpu-resident-drawer.html
- Unity Manual: Addressables Memory Management -- https://docs.unity3d.com/Packages/com.unity.addressables@2.4/manual/MemoryManagement.html
- Unity Manual: CPU Profiler -- https://docs.unity3d.com/Manual/ProfilerCPU.html
- Unity Manual: Memory Profiler package -- https://docs.unity3d.com/Packages/com.unity.memoryprofiler@latest
- TheGamedev.Guru: Unity Draw Call Batching Ultimate Guide (2026) -- https://thegamedev.guru/unity-performance/draw-call-optimization/
- Generalist Programmer: Unity Performance Optimization Complete Guide (2025) -- https://generalistprogrammer.com/unity-performance-optimization-complete-technical-guide-2025
