<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
Consumed by the `unity-performance` skill. Load on demand; do not load independently.

## Device detection commands

```bash
# In Editor: Edit -> Project Settings -> Player -> Other Settings
# Check: Target minimum API level (Android), Minimum iOS version
# Check: Graphics APIs list (Vulkan/OpenGL ES 3.x for Android; Metal for iOS)

# Check current frame rate cap
grep -r "targetFrameRate\|vSyncCount" Assets/ --include="*.cs" | head
# Locate URP Asset files
find . -name "*.asset" -path "*/URP*" | head
```

## Frame budget tables

| Target FPS | Budget per frame | Typical low-end headroom target |
|---|---|---|
| 30 fps | 33 ms | <= 25 ms game logic + 8 ms GPU |
| 60 fps | 16.6 ms | <= 12 ms game logic + 4 ms GPU |

Draw call budgets by device tier:

| Tier | Draw calls (opaque) |
|---|---|
| Low-end (Adreno 506, Mali-G52) | <= 100 |
| Mid (Adreno 619, Mali-G77) | <= 200 |
| High (Adreno 730+) | <= 400 |

## Batching decision tree

```
Has identical meshes that move? -> GPU Instancing (+ MaterialPropertyBlock)
Non-moving world geometry? -> Static Batching (disable if GPU Resident Drawer is on)
Everything else in URP? -> SRP Batcher (enabled by default; reduce shader keyword combos)
UI/Sprites that share draw calls? -> Sprite Atlas
Using GPU Resident Drawer (Unity 6 URP)? -> disable Static Batching on the URP Asset; the two conflict
```

**SRP Batcher detail:**
- URP Asset -> Advanced -> SRP Batcher: must be enabled.
- Batches by shader variant, not by material. Reduce shader keyword combinations.
- Verify: Frame Debugger (Window -> Analysis -> Frame Debugger); count "SRP Batch" events; Render Stats overlay shows "Batches" dropping.

**GPU Instancing detail:**
- Enable "Enable GPU Instancing" on the material.
- Pass per-instance data via `MaterialPropertyBlock`; never set properties directly on the material instance (breaks instancing and allocates).
- Verify: Frame Debugger shows "Draw Mesh (instanced)" entries.

**Static Batching detail:**
- Mark the GameObject Static in the Inspector.
- Confirm in Player Settings: "Static Batching" checkbox is on.
- Unity 6 with GPU Resident Drawer: disable static batching on the URP Asset.

**Texture atlasing:** combine sprites/UI elements that appear together into atlas sheets (Sprite Atlas asset). Reduces material switches between draw calls.

## Object pool pattern

Unity 6 built-in pool (simple cases):

```csharp
using UnityEngine.Pool;

public class BulletSpawner : MonoBehaviour
{
    private ObjectPool<Bullet> _pool;

    void Awake()
    {
        _pool = new ObjectPool<Bullet>(
            createFunc: () => Instantiate(bulletPrefab),
            actionOnGet: b => b.gameObject.SetActive(true),
            actionOnRelease: b => b.gameObject.SetActive(false),
            actionOnDestroy: b => Destroy(b.gameObject),
            collectionCheck: false,
            defaultCapacity: 32,
            maxSize: 128
        );
    }

    public Bullet Rent() => _pool.Get();
    public void Return(Bullet b) => _pool.Release(b);
}
```

Pool sizing and lifecycle rules:
- Pre-warm during scene load, not mid-gameplay.
- Size to peak concurrency + 20% headroom.
- Log a warning (never throw) when a pool expands at runtime; treat it as a sizing bug.
- Returning to pool: `SetActive(false)` + `SetParent(poolRoot)`. Renting: `SetActive(true)`.

## GC allocation pattern table

| Pattern | Problem | Fix |
|---|---|---|
| `new List<T>()` in Update | Heap alloc every frame | Pre-allocate field; call `Clear()` |
| `new WaitForSeconds(n)` in coroutine | Alloc on each yield | Cache instance as a field |
| String interpolation in hot path | Boxed args + string alloc | `TextMeshPro.SetText(fmt, arg)` overloads |
| LINQ in Update/FixedUpdate | Iterator allocation | Manual loop over pre-allocated array |
| Short-lived frame buffers | Heap pressure | `Span<T>` / `stackalloc` |
| Lockstep sim step | Managed alloc + no vectorization | `[BurstCompile]` on job struct |

## Profiler and Memory Profiler workflow

**Connect to device (Android over USB):**
```bash
adb forward tcp:34999 localabstract:Unity-<your.bundle.id>
# Then: Window -> Analysis -> Profiler -> target the device
```

**Connect to device (iOS):** use Xcode Instruments -> Allocations, or connect via the Profiler window with the device selected over USB (no adb step needed; Unity handles the connection).

**Capture triage order:**
1. Frame time spike: CPU Usage -> Hierarchy, sort "Time ms"; find the deepest hot frame.
2. GC spikes: enable "Record Allocations" in the CPU module; check "GC Alloc" column and the `GC.Alloc` marker callstack.
3. Draw calls: Rendering module "Batches" column; Frame Debugger for per-draw breakdown.
4. Texture memory: Memory Profiler package (`com.unity.memoryprofiler`) -> take two snapshots (before and after scene load) -> compare; leaked textures show refcount > 0.

Save the capture before closing the Profiler window.

**Snapshot comparison procedure:**
- Window -> Memory Profiler -> Snapshots.
- Take snapshot A (baseline), perform the operation (scene transition, gameplay loop), take snapshot B.
- Click "Compare Snapshots A vs B"; filter by "Not in A" to find new allocations that did not release.

## Texture compression settings

| Platform | Format | Use case |
|---|---|---|
| Android API 23+ | ASTC 6x6 | Most textures |
| Android API 23+ | ASTC 4x4 | Characters, UI (higher quality) |
| iOS (9+) | ASTC 6x6 | All textures |
| Legacy Android fallback | ETC2 | Set per-platform override in Texture Importer; without ASTC the device decompresses to RGBA32 at runtime, doubling memory |

## Build stripping steps

1. Player Settings -> Managed Stripping Level: High (IL2CPP). Test after enabling; stripping can remove reflection targets. Add `link.xml` preserves for anything stripped incorrectly.
2. Player Settings -> Strip Engine Code: on.
3. Edit -> Project Settings -> Graphics -> Shader Stripping: remove unused passes and variants. Audit with a Shader Variant Collection.
4. Audio: music = Vorbis; short SFX = ADPCM.

## Pass/fail criteria (lowest supported device)

```
1. Profiler capture: worst-case frame time <= budget (33 ms at 30 fps / 16.6 ms at 60 fps)
2. GC Alloc column: zero per-frame allocations in the game loop hot path
3. Draw calls: within budget for the device tier (see draw call budget table above)
4. Memory Profiler: no leaked objects between scene transitions
5. Build size: within the operator's target (OTA update delta matters for F2P)
```

Do not report a fix as done based on code review alone; always run the profiler check.
