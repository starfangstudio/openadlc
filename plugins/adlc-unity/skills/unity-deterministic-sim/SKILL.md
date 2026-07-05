---
name: unity-deterministic-sim
description: >-
  This skill should be used when the user asks to "make the simulation deterministic",
  "add lockstep networking", "implement PvP with real opponents", "build a deterministic
  tick sim", "wire up replay recording", "make replays work as bots", "prevent desync
  between clients", "add server-side anti-cheat via replay revalidation", "implement
  simultaneous-resolution for auto-battler waves", "golden-replay test the sim", or
  "ban floats from the game logic path". Designs and implements a pure-C# fixed-tick
  deterministic simulation layer for real-time PvP: lockstep input exchange, fixed-point
  math, seeded RNG, zero Unity-float game logic, integer state, and a golden-replay
  test that proves identical output from identical inputs across runs and platforms.
version: 0.1.0
---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# Unity deterministic sim

Build a pure-C# tick-based simulation that produces bit-identical output from identical
inputs on every run and every platform. This is the foundation for: real human PvP via
lockstep, server-revalidatable anti-cheat, and replay-as-bot for empty lobbies.

## Step 1: Detect any existing sim or netcode

Never scaffold over something that already exists. Inspect first:

```bash
# Assembly definitions and sim-scoped code
find . -name "*.asmdef" | xargs grep -l -i "sim\|netcode\|lockstep\|network" 2>/dev/null | head
# Existing fixed-point or lockstep libs
find . -name "*.cs" | xargs grep -l "FixedMath\|FixedPoint\|Lockstep\|ISimTick" 2>/dev/null | head
# Any Unity Netcode / Mirror / Photon references
grep -rEln "Unity\.Netcode|Mirror|Photon|MLAPI|com\.unity\.netcode" --include=*.cs --include=*.json . | head
```

Record what is found. If a sim layer, fixed-point lib, or multiplayer solution already
exists, extend it; do not replace. Mark anything uncertain `unknown` and ask before
proceeding.

## Step 2: Understand why determinism is mandatory here

Explain this to the team (include in any design doc you produce):

- **Lockstep PvP:** both clients run the same sim from the same inputs and seed. No
  world-state sync is sent; only compact input packets cross the wire. If output
  diverges by a single bit, clients desync.
- **Server revalidation / anti-cheat:** the server re-runs the sim from the recorded
  input log after each match. Any client reporting a different outcome is flagged. This
  only works if the server's sim output equals the clients'.
- **Replay-as-bot:** the replay IS the bot; feed the input log back into the sim and
  it plays like a human. Empty-lobby problem solved with zero extra AI code.

## Step 3: Establish the sim boundary

Create a dedicated C# assembly (`Sim.asmdef`) with zero Unity engine references in
the sim path. Enforce with an `AssemblyDefinition` that does NOT reference
`UnityEngine` in its `references` array.

For the directory layout and the full list of hard boundary rules (no floats, no
`Dictionary` iteration, no async), see
[references/unity-deterministic-sim-detail.md](../../references/unity-deterministic-sim-detail.md).

## Step 4: Fixed-point math

Add a fixed-point library. Check existing packages first. Wrap the chosen lib in a
thin `FP` struct; the rest of the sim imports only `FP`, never the underlying type.
Never use `System.Math` or `Mathf` inside the sim boundary for transcendental functions.

For the library comparison table and the transcendental-function requirement, see
[references/unity-deterministic-sim-detail.md](../../references/unity-deterministic-sim-detail.md).

## Step 5: Deterministic seeded RNG

Add `SimRng` (pure C# xorshift64 or PCG). Seed from the server-issued match seed
(`ulong`). Advance the RNG in strict tick order; never call it from rendering. Never
use `System.Random`, `UnityEngine.Random`, or `Unity.Mathematics.Random` inside the
sim boundary.

For the `SimRng` struct shape, see
[references/unity-deterministic-sim-detail.md](../../references/unity-deterministic-sim-detail.md).

## Step 6: Sim API contract

Expose one entry point (`SimWorld.Tick(TickInputs)`) returning a `TickResult` that
includes a `StateHash` and a `SimEvent[]`. Compute `StateHash` via deterministic byte
serialization (no `GetHashCode()`). A per-tick hash log lets you pinpoint the first
divergence tick when clients report different final states.

For the full struct and class signatures, see
[references/unity-deterministic-sim-detail.md](../../references/unity-deterministic-sim-detail.md).

## Step 7: Lockstep driver shape

`SimDriver` (Presentation layer) implements the basic lockstep loop:

1. Send local player input for tick T to the relay server / other clients.
2. Wait until inputs for tick T from all players have arrived.
3. Call `sim.Tick(inputs)`.
4. Compare `StateHash` with the remote player's reported hash (if running cross-check).
5. Apply `Events` to the presentation layer (animations, SFX, UI).
6. Advance to tick T+1.

Input delay (half median RTT, typically 1-3 frames at 20 Hz) is configured at session
start. For a wave-resolution auto-battler the delay is invisible: players act between
waves, not in reaction to real-time movement.

## Step 8: Replay recording

Record the input log as a `List<TickInputs>` during the match. Serialize to JSON or
a compact binary format at match end. The input log + seed fully reproduce the match.

Use the same log to feed a bot opponent, validate outcome server-side, and provide
spectate/replay.

## Step 9: Verify with the golden-replay test (pass/fail required)

STOP: Do not mark this skill complete without a green test.

Run two NUnit Edit Mode tests: one that proves two runs from the same seed produce
identical hashes, and one that locks the hash against a committed golden file. Extend
CI to run on an ARM device or Android emulator.

For the full test code and the post-change validator loop, see
[references/unity-deterministic-sim-detail.md](../../references/unity-deterministic-sim-detail.md).

## What this skill does NOT cover

- **Design token / UI Toolkit wiring** -- defer to `adlc-design`.
- **Economy / F2P meta balance** -- defer to the `adlc-monetization` pack.
- **Store builds / signing** -- out of scope here.
- **Rollback netcode** -- lockstep is correct for this game type. See the reference
  file for the lockstep vs rollback tradeoff if the decision is revisited.

## Outbound checkpoint

Local work needs no approval. Outbound here (pushing to remote, opening a PR, posting match logs to a server, or publishing a build): stop, present exactly what would go out, and ask the operator for an explicit "yes" first.

## References

- [references/unity-deterministic-sim-detail.md](../../references/unity-deterministic-sim-detail.md) -- layout, boundary rules, FP library table, SimRng shape, API contract, test code, validator loop, lockstep vs rollback.
- [references/deterministic-sim.md](../../references/deterministic-sim.md) -- cross-platform caveats table.
- Zack Sinisi, "Deterministic Lockstep Networking Demystified": https://zacksinisi.com/deterministic-lockstep-networking-demystified/
- Unity Discussions, "State of Determinism in Unity": https://discussions.unity.com/t/state-of-determinism-in-unity/867770
- FixedMath.Net: https://github.com/asik/FixedMath.Net
- Unity.Mathematics.FixedPoint: https://github.com/danielmansson/Unity.Mathematics.FixedPoint
- UnityLockstep: https://github.com/proepkes/UnityLockstep
- YAL, "Preparing your game for deterministic netcode": https://yal.cc/preparing-your-game-for-deterministic-netcode/
