<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
Consumed by the `unity-testing` skill. Load on demand; do not load independently.

## Assembly definition layout

Match the pattern of any existing test assembly. If none exists, use this layout:

```
Assets/
  <YourCode>/
    Runtime/
      <YourCode>.asmdef          # production assembly, no TestAssemblies ref
  Tests/
    EditMode/
      <YourCode>.Tests.EditMode.asmdef   # includePlatforms: ["Editor"]
    PlayMode/
      <YourCode>.Tests.PlayMode.asmdef   # includePlatforms: [] (all platforms)
```

**EditMode `.asmdef` minimum fields:**
```json
{
  "name": "<YourCode>.Tests.EditMode",
  "references": ["<YourCode>.Runtime"],
  "includePlatforms": ["Editor"],
  "optionalUnityReferences": ["TestAssemblies"]
}
```

**PlayMode `.asmdef` minimum fields:**
```json
{
  "name": "<YourCode>.Tests.PlayMode",
  "references": ["<YourCode>.Runtime"],
  "includePlatforms": [],
  "optionalUnityReferences": ["TestAssemblies"]
}
```

EditMode tests run inside the Editor without entering Play mode; use `[Test]`.
PlayMode tests run inside the game loop; use `[UnityTest]` with `yield return` only
when frame-skipping or time delays are genuinely required. Prefer `[Test]` everywhere else.

## Golden-replay determinism test (code sample)

```csharp
[Test]
public void SimRun_GivenSeed_MatchesGoldenHash()
{
    // 1. Load the golden input (commands + seed) from a committed binary or JSON
    var replay = ReplayLoader.Load("Assets/Tests/EditMode/Replays/golden_001.json");

    // 2. Run the sim deterministically (pure C#, no MonoBehaviour, no Unity physics)
    var result = SimRunner.RunToEnd(replay.Seed, replay.Commands);

    // 3. Hash the output state and compare to the committed hash
    Assert.AreEqual(replay.ExpectedStateHash, SimHasher.Hash(result),
        "Sim output changed -- update the golden file if intentional, " +
        "otherwise a determinism regression was introduced.");
}
```

Commit golden files under `Assets/Tests/EditMode/Replays/`. When the sim changes
intentionally, regenerate the golden file with a dedicated editor tool and commit the
new hash; treat an unexpected hash change as a blocking regression.

## CLI flags reference

```bash
# EditMode only (fast, no scene load, default for the sim)
/path/to/Unity -batchmode -runTests \
  -testPlatform EditMode \
  -projectPath /path/to/project \
  -testResults ./test-results-editmode.xml \
  -logFile ./unity-test.log

# PlayMode inside the Editor
/path/to/Unity -batchmode -runTests \
  -testPlatform PlayMode \
  -projectPath /path/to/project \
  -testResults ./test-results-playmode.xml \
  -logFile ./unity-test.log

# Filter to a single assembly or test class
  -assemblyNames "Sim.Tests.EditMode" \
  -testFilter "SimDeterminismTests"
```

Exit code 0 = all pass, non-zero = failures. Parse `test-results-*.xml` (NUnit format)
in CI. Always pass `-logFile`; batchmode suppresses console output by default.
