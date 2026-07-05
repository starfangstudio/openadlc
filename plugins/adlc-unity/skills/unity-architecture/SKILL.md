---
name: unity-architecture
description: >-
  Structures a Unity project for testability and modularity via assembly definition boundaries,
  a pure-C# simulation core decoupled from the rendering layer, and ScriptableObject-driven
  config. Use when the user asks to "set up assembly definitions", "make the simulation
  testable", "decouple the sim from MonoBehaviours", "replace a singleton with a
  ScriptableObject", or "use composition instead of inheritance in Unity".
version: 0.1.0
---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# unity-architecture

Structure a Unity project for testability and modularity: assembly definition boundaries,
ScriptableObject-driven config, composition over inheritance, and a pure-C# simulation core
decoupled from the Unity rendering layer so it is testable and server-runnable.

## Step 1: Detect first -- never impose

Before changing anything, inspect the project. For detection commands, see
[references/unity-architecture-detail.md](../../references/unity-architecture-detail.md) (Step 1: Detection commands).

Record: existing asmdef names and dependency graph, whether DOTS is present, whether a
sim/render split already exists. Mark anything unclear `unknown`; ask before restructuring.

If DOTS is already in use, defer to DOTS-specific conventions -- this skill covers the
MonoBehaviour-composition path.

## Step 2: Establish assembly definition boundaries

Each domain-level feature gets its own asmdef. For full layout examples, see
[references/unity-architecture-detail.md](../../references/unity-architecture-detail.md) (Step 2: Assembly definition layouts).

Rules:
- Dependency direction is one-way: Impl references Api; never the reverse.
- Other features reference the Api assembly only; never the Impl.
- Set `"autoReferenced": false` on feature asmdefs. Only declared references can see them.
- For the simulation assembly: set `"noEngineReferences": true` (no UnityEngine namespace).

Verify boundaries compile cleanly (Step 5).

## Step 3: Simulation / render separation

If the project is a real-time game with multiplayer or replay requirements, establish the
sim/render split. For the full architecture breakdown and fixed-point RNG rules, see
[references/unity-architecture-detail.md](../../references/unity-architecture-detail.md) (Step 3: Simulation / render separation detail).

Three assembly roles: Simulation (`noEngineReferences: true`, pure C#, fixed-point state,
single `Tick` entry point), Rendering (reads `SimState` each frame, no writes back), and
Server/test runner (references Sim.Api + Sim.Impl only, zero Unity dependency).

Do not introduce this split if the project is single-player only and replay is not needed.
Ask the operator.

## Step 4: ScriptableObject-driven config

Replace hardcoded constants and singleton data stores with ScriptableObjects (config SOs,
runtime sets, event channels). For pattern descriptions and copy-ready code, see
[references/unity-architecture-detail.md](../../references/unity-architecture-detail.md) (Step 4: ScriptableObject patterns)
and [references/unity-architecture.md](../../references/unity-architecture.md) (ScriptableObject Patterns).

## Step 5: Composition over deep MonoBehaviour inheritance

If the project has multi-level MonoBehaviour hierarchies, extract concerns into focused
components composed via `[SerializeField]` interfaces; strategy variants become injected
ScriptableObjects. For the full refactoring checklist, see
[references/unity-architecture-detail.md](../../references/unity-architecture-detail.md) (Step 5: Composition over deep MonoBehaviour inheritance).

Do not refactor working inheritance hierarchies without the operator's explicit request.

## Step 6: Verify (pass/fail, not "looks right")

For the full set of verify commands (compile check, test runner, assembly graph), see
[references/unity-architecture-detail.md](../../references/unity-architecture-detail.md) (Step 6: Verify commands).

A clean compile with no assembly reference errors, plus green unit tests on the sim
assembly, is the required proof. Do not mark done without both.

## Outbound checkpoint

Local work needs no approval. Anything outbound (publish, push, post) needs the operator's explicit per-action "yes" first; see the global consent law.

## References

- [references/unity-architecture-detail.md](../../references/unity-architecture-detail.md) -- detection commands,
  asmdef layout examples, sim/render separation detail, ScriptableObject patterns,
  composition checklist, verify commands.
- [references/unity-architecture.md](../../references/unity-architecture.md) -- asmdef boundaries,
  ScriptableObject patterns (config / runtime sets / event channels), sim/render separation
  architecture, composition patterns.
- Unity Manual: Assembly Definition Files --
  https://docs.unity3d.com/6000.2/Documentation/Manual/cus-asmdef.html
- Unity How-To: Architect your code with ScriptableObjects --
  https://unity.com/how-to/architect-game-code-scriptable-objects
- Unity How-To: ScriptableObject-based Runtime Sets --
  https://unity.com/how-to/scriptableobject-based-runtime-set
- Deterministic Lockstep Networking Demystified --
  https://zacksinisi.com/deterministic-lockstep-networking-demystified/
