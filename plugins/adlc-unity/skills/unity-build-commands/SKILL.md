---
name: unity-build-commands
description: >-
  This skill should be used when the user asks to "build the Unity project", "run Unity
  tests", "run EditMode tests", "run PlayMode tests", "make a Unity player build", "build
  addressables", "build for Android/iOS", "trigger a batchmode build", "build content",
  "run tests from the command line", "use the Unity MCP to inspect the scene", "read the
  Unity console", "drive the Unity Editor from the agent", "what command builds/tests this
  Unity project", or "set up the MCP editor loop". Covers: Unity Test Framework CLI
  (EditMode + PlayMode), batchmode player builds via -executeMethod, Addressables CLI
  build, and the MCP-driven editor loop (scene/console inspection, play-mode iteration,
  profiler capture) with the human-in-loop gate for game-feel and visual polish.
version: 0.1.0
---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# Unity build commands

Run Unity builds and tests through the CLI (`-batchmode`) for headless automation, and
through the Unity MCP for live editor inspection and iteration. Never use both paths
simultaneously for the same operation; they are separate execution contexts.

## Detect first

Before running any command, verify the project's Unity version, path, and MCP state:

```bash
# Find the Unity version the project targets
cat /path/to/project/ProjectSettings/ProjectVersion.txt

# Find the Unity executable for that version (macOS)
ls /Applications/Unity/Hub/Editor/

# Confirm the project path (contains Assets/ and ProjectSettings/)
ls /path/to/project/Assets /path/to/project/ProjectSettings

# Check MCP bridge status (only if Editor is running)
# Edit > Project Settings > AI > Unity MCP > bridge must show "Running"
```

Set `UNITY_EXE` to the absolute path of the correct Unity binary. Mark anything not
resolvable as `unknown` and ask; never guess the executable path.

```bash
# macOS example -- substitute the real version
UNITY_EXE="/Applications/Unity/Hub/Editor/6000.3.0f1/Unity.app/Contents/MacOS/Unity"
PROJECT="/absolute/path/to/YourProject"
```

## Running tests (Unity Test Framework)

Tests run in **batchmode**: no GUI, no manual input. EditMode tests are faster; PlayMode
tests require Play mode entry and take longer. Run the narrowest scope that proves the
change.

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
```

Results are NUnit XML at `-testResults`. Exit code `0` = all passed; non-zero = failures
or error. For filtering by assembly, category, or test name, see the detail file.

## Batchmode player build

Player builds require a static C# method in `Assets/Editor/` that calls
`BuildPipeline.BuildPlayer`. Trigger it with `-executeMethod`.

```bash
"$UNITY_EXE" -batchmode -quit \
  -projectPath "$PROJECT" \
  -buildTarget Android \
  -executeMethod BuildScripts.BuildAndroid \
  -logFile "$PROJECT/Logs/build-android.log"
```

Read the log for errors if exit code is non-zero. A stacktrace means the build method
threw; check for missing signing config, missing SDK path, or an uncaught exception. For
full flag reference and error-diagnosis notes, see the detail file.

## Addressables build (CLI)

Addressables has no dedicated batchmode flag. The Editor method must call
`AddressableAssetSettings.BuildPlayerContent()` before `BuildPipeline.BuildPlayer`. Run
content-only and player builds as separate invocations (content first, then player; they
share the catalog). For the full command and separate-invocation pattern, see the detail
file.

## MCP-driven editor loop

Use the Unity MCP when the Editor is already running and you need to inspect or iterate
on live state: scenes, GameObjects, console logs, profiler data, or visual output.

**Prerequisite**: follow the one-time setup in
[references/unity-mcp.md](references/unity-mcp.md) before using any tool below.

Common iteration loop (ordered):

```
1. Unity.GetConsoleLogs        -- read errors and warnings
2. Unity.ValidateScript        -- check a script compiles (no full rebuild needed)
3. Unity.ManageGameObject      -- inspect / modify a GameObject or component
4. Unity.ManageEditor {play}   -- enter Play mode
5. Unity.GetConsoleLogs        -- read runtime output
6. Unity.ManageEditor {stop}   -- exit Play mode
7. Inspect / fix / repeat
```

For scene inspection tools, profiler tools, and the full MCP tool list, see the detail
file.

### Human-in-loop gate (game-feel and visual polish)

The MCP can enter Play mode and capture screenshots, but it cannot make subjective
game-feel or visual-polish decisions. When iterating on feel, timing, visual fidelity, or
audio:

1. Capture: `Unity.Camera.Capture` or `Unity.SceneView.Capture2DScene`.
2. Present the capture to the operator with a plain description of what changed.
3. Wait for explicit feedback before the next iteration.

Never auto-advance through feel/polish iterations without operator input.

## Verify loop

After any change, run the narrowest verifier first, then broaden only on failure:

```
1. Unity.ValidateScript             -- immediate compile check (MCP path)
2. EditMode batchmode tests         -- logic, determinism, unit coverage
3. PlayMode batchmode tests         -- integration / in-editor gameplay
4. Player build                     -- confirms packaging and signing
```

Do not claim done without a green test run or a successful player build. A log file with
`Build succeeded` and exit code `0` is the proof.

## Outbound checkpoint

Local work needs no approval. Outbound here (uploading a player build to the Google Play Console, Apple App Store, or any external distribution channel): stop, present exactly what would go out, and ask the operator for an explicit "yes" first.

## References

- [references/unity-build-commands-detail.md](references/unity-build-commands-detail.md) -- full command
  samples, flag reference, and MCP tool lists for all operations in this skill.
- [references/unity-mcp.md](references/unity-mcp.md) -- Unity MCP setup, all 51 built-in
  tools, what the MCP can vs. cannot do, and the agent loop pattern.
- Unity Test Framework CLI reference:
  https://docs.unity3d.com/Packages/com.unity.test-framework@1.4/manual/reference-command-line.html
- Build a player from the command line (Unity 6):
  https://docs.unity3d.com/6000.4/Documentation/Manual/build-command-line.html
- Unity MCP get started (com.unity.ai.assistant @2.7):
  https://docs.unity3d.com/Packages/com.unity.ai.assistant@2.7/manual/integration/unity-mcp-get-started.html
