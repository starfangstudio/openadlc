<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
# Unity Architecture Reference

Deep-dive companion to the `unity-architecture` skill. Load on demand; do not duplicate in the skill body.

---

## Assembly Definition (.asmdef) Boundaries

### File location and naming

Follow Unity's recommended layout:

```
Assets/
  <Feature>/
    Runtime/
      <Company>.<Feature>.asmdef          # runtime API + impl (or split; see below)
    Editor/
      <Company>.<Feature>.Editor.asmdef   # editor-only tooling
    Tests/
      Runtime/
        <Company>.<Feature>.Tests.asmdef  # play-mode / NUnit runtime tests
      Editor/
        <Company>.<Feature>.Editor.Tests.asmdef
```

### Critical fields

| Field | Notes |
|---|---|
| `name` | Dot-notation, matches the filename sans extension |
| `references` | Explicit list; use GUID references (`"GUID:..."`) in packages, name references in-project |
| `autoReferenced` | Set `false` for feature assemblies so only declared deps can see them |
| `noEngineReferences` | Set `true` for pure-C# simulation assemblies (no UnityEngine, no UnityEditor) |
| `includePlatforms` | Empty = all platforms. Use `["Editor"]` for editor-only asmdefs |
| `defineConstraints` | Guard optional integrations (e.g., `UNITY_IAP`) |

### Interface vs. implementation split

Mirroring Android's `-api`/`-impl` pattern in Unity:

```
Runtime/
  <Company>.<Feature>.Api.asmdef      # interfaces + data structs; no impl, no engine refs
  <Company>.<Feature>.asmdef          # implementation; references Api assembly
```

Rules:
- The Api assembly may set `noEngineReferences: true` if it is pure-C# (e.g., simulation contracts).
- The impl assembly references the Api assembly; never the reverse.
- Other features depend on the Api assembly only; never on the impl.
- Test assemblies reference whichever layer they exercise; runtime tests reference the impl.

### Dependency direction (one-way rule)

```
Sim.Api  <--  Sim.Impl  <--  Rendering
              ^
              |
         UnitTests (references Sim.Impl)
```

No cycles. Enforce with Unity's Assembly Definition Reference validator (Window > Analysis > Assembly Definition).

---

## ScriptableObject Patterns

### Config / balance data

Use ScriptableObjects for game-wide constants, per-unit balance tables, and level configs. Assets live in `Resources/` or under Addressable groups. Keep them immutable at runtime (treat as read-only after load).

```csharp
[CreateAssetMenu(menuName = "Game/UnitData")]
public class UnitDataSO : ScriptableObject
{
    public int MaxHp;
    public float MoveSpeed;
    // Add [Range] attributes; validated in OnValidate()
}
```

### Runtime Sets

A ScriptableObject that holds a `List<T>` populated at runtime by components registering/deregistering themselves. Avoids singletons while keeping global visibility.

```csharp
[CreateAssetMenu(menuName = "Game/RuntimeSet/Unit")]
public class UnitRuntimeSet : ScriptableObject
{
    public readonly List<UnitView> Items = new();
    public void Add(UnitView v) => Items.Add(v);
    public void Remove(UnitView v) => Items.Remove(v);
}
```

Components call `Add` in `OnEnable`, `Remove` in `OnDisable`.

### Event Channels

ScriptableObject-based events decouple senders from receivers without hard references.

```csharp
[CreateAssetMenu(menuName = "Game/Event/Void")]
public class GameEventSO : ScriptableObject
{
    private readonly List<GameEventListener> _listeners = new();
    public void Raise() { for (int i = _listeners.Count - 1; i >= 0; i--) _listeners[i].OnEventRaised(); }
    public void Register(GameEventListener l) => _listeners.Add(l);
    public void Unregister(GameEventListener l) => _listeners.Remove(l);
}
```

---

## Simulation / Render Separation

### Why

Floating-point non-determinism across platforms breaks lockstep multiplayer and server revalidation. The simulation must produce identical state given identical inputs on any machine.

### Architecture

```
+--------------------------+          +---------------------------+
|  Pure-C# Simulation      |          |  Unity Rendering Layer    |
|  (no UnityEngine ref)    |          |  (MonoBehaviour / UGUI /  |
|                          |          |   UI Toolkit)             |
|  SimWorld                |          |                           |
|  SimTick(input[])        | --view-- |  GameView                 |
|  SimState (snapshot)     |  events  |  reads SimState read-only |
+--------------------------+          +---------------------------+
         |
         v
  Server / replay runner
  (references Sim.Api + Sim.Impl only; zero Unity dependency)
```

Key rules:
- Simulation uses **fixed-point math** (e.g., `FixedMath.Net`, `LibFixedPoint`, or a hand-rolled `FP` struct). Never `float`/`double` for position, velocity, HP, or RNG.
- No `UnityEngine` namespace inside the simulation assembly. Enforce with `"noEngineReferences": true` in the asmdef.
- State is a pure data snapshot (`SimState` struct/record). The render layer reads it each frame; it never writes back.
- Inputs are value types collected by the render layer and passed into `SimTick(FixedInput[] inputs)`. No references to MonoBehaviours cross the boundary.
- Server re-runs the simulation from a snapshot + input log to validate outcomes.

### Fixed-point RNG

Use a seeded deterministic RNG: the project's `SimRng` (a seeded xorshift64 or PCG) replayed from the input log. Never `System.Random`, `Unity.Mathematics.Random`, or `UnityEngine.Random` inside the sim; they are not cross-platform deterministic (see `deterministic-sim.md`).

### Unit test entry point

Because the sim is pure C#, NUnit tests run in the Unity Test Framework's **Edit Mode** (no scene required) or even outside Unity entirely (via `dotnet test` targeting the sim assembly).

---

## Composition over MonoBehaviour Inheritance

Avoid deep MonoBehaviour hierarchies. Prefer:

1. **Component composition**: small, focused MonoBehaviours each owning one concern (movement, health display, input relay).
2. **ScriptableObject strategy objects**: behaviour variants (e.g., attack patterns) are SOs injected into components; swap at runtime or in the Inspector.
3. **Interface injection via SerializeField**: reference an interface field backed by a MonoBehaviour implementing it.

Anti-pattern: a `BaseUnit` -> `BaseMeleeUnit` -> `TowerUnit` hierarchy where every override adds complexity. Instead, `UnitView` holds references to `IMovement`, `IAttack`, `IHealthDisplay` components.

---

## References

- Unity Manual: Assembly Definition Files -- https://docs.unity3d.com/6000.2/Documentation/Manual/cus-asmdef.html
- Unity How-To: Architect your code with ScriptableObjects -- https://unity.com/how-to/architect-game-code-scriptable-objects
- Unity How-To: ScriptableObject-based Runtime Sets -- https://unity.com/how-to/scriptableobject-based-runtime-set
- Unity How-To: Separate Game Data and Logic with ScriptableObjects -- https://unity.com/how-to/separate-game-data-logic-scriptable-objects
- Deterministic Lockstep Networking Demystified -- https://zacksinisi.com/deterministic-lockstep-networking-demystified/
- Unity Assembly Definitions: Faster Iteration and Better Architecture -- https://silviocarrera.medium.com/unity-assembly-definitions-faster-iteration-and-better-architecture-4c9474fbdc54
