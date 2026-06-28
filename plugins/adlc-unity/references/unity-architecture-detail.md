<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
Consumed by the `unity-architecture` skill. Load on demand; do not load independently.

## Step 1: Detection commands

Run these via the Unity MCP or Bash before changing anything:

```bash
# Existing asmdef files and their locations
find . -name "*.asmdef" | sort

# Whether DOTS/ECS packages are present (do NOT use ECS if not already there)
grep -r "com.unity.entities\|com.unity.physics" Packages/manifest.json 2>/dev/null

# Existing ScriptableObject usage
grep -rl "ScriptableObject" Assets --include="*.cs" | head -10

# MonoBehaviour inheritance depth (look for base classes)
grep -rn "class.*:.*MonoBehaviour" Assets --include="*.cs" | head -20

# Fixed-point math or deterministic sim signals
grep -rn "noEngineReferences\|FixedPoint\|FP\." Assets --include="*.cs" | head -10
```

Record: existing asmdef names and dependency graph, whether DOTS is present, whether a
sim/render split already exists. Mark anything unclear `unknown`; ask before restructuring.

## Step 2: Assembly definition layouts

Minimum layout for a feature that needs testability:

```
Assets/<Feature>/
  Runtime/
    <Company>.<Feature>.asmdef        # runtime code
  Tests/
    Runtime/
      <Company>.<Feature>.Tests.asmdef
```

For features other assemblies must depend on, split into Api + Impl:

```
Assets/<Feature>/
  Runtime/
    <Company>.<Feature>.Api.asmdef    # interfaces + data structs; autoReferenced: false
    <Company>.<Feature>.asmdef        # implementation; references Api; autoReferenced: false
```

## Step 3: Simulation / render separation detail

**Simulation assembly** (`noEngineReferences: true`):
- Pure C# structs and classes only.
- All numeric state uses fixed-point (`FP` type), never `float`/`double`.
- Exposes a single tick entry point: `SimWorld.Tick(FixedInput[] inputs)`.
- State is a plain-data snapshot struct; nothing holds a MonoBehaviour reference.

**Rendering assembly** (references Sim.Api, no writes back):
- MonoBehaviours read `SimState` each frame and drive visual components.
- Collects player input; hands it to the sim as a value type; never passes `this`.

**Server / test runner**:
- References Sim.Api + Sim.Impl only; zero Unity dependency.
- Can run via `dotnet test` or NUnit Edit Mode with no scene.

## Step 4: ScriptableObject patterns

Three patterns to know:

- **Balance/config data:** `[CreateAssetMenu]` SOs under `Resources/` or an Addressable group.
  Treat them as read-only at runtime.
- **Runtime sets:** a SO holding `List<T>` populated by components in `OnEnable`/`OnDisable`.
  Replaces global singletons for "all active units" style queries.
- **Event channels:** a SO that components register listeners on; call `Raise()` to broadcast.
  Decouples sender from receiver without a hard reference.

See [references/unity-architecture.md](references/unity-architecture.md) (ScriptableObject Patterns) for
copy-ready code for all three.

## Step 5: Composition over deep MonoBehaviour inheritance

If the project has multi-level MonoBehaviour hierarchies:
- Extract each concern into a focused MonoBehaviour or plain C# class.
- Compose via `[SerializeField]` references to `IMovement`, `IAttack`, etc.
- Strategy variants (attack patterns, move modes) become ScriptableObjects injected
  through the Inspector, swapped at runtime.
- No business logic in a class that also inherits from `MonoBehaviour`.

## Step 6: Verify commands

```bash
# Compile check: red asmdef errors appear here.
# Run via Unity MCP: CompileScripts or open the Editor and check Console.

# Run sim unit tests (no scene needed if sim is pure C#).
# Unity Test Framework: Edit Mode runner, or dotnet test if assembly is net-standard.
# Via Unity MCP:
#   RunTests mode:EditMode assemblyFilter:<Company>.<Feature>.Tests

# Confirm no forbidden cross-assembly references.
# Window > Analysis > Assembly Definition (in Editor) shows the graph.
```
