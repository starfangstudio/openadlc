---
name: desktop-ipc-security
description: "This skill should be used when wiring or hardening the boundary between a desktop app's privileged backend and its untrusted renderer, \"secure IPC\", \"set up contextBridge\", \"expose an API to the renderer\", \"preload script\", \"ipcMain handler\", \"Tauri command\", \"capabilities\", \"allowlist\", \"is this IPC channel safe\", \"why can the renderer call Node\", \"add a CSP to my Electron/Tauri app\", or reviewing the IPC surface before ship. Detect-first across Electron (contextBridge + ipcMain) and Tauri 2 (commands + capabilities): expose a minimal typed API, validate every message, never hand the renderer fs/exec/system access, treat all renderer content as untrusted, and lock it down with a strict CSP. Pairs with desktop-architecture (the process model) and desktop-reviewer (the review)."
version: 0.1.0
---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# Desktop IPC security

The renderer runs web content, so treat it as hostile: one XSS or one malicious sub-resource is now executing in your renderer. The whole job of the IPC layer is to make sure that even a fully compromised renderer cannot read the disk, spawn a process, or reach the network beyond what you explicitly allowed. Default-deny, expose the minimum, validate everything.

## Step 1: Detect the framework and the existing surface first
Never impose a stack. Read the project before touching it:
- **Electron:** `package.json` depends on `electron`. Look for `webPreferences` in the `BrowserWindow` setup, a `preload` script, and `ipcMain.handle` / `ipcMain.on` calls. Confirm `contextIsolation`, `nodeIntegration`, and `sandbox` settings.
- **Tauri:** `src-tauri/tauri.conf.json` and a Rust crate. Look for `#[tauri::command]` functions, the `tauri::generate_handler!` list, and `src-tauri/capabilities/*.json`.
- **Neither (native, Qt, etc.):** map the existing IPC primitive (named pipe, local socket, message port) and apply the same principles (typed contract, validate every message, least privilege). The rest of this skill uses Electron and Tauri as the two concrete tracks.

Inventory what the renderer can already call before adding anything. You cannot secure a surface you have not enumerated.

## Step 2: Lock the process baseline (Electron)
The bridge is only safe if the renderer cannot bypass it. These `webPreferences` are the secure defaults in current Electron; confirm them, do not assume:
- `contextIsolation: true` (default since Electron 12). Without it the preload and renderer share one JS context and prototype pollution in the renderer reaches your preload's scope.
- `nodeIntegration: false` (the default). The renderer must never have `require`.
- `sandbox: true`. Runs the renderer in an OS sandbox even if Node leaks.
- `webSecurity: true` (the default). Never disable it.

**Lock navigation and window creation** (Electron): a renderer that can navigate off-origin or spawn windows escapes the contextBridge. On each `webContents`, deny it:
```js
contents.on('will-navigate', (e, url) => { if (new URL(url).origin !== APP_ORIGIN) e.preventDefault() })
contents.setWindowOpenHandler(({ url }) => isAllowed(url) ? { action: 'allow' } : (shell.openExternal(url), { action: 'deny' }))
```
Open external links in the OS browser (`shell.openExternal`), never in-app. (Tauri: pin the allowed navigation in the capability / config.)

If any of these is off, fix that first; nothing below holds otherwise. Tauri's webview is sandboxed by design and has no Node, so its equivalent baseline is the capability set in Step 4.

## Step 3: Expose a minimal typed API, never the raw channel
The renderer gets a small, named, typed API and nothing else. Hand it raw `ipcRenderer` or any Node object and you have handed it everything.

**Electron** preload using `contextBridge.exposeInMainWorld`. Expose one function per operation; serialize to plain types (string, number, plain object, array) before they cross the bridge:
```js
// preload.js
const { contextBridge, ipcRenderer } = require('electron')

contextBridge.exposeInMainWorld('api', {
  // one method per IPC message, not a passthrough
  getProfile: (id) => ipcRenderer.invoke('profile:get', id),
  onCounter: (cb) => ipcRenderer.on('counter:update', (_e, v) => cb(v)),
})
```
Hard rules:
- Never `exposeInMainWorld('ipc', ipcRenderer)` or expose `require`, `process`, a Node `Buffer`, stream, or `EventEmitter`. Those leak Node internals across the bridge.
- Never pass the raw Electron `event` to the renderer callback (it carries `sender`). Forward only the data argument, as above.
- Give the API a typed contract (a `.d.ts` for the `window.api` shape) so the renderer and the handlers share one definition.

**Tauri** exposes Rust functions as commands; the renderer calls them by name. Keep each command narrow and typed:
```rust
#[tauri::command]
fn get_profile(id: u32) -> Result<Profile, String> { /* ... */ }

fn main() {
  tauri::Builder::default()
    .invoke_handler(tauri::generate_handler![get_profile]) // explicit allowlist
    .run(tauri::generate_context!())
    .expect("error while running tauri app");
}
```
Only commands listed in `generate_handler!` exist, and a window can call a command only if a capability grants it (Step 4).

## Step 4: Default-deny the surface (allowlist, not blocklist)
Enumerate what the renderer may do and deny the rest.

**Tauri** capabilities live in `src-tauri/capabilities/*.json` and bind permissions to specific windows. A window matching no capability has no IPC access at all:
```json
{
  "$schema": "../gen/schemas/desktop-schema.json",
  "identifier": "main-capability",
  "description": "What the main window may do",
  "windows": ["main"],
  "permissions": ["core:window:allow-set-title"]
}
```
Reference the capability set in `tauri.conf.json` under `app.security.capabilities`. Grant the narrowest permission that works; prefer scopes with explicit `allow` / `deny` paths over a whole API family. Tauri 2 makes this per-window and per-scope; do not regress to a flat on/off allowlist.

**Electron** has no built-in allowlist, so the preload is your allowlist: the only channels that exist for the renderer are the ones you wrote a method for in Step 3. Keep that list short and audit it. Register exactly one handler per channel with `ipcMain.handle` (request/response) or `ipcMain.on` (fire-and-forget); never a catch-all.

## Step 5: Validate every message, on the privileged side
Treat every IPC argument as attacker-controlled. The renderer's "type" is a suggestion, not a guarantee.
- **Schema-validate** every argument in the handler (a validator such as zod, or explicit type and range checks). Reject and return an error on anything unexpected; never throw raw internals back across the bridge.
- **Verify the sender** in Electron. Check `event.senderFrame` so only your own content can call a handler:
  ```js
  ipcMain.handle('profile:get', (e, id) => {
    if (!isTrustedFrame(e.senderFrame)) return null
    if (!Number.isInteger(id)) return null
    return getProfile(id)
  })
  function isTrustedFrame(frame) {
    return new URL(frame.url).host === 'app.localhost' // your origin only
  }
  ```
- **Canonicalize and contain file paths.** If a handler or command takes a path, resolve it (`path.resolve` / Rust `dunce::canonicalize`) and confirm it stays inside an allowed root before any read or write. Reject `..` traversal. In Tauri, prefer a path scope in the capability over hand-rolled checks.
- **Bound everything else:** validate ids, enum values, and lengths; cap array and string sizes so a single message cannot exhaust memory.

## Step 6: Never expose fs, exec, or system APIs to the renderer
The renderer asks for an *outcome*; the privileged side decides whether and how. Do not expose a primitive the renderer can aim.
- No generic `readFile(path)`, `writeFile(path, data)`, `exec(cmd)`, `spawn`, env access, or "run this SQL" method. Each is a full compromise behind one XSS.
- Expose intent-named operations instead: `exportReport(reportId)` that writes to a fixed app directory, not `writeFile`. `pickAndOpenImage()` that runs the native file dialog in the main process and returns bytes, not a path the renderer chose.
- Keep all filesystem, process, network-to-disk, and OS calls in the main process (Electron) or Rust side (Tauri). The renderer never holds the capability, only the request.
- For native dialogs, menus, tray, and the like, see `native-integration`; the same rule applies, the privileged side owns the action.

## Step 7: Set a strict Content Security Policy
A strict CSP is the backstop that stops injected script and blocks exfiltration even if something slips through. Treat all renderer content as untrusted and disallow remote code.

**Electron** set it as a response header (stronger than a meta tag, which the page can race), starting from `default-src 'none'` and adding back only what you need:
```js
session.defaultSession.webRequest.onHeadersReceived((details, cb) => {
  cb({ responseHeaders: {
    ...details.responseHeaders,
    'Content-Security-Policy': ["default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self' https://api.example.com"]
  }})
})
```
**Tauri** set `app.security.csp` in `tauri.conf.json` with the same shape.

Rules for both: no `unsafe-inline` or `unsafe-eval` in `script-src`; pin `connect-src` to the exact API origins so a compromised renderer cannot phone home; load scripts and styles from `'self'`, not a CDN.

## Step 8: Verify (the failable check)
Two checks, both must pass, or the IPC surface is not done:

1. **IPC contract test.** For each exposed method or command, an automated test that (a) a valid request returns the expected result, and (b) malformed, out-of-range, or wrong-type input is rejected (returns an error / null, never executes). For a path argument, include a `..` traversal case that must be denied. In Tauri, assert that a window without the capability cannot invoke the command.

2. **No-privileged-leak check.** An automated assertion that the renderer's exposed surface contains no raw escape hatch. Concretely:
   - Electron: in a renderer-context test, assert `window.require`, `window.process`, and a raw `ipcRenderer` / `ipc` global are all `undefined`, and that `window.api` exposes only the allowlisted method names (compare keys against the expected set; fail on any extra).
   - Tauri: parse `generate_handler!` and the capability files; assert every exposed command is intentional and no command grants `fs`/`shell`/`exec`-class access to an unintended window. A missing CSP also fails the check.

If either check cannot be written for a given surface, that surface is too broad; narrow it until it can.

## References
- The process model and where logic lives: `desktop-architecture`. The independent pre-merge review: `desktop-reviewer`. OS integration done from the privileged side: `native-integration`. General injection / hardening lenses: `adlc-security`.
- Electron security guide: https://www.electronjs.org/docs/latest/tutorial/security and contextBridge: https://www.electronjs.org/docs/latest/api/context-bridge
- Tauri capabilities: https://v2.tauri.app/security/capabilities/ , permissions: https://v2.tauri.app/security/permissions/ , and calling Rust from the frontend: https://v2.tauri.app/develop/calling-rust/
