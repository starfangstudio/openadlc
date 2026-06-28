---
name: desktop-architecture
description: "This skill should be used when choosing or structuring a desktop app, \"build a desktop app\", \"Electron vs Tauri\", \"should this be native or web-based\", \"set up the main and renderer process model\", \"where should logic live in my desktop app\", \"lock down Electron security\", \"context isolation and sandbox\", \"wire the preload bridge\", or reviewing a desktop app's architecture and security baseline. Detect-first across Electron, Tauri v2, and native (Swift / WinUI): pick the runtime, split privileged logic from UI, and harden the security baseline (context isolation on, nodeIntegration off, sandbox on). Pairs with desktop-ipc-security (the IPC surface), native-integration (OS features), and desktop-packaging (ship and sign)."
version: 0.1.0
---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# Desktop architecture

Pick the runtime that fits the project, then split the app into a privileged core and an untrusted UI. The renderer shows pixels; the main process owns the machine. Treat the UI as hostile and the boundary between them as the whole security story.

## Step 1: Detect before you choose
Never impose a runtime. Read the repo first:
- An existing desktop app (`package.json` with `electron`, a `src-tauri/` folder with `tauri.conf.json`, an Xcode `*.xcodeproj` / `Package.swift`, a `*.csproj` with WinUI). If one exists, match it and skip to Step 3.
- The team's language (TypeScript / web stack, Rust, Swift, C#) and the target OSes (macOS only, Windows only, or all three).

If nothing exists, this is a real fork. Stop and choose with Step 2, give the options plus a recommendation, do not guess.

## Step 2: Choose the runtime (only when greenfield)
One axis decides most of it: does the team already own a web UI and need cross-platform, or do they need deep single-OS native feel?

- **Tauri v2** (default for new cross-platform apps): Rust core plus the OS's own WebView. Small binaries, low memory, a capability / permission system that scopes IPC per window. Pick it when the team can write some Rust and wants the leanest cross-platform shipping path. Scaffold: `npm create tauri-app@latest`.
- **Electron**: bundles Chromium plus Node.js, so the renderer is identical on every OS and the whole Node ecosystem is available in the main process. Larger binaries (~100MB+) and more memory. Pick it when an existing web app must become a desktop app fast, or a feature needs the exact same Chromium everywhere.
- **Native (Swift / SwiftUI for macOS, WinUI 3 / C# for Windows)**: no web layer. Pick it for a single OS, the tightest platform integration, smallest footprint, or App Store / Store-store expectations. Cost: a separate codebase per OS.

Write the choice down with its trade-off (see `decision-record`). Do not mix two runtimes to avoid choosing.

## Step 3: Split the process model
Every option (Electron, Tauri, even native) has the same shape: a privileged process and an untrusted UI surface. Put logic on the right side of that line.

- **Main / core process (privileged):** owns file system, network, child processes, OS APIs, secrets, native modules. All heavy or sensitive work lives here. In Electron this is the Node.js `main` entry; in Tauri it is the Rust core.
- **Renderer / WebView (untrusted):** renders UI and handles user input only. Assume any code in it can be hijacked by injected content. It must hold no secrets and reach the OS only through one narrow, validated channel.
- **The bridge:** the renderer asks the main process to do privileged work over IPC. It never does that work itself. Design that surface as one named function per action, never a raw pass-through (the full IPC contract lives in `desktop-ipc-security`).

Rule of thumb: if a line of code touches the disk, the network, a secret, or the OS, it belongs in main, not in the renderer.

## Step 4: Set the Electron security baseline
For Electron, these `webPreferences` are the non-negotiable floor. Electron 20+ ships these as defaults, but assert them explicitly so a future edit cannot silently weaken them:

```js
// main.js
const win = new BrowserWindow({
  webPreferences: {
    contextIsolation: true,   // preload and page run in separate JS contexts
    nodeIntegration: false,   // no Node.js (require, process) in the renderer
    sandbox: true,            // OS-level sandbox; renderer has no Node env
    preload: path.join(__dirname, 'preload.js'),
  },
});
```

Setting `nodeIntegration: true` or `contextIsolation: false` also disables the sandbox for that renderer. Treat any of the three flipping the wrong way as a release blocker. Expose privileged calls only through a tiny `contextBridge` API in the preload, one wrapped `ipcRenderer.invoke` per channel, never the raw `ipcRenderer`:

```js
// preload.js
const { contextBridge, ipcRenderer } = require('electron');
contextBridge.exposeInMainWorld('api', {
  readConfig: () => ipcRenderer.invoke('config:read'), // one function per action
});
```

Also set a strict Content-Security-Policy and validate every IPC argument in main (see `desktop-ipc-security`).

## Step 5: Set the Tauri / native baseline
- **Tauri v2:** the WebView reaches the Rust core only through `invoke` commands, and the core checks each call against the window's **capabilities** before it runs. Grant the narrowest permission and scope per window (a settings window may write files; a help window may not), never a blanket allow. Keep all privileged logic in Rust commands.
- **Native:** there is no web renderer to sandbox, so the equivalent baseline is OS hardening: enable App Sandbox / the hardened runtime (macOS) or the app container (Windows), request the fewest entitlements / capabilities, and keep secrets in the Keychain / Credential Manager, not in app files.

## Step 6: Verify with a failable check
Two assertions, both must pass, or the architecture is not done:
1. **Smoke launch:** the app boots to a visible window and exits cleanly. For Electron / Tauri, drive it with Playwright's Electron support (`electron.launch()`) or `tauri dev`; assert the main window is created. Spectron is deprecated, do not use it.
2. **Security-config assertion:** a test that fails the build if the baseline is wrong. For Electron, read each `BrowserWindow`'s `webPreferences` and assert `contextIsolation === true`, `nodeIntegration === false`, `sandbox === true`. For Tauri, assert no capability grants a wildcard / unscoped permission. A passing smoke launch with a weakened security config is still a failure.

## References
- The IPC contract and CSP: `desktop-ipc-security`. OS features (menus, tray, notifications, deep links, auto-update): `native-integration`. Build, sign, notarize, distribute: `desktop-packaging`. Record the runtime choice: `decision-record`.
- Electron Security: https://www.electronjs.org/docs/latest/tutorial/security
- Electron Process Sandboxing: https://www.electronjs.org/docs/latest/tutorial/sandbox
- Electron contextBridge: https://www.electronjs.org/docs/latest/api/context-bridge
- Tauri v2 Process Model: https://v2.tauri.app/concept/process-model/
- Tauri v2 Security and Capabilities: https://v2.tauri.app/security/ and https://v2.tauri.app/security/capabilities/
- Playwright Electron testing: https://playwright.dev/docs/api/class-electron
