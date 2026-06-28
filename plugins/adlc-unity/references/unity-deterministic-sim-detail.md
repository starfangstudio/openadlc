<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
Consumed by the `unity-deterministic-sim` skill. Load on demand; do not load independently.

## Directory layout and assembly boundary

```
Assets/
  Sim/
    Sim.asmdef          # no UnityEngine reference
    SimWorld.cs         # the world state (integer/FP fields only)
    SimTick.cs          # Tick(inputs) -> TickResult
    SimRng.cs           # seeded xorshift RNG
    FP.cs               # thin wrapper over chosen fixed-point lib
  Presentation/
    SimDriver.cs        # MonoBehaviour: drives Tick(), renders state
```

Hard rules for every `.cs` file inside `Sim/`:

- No `using UnityEngine;` import.
- No `float` or `double` fields on sim-owned state; use `FP` (fixed-point) or `int`/`long`.
- No `Mathf`, `Physics`, `Physics2D`, `Time.deltaTime`, `Time.time`.
- No `Dictionary<K,V>` iterated in undefined order; use `List` sorted by a deterministic integer key.
- No `async`/`await`, no `Task`, no `Thread`; all sim logic runs on one thread.

`SimDriver` lives in `Presentation/` and is the only place allowed to call `Time.deltaTime`. It accumulates real time, then calls `sim.Tick(inputs)` N times per frame at the fixed tick rate (e.g., 20 Hz for an auto-battler wave resolution loop).

## Fixed-point library options

| Library | Format | Where |
|---|---|---|
| `FixedMath.Net` | Q31.32 (64-bit) | https://github.com/asik/FixedMath.Net |
| `Unity.Mathematics.FixedPoint` | Q32.32 (64-bit) | https://github.com/danielmansson/Unity.Mathematics.FixedPoint |

Check existing packages first. Wrap the chosen lib in a thin `FP` struct and `FPVector2`/`FPVector3` if needed. The rest of the sim imports only `FP`, never the underlying library type.

Transcendental functions (`Sin`, `Cos`, `Sqrt`, `Atan2`): use lookup tables or the fixed-point lib's own implementations. Never delegate to `System.Math` or `Mathf` inside the sim boundary; those are IEEE 754 and not guaranteed bit-identical across platforms.

## SimRng struct shape

```csharp
// Minimal shape -- implement bit ops in the struct body
public struct SimRng
{
    ulong _state;
    public SimRng(ulong seed) { _state = seed == 0 ? 1UL : seed; }
    public uint  NextUInt();      // xorshift64
    public int   NextIntRange(int min, int max);
    public FP    NextFP01();      // maps to [0,1) in fixed-point
}
```

Never use `System.Random`, `UnityEngine.Random`, or `Unity.Mathematics.Random` inside the sim boundary.

## Sim API contract

```csharp
// All inputs for one tick from all players
public struct TickInputs
{
    public PlayerInput[] Inputs;  // indexed by player slot
    public int Tick;
}

// What the sim returns after each tick
public struct TickResult
{
    public ulong StateHash;       // xxHash / FNV-1a over full world state
    public SimEvent[] Events;     // damage dealt, unit deaths, wave result, etc.
}

public class SimWorld
{
    public TickResult Tick(TickInputs inputs) { ... }
    public byte[] Serialize();                  // for golden-replay and snapshots
    public static SimWorld Deserialize(byte[]); // for rollback (future)
}
```

`StateHash` must cover every sim-owned field. Compute it via deterministic byte serialization (no `GetHashCode()`). A per-tick hash log lets you pinpoint the first divergence tick when clients report different final states.

## Golden-replay tests (NUnit, Edit Mode)

```csharp
[Test]
public void GoldenReplay_SameSeed_IdentialHash()
{
    var inputs = GoldenFixture.Load("match_001.json");
    ulong seed = 0xDEADBEEF_CAFEF00Dul;
    var a = SimRunner.RunToEnd(inputs, seed);
    var b = SimRunner.RunToEnd(inputs, seed);
    Assert.AreEqual(a.FinalHash, b.FinalHash);
}

[Test]
public void GoldenReplay_Hash_MatchesLockedGolden()
{
    // Update the golden file intentionally when sim logic changes.
    var expected = GoldenFixture.LoadHash("match_001.golden");
    var actual   = SimRunner.RunToEnd(GoldenFixture.Load("match_001.json"),
                                      0xDEADBEEF_CAFEF00Dul);
    Assert.AreEqual(expected, actual.FinalHash,
        "Sim output changed. If intentional, regenerate the golden file.");
}
```

Run with Unity Test Framework (Edit Mode tests, no MonoBehaviour required). Extend the CI pipeline to run these tests on an ARM device or Android emulator to catch cross-platform divergence early.

## Validator loop (post-change checklist)

1. Run `GoldenReplay_SameSeed_IdentialHash` -- must be green.
2. Run `GoldenReplay_Hash_MatchesLockedGolden` -- green = no regression; red = intentional change (update golden) or bug (fix sim).
3. If adding a new feature: add a focused `[Test]` for that mechanic using `SimRunner` directly, no MonoBehaviour.
4. If hash mismatch appears across platforms: audit for `Dictionary` iteration order, `System.Math` trig, or float intermediates crossing the sim boundary.

## Lockstep vs rollback

Lockstep is correct for wave-resolution auto-battlers: players act between waves, not in real-time reaction, so 1-3 tick input delay is invisible. Rollback netcode (GGPO-style) is a larger investment appropriate when sub-frame reaction matters (fighting games, fast-paced shooters). Revisit this decision only if the game type changes.
