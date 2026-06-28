<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
# Unity MCP reference

The **Unity AI Assistant MCP** (`com.unity.ai.assistant`) bridges Claude Code (and other MCP
clients) to a live Unity Editor session via a local IPC channel. It replaces polling or
manual copy-paste when working with scenes, GameObjects, scripts, and the console.

## Requirements

- **Unity 6.3 (6000.3.x) or later** with `com.unity.ai.assistant` >= 2.7.0-pre installed
  via the Package Manager.
- The Editor must be **running** and the bridge must be **Running** (green) in
  Edit > Project Settings > AI > Unity MCP.

## Setup (one-time per machine)

1. Open the project in Unity 6.3+.
2. Install or verify `com.unity.ai.assistant` in the Package Manager.
3. Edit > Project Settings > AI > Unity MCP > confirm bridge shows **Running**.
4. Expand **Integrations**, select **Claude Code**, click **Configure**; Unity writes the
   relay binary path into `~/.claude/claude_mcp_settings.json` automatically.
   - Manual fallback: add `{ "mcpServers": { "unityMCP": { "url": "http://localhost:8080/mcp" } } }` to `.claude/settings.json`; change port if 8080 is taken.
5. First connection: Unity shows **Pending Connection** -- approve it in the settings page.
   Claude Code then appears under **Connected Clients**.
6. Most tools are disabled by default. Activate individual tools at
   Edit > Project Settings > AI > Unity MCP > Built-in tools.

## What the MCP CAN do (51 built-in tools, Unity 6.3 / @2.7)

### Core tools (always useful for agent loops)

| Tool | What it does |
|---|---|
| `Unity.RunCommand` | Execute arbitrary C# in the Editor (enabled by default) |
| `Unity.ManageScene` | Load / save / query scenes |
| `Unity.ManageGameObject` | Create, modify, delete GameObjects and components |
| `Unity.ManageEditor` | Set play/pause state; manage tags and layers |
| `Unity.ManageMenuItem` | Trigger any Editor menu item by path |
| `Unity.ManageAsset` | Import, create, modify, move assets |
| `Unity.ManageShader` | Create/edit shader scripts |
| `Unity.ReadConsole` / `Unity.GetConsoleLogs` | Read (and clear) console output + stack traces |
| `Unity.CreateScript` / `Unity.ApplyTextEdits` / `Unity.ScriptApplyEdits` | Write/edit C# files |
| `Unity.ValidateScript` | Diagnose compilation errors without rebuilding the player |
| `Unity.FindProjectAssets` | Search assets by name or semantic description |
| `Unity.Grep` | ripgrep search across the project |
| `Unity.GetProjectData` | Project overview (settings, packages, build targets) |
| `Unity.PackageManager.*` | Query and install/remove packages |

### Debug / Profiler tools (need the Profiler window open with data captured)

`Unity.Profiler.GetFrameRangeTopTimeSummary`, `GetFrameTopTimeSamplesSummary`,
`GetSampleTimeSummary`, `GetOverallGcAllocationsSummary`, `GetFrameGcAllocationsSummary`, etc.

### Visual capture tools (high cost; use sparingly on CI)

`Unity.Camera.Capture`, `Unity.SceneView.Capture2DScene`, `Unity.SceneView.CaptureMultiAngleSceneView`

### AI asset generation (consumes Unity Credits)

`Unity.AssetGeneration.GenerateAsset` and related tools. Credit consumption is real
money; never call these autonomously -- always show the user what would be generated and
wait for an explicit yes.

## What the MCP CANNOT do

- **Run tests**: no `runTests` equivalent; use the CLI batchmode path instead.
- **Build players**: no player-build tool; use `-executeMethod` CLI path instead.
- **Build Addressables**: no Addressables build tool; use CLI or `Unity.RunCommand` to
  invoke `AddressableAssetSettings.BuildPlayerContent()` in-editor.
- **File I/O outside the project**: all asset operations are scoped to `Assets/`.
- **Profiler data if the Profiler is closed**: profiler tools return empty results unless
  the Profiler window has captured frames.
- **Operate without a running Editor**: batchmode builds and tests do not use the MCP;
  they bypass it entirely.
- **Approve connections autonomously**: first-time client approval requires a human click
  in the Unity settings page.

## Agent loop pattern

```
1. Unity.GetConsoleLogs        -- read current errors
2. Unity.ValidateScript        -- check a changed script compiles
3. Unity.ManageEditor (play)   -- enter Play mode
4. Unity.GetConsoleLogs        -- read runtime output
5. Unity.ManageEditor (stop)   -- exit Play mode
6. Inspect / fix / repeat
```

Game-feel and visual-polish decisions that require subjective human judgement MUST be
handed back to the operator. The agent captures screenshots via `Unity.Camera.Capture` or
`Unity.SceneView.Capture2DScene`, presents them, and waits for feedback before proceeding.

## References

- Unity AI Assistant MCP overview:
  https://docs.unity3d.com/Packages/com.unity.ai.assistant@2.7/manual/integration/unity-mcp-overview.html
- Get started with Unity MCP:
  https://docs.unity3d.com/Packages/com.unity.ai.assistant@2.7/manual/integration/unity-mcp-get-started.html
- Unity MCP built-in tools complete reference (51 tools, third-party but accurate):
  https://gamedevllm.com/en/unity-mcp-builtin-tools-reference-en/
