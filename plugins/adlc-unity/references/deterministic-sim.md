<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
# Deterministic Simulation Reference

Deep-dive companion to the `unity-deterministic-sim` skill. Contains the detail that would bloat the main SKILL.md body.

---

## Why floats break cross-platform determinism

IEEE 754 basic arithmetic (+, -, *, /) is reproducible on modern consumer hardware when the FPU mode is consistent. The problems come from:

- **Transcendentals (sin, cos, sqrt, pow, atan2):** .NET `System.Math` trig functions produce different bit-patterns on different platforms. Wrap in Burst or replace with a software implementation.
- **`float` vs `double` promotion:** JIT compilers may silently promote 32-bit intermediates to 80-bit or 64-bit registers. IL2CPP removes most of this risk vs Mono.
- **Compiler auto-vectorization / FMA:** fused-multiply-add changes rounding. Burst exposes `[BurstCompile(FloatMode = FloatMode.Strict)]` to disable FMA.
- **Dictionary / HashSet iteration order:** `GetHashCode` for reference types is not deterministic across runs in .NET. Never iterate a `Dictionary` in sim logic; use `List` or `SortedList` keyed on a deterministic integer.
- **`Mathf` and `Physics`:** Unity's `Mathf` wraps `System.Math`; Unity PhysX is non-deterministic across platforms and tick rates. Neither is allowed in the sim path.

**Recommended compile target:** IL2CPP on both iOS and Android. Unity's documentation and community testing consistently show better determinism than Mono because Unity controls the full codegen pipeline.

---

## Fixed-point math

Fixed-point arithmetic stores a scaled integer and does all math in integer ops, side-stepping the float hardware entirely.

### Representation

A Q16.16 value (32-bit) stores `value * 65536` as a signed int32. A Q32.32 (64-bit) stores `value * 2^32` as a signed int64. 64-bit is strongly preferred for game simulation (more precision, fewer overflow surprises in multiply paths).

```
FP64 x = FP64.FromInt(5);       // 5.0
FP64 y = FP64.FromRaw(327680);  // 5.0 via raw bits (Q16.16)
FP64 z = x * y;                 // integer multiply, then >> 32
```

### Libraries

| Library | Notes |
|---|---|
| `FixedMath.Net` | Q31.32, MIT, battle-tested; basis of many Unity lockstep projects |
| `Unity.Mathematics.FixedPoint` (danielmansson) | Q32.32 extension of `Unity.Mathematics`; idiomatic with Burst |
| `libfixmath` | C, Q16.16, smallest; good reference for understanding the ops |

Pick one and wrap it in a thin `FP` / `FPVector2` / `FPVector3` API so the rest of the sim never touches the underlying type.

### Transcendentals in fixed-point

Use lookup-table or polynomial approximation implementations that ship with the chosen library. Never delegate to `Mathf`, `Math`, or `System.Math` inside the sim boundary.

---

## Deterministic seeded RNG

The standard `System.Random` is not cross-platform deterministic. `Unity.Mathematics.Random` (xorshift) is seeded and deterministic when all parameters are the same, but verify the version you ship.

Preferred: **xorshift64** or **PCG** implemented in pure C#, seeded from the match seed. Example contract:

```csharp
public struct SimRng
{
    ulong _state;
    public SimRng(ulong seed) { _state = seed == 0 ? 1u : seed; }
    public uint NextUInt() { /* xorshift64 bit ops */ }
    public FP NextFP01() => FP.FromRaw((long)(NextUInt() >> 1));
}
```

Key rules:
- Advance the RNG exactly once per logical usage in tick order.
- Never call the RNG from rendering or async paths.
- Seed = match ID hash or server-provided uint64; both peers start with the same value.

---

## Lockstep vs rollback

### Lockstep (input delay model)

Each tick advances only when all players' inputs for that tick have arrived. Input is intentionally delayed (half median RTT). Simple to implement and replay-perfect.

**Tradeoffs:**
- Any player with poor/unstable connection stalls everyone.
- Scales well to many units (only inputs sent, not world state).
- Well-suited for turn-resolution games (Legion-TD style): the simultaneous-resolution model already implies a natural tick boundary, so input delay is invisible to the player.

**Use when:** game has a natural tick boundary, small player count (2-4), unit counts are high, and you want server revalidation for free.

### Rollback (predictive model)

Predict remote inputs, advance simulation, then rewind and replay when corrections arrive. Hides latency at the cost of complexity: save-states must be fast and complete.

**Tradeoffs:**
- Smoother under packet loss, but implementation complexity is much higher.
- Every simulated object must be serializable into a compact snapshot.
- GGPO is the reference implementation; Unity ports: `Backroll`, `BestoNet`.
- Rewinding Unity GameObject transforms is non-trivial; pure ECS state is much cleaner.

**Use when:** tight input-response loop is critical (fighting games) and you can afford snapshot complexity.

**For Legion-TD:** lockstep is the correct choice. Simultaneous resolution means players only submit deployment orders and ability inputs per wave. Input delay of 1-2 frames is invisible because the action happens at wave start, not in reaction to real-time movement.

---

## Server revalidation shape

Server runs the authoritative sim from recorded inputs:

```
Client A ──inputs[tick]──► Relay server ──broadcast──► Client B
                                │
                           record inputs
                           (optional: run sim, compare hash)
```

- **Light validation:** server records inputs and final-state hashes per tick from each client; flags divergences.
- **Full revalidation:** server runs the sim headlessly from the input log after match completion; compares final state checksum to reported outcomes.
- **Replay-as-bot:** the same input log drives an AI opponent when a human disconnects or for empty-lobby matchmaking. Works only because the sim is fully reproducible from inputs + seed.

The sim layer must expose: `Tick(inputs)` → `TickResult` (new state hash, events). No Unity lifecycle calls inside that method.

---

## Golden-replay test pattern

```csharp
[Test]
public void GoldenReplay_SameSeed_ProducesIdenticalHash()
{
    var inputs = GoldenFixture.LoadInputLog("legion_td_match_001.json");
    ulong seed = 0xDEADBEEF_CAFEF00D;

    var stateA = SimRunner.RunToEnd(inputs, seed);
    var stateB = SimRunner.RunToEnd(inputs, seed);

    Assert.AreEqual(stateA.FinalHash, stateB.FinalHash);
}

[Test]
public void GoldenReplay_Hash_MatchesGoldenFile()
{
    // Catches regressions: if sim logic changes the hash changes.
    var expected = GoldenFixture.LoadExpectedHash("legion_td_match_001");
    var actual   = SimRunner.RunToEnd(...);
    Assert.AreEqual(expected, actual.FinalHash,
        "Sim logic changed; update the golden file intentionally.");
}
```

Hash the full world state after each tick (not just final): use `xxHash` or `FNV-1a` over a deterministic byte serialization of all sim-owned state. Check the per-tick hash log to pinpoint the first divergence tick when a mismatch occurs.

**Cross-platform gate:** run the golden-replay test as part of CI on both an x64 host and an ARM device (or Android emulator). A mismatch there is a determinism bug, not a test bug.

---

## Cross-platform determinism caveats (summary)

| Source of nondeterminism | Mitigation |
|---|---|
| `System.Math` trig | Replace with fixed-point or Burst-compiled soft-float |
| `Mathf` functions | Banned from sim path; use fixed-point equivalents |
| Unity `Physics` / PhysX | Banned from sim path; use custom fixed-point collision |
| `Dictionary` iteration | Use `List<(key,val)>` sorted by deterministic key |
| `float` intermediates in Burst | `FloatMode.Strict`, no FMA |
| `Time.deltaTime` in logic | Fixed tick rate only; `Time.deltaTime` is presentation-only |
| `System.Random` | Replace with seeded `SimRng` |
| Mono vs IL2CPP | Ship IL2CPP on both platforms |
| Thread scheduling | All sim logic on the main thread or a single dedicated sim thread; never async |

---

## References

- Zack Sinisi, "Deterministic Lockstep Networking Demystified": https://zacksinisi.com/deterministic-lockstep-networking-demystified/
- Unity Discussions, "State of Determinism in Unity": https://discussions.unity.com/t/state-of-determinism-in-unity/867770
- danielmansson, Unity.Mathematics.FixedPoint: https://github.com/danielmansson/Unity.Mathematics.FixedPoint
- FixedMath.Net (fixed-point Q31.32 library): https://github.com/asik/FixedMath.Net
- proepkes, UnityLockstep (reference lockstep project): https://github.com/proepkes/UnityLockstep
- Kimbatt, unity-deterministic-physics (DOTS + soft floats): https://github.com/Kimbatt/unity-deterministic-physics
- Backroll (GGPO rollback port for Unity): https://github.com/HouraiTeahouse/Backroll
- YAL, "Preparing your game for deterministic netcode": https://yal.cc/preparing-your-game-for-deterministic-netcode/
- Understanding Determinism Part 1: Intro and Floating Points: https://shaderfun.com/2020/10/25/understanding-determinism-part-1-intro-and-floating-points/
