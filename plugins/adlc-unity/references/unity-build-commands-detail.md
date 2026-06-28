<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
Consumed by the `unity-build-commands` skill. Load on demand; do not load independently.

---

## Running tests (Unity Test Framework): full command reference

```bash
# EditMode tests -- all assemblies
"$UNITY_EXE" -batchmode -runTests -testPlatform EditMode \
  -projectPath "$PROJECT" \
  -testResults "$PROJECT/TestResults-EditMode.xml" \
  -logFile "$PROJECT/Logs/test-editmode.log" \
  -quit

# PlayMode tests -- all assemblies
"$UNITY_EXE" -batchmode -runTests -testPlatform PlayMode \
  -projectPath "$PROJECT" \
  -testResults "$PROJECT/TestResults-PlayMode.xml" \
  -logFile "$PROJECT/Logs/test-playmode.log" \
  -quit

# Filter by assembly, category, or test name (semicolon-separated)
"$UNITY_EXE" -batchmode -runTests -testPlatform EditMode \
  -projectPath "$PROJECT" \
  -assemblyNames "MyGame.Simulation.Tests" \
  -testCategory "Determinism;Core" \
  -testResults "$PROJECT/TestResults.xml" \
  -logFile "$PROJECT/Logs/test.log" \
  -quit

# Filter to a single test or regex pattern
  -testFilter "MyGame.Simulation.Tests.LockstepTests.DeltaIsReproducible"
```

Results are NUnit XML at `-testResults`. Exit code `0` = all passed; non-zero = failures or error. If the process hangs, add `-playerHeartbeatTimeout 300` (seconds) to prevent indefinite waits on PlayMode player launch.

---

## Batchmode player build: command and flags

```bash
# Trigger a build for Android (substitute your method path)
"$UNITY_EXE" -batchmode -quit \
  -projectPath "$PROJECT" \
  -buildTarget Android \
  -executeMethod BuildScripts.BuildAndroid \
  -logFile "$PROJECT/Logs/build-android.log"
```

Key flags:

- `-batchmode`: headless, no GUI popups.
- `-quit`: exits the Editor after `executeMethod` returns; omit if the method calls `EditorApplication.Exit` itself.
- `-logFile`: write to a file; pass `-` for stdout.
- `-buildTarget`: sets the active build target before the method runs.

A stacktrace in the log means the build method threw; check for missing signing config, missing SDK path, or an uncaught exception.

---

## Addressables build: command and notes

```bash
"$UNITY_EXE" -batchmode -quit \
  -projectPath "$PROJECT" \
  -buildTarget Android \
  -executeMethod BuildScripts.BuildAddressablesAndPlayer \
  -logFile "$PROJECT/Logs/build-addressables.log"
```

The Editor method must call `AddressableAssetSettings.BuildPlayerContent()` before `BuildPipeline.BuildPlayer`. For content-only builds, run them as separate invocations (content build first, then player build; they share the catalog).

---

## MCP tool reference

### Iteration loop (ordered steps)

```
1. Unity.GetConsoleLogs        -- read errors and warnings
2. Unity.ValidateScript        -- check a script compiles (no full rebuild needed)
3. Unity.ManageGameObject      -- inspect / modify a GameObject or component
4. Unity.ManageEditor {play}   -- enter Play mode
5. Unity.GetConsoleLogs        -- read runtime output
6. Unity.ManageEditor {stop}   -- exit Play mode
7. Inspect / fix / repeat
```

### Scene inspection tools

```
Unity.ManageScene              -- load, save, query scene hierarchy
Unity.FindProjectAssets        -- locate assets by name or semantic query
Unity.Grep                     -- ripgrep search across project files
Unity.GetProjectData           -- project-wide settings and package list
```

### Profiler tools

```
Unity.Profiler.GetFrameRangeTopTimeSummary         -- hottest methods in a frame range
Unity.Profiler.GetOverallGcAllocationsSummary       -- GC pressure overview
Unity.Profiler.GetFrameGcAllocationsSummary         -- per-frame allocations
```

Profiler tools require the Profiler window to have captured frames; they return empty results if the Profiler is closed or has no data.
