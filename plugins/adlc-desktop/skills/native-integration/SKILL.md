---
name: native-integration
description: "This skill should be used when wiring a desktop app into the operating system, \"add a tray icon\", \"build the app menu\", \"send a native notification\", \"register a custom protocol / deep link\", \"open my app from a URL\", \"let the user pick a file\", \"scoped file access\", \"add a native open/save dialog\", \"set up auto-update\", \"sign and notarize the updater\", or reviewing OS-integration code. Detect-first across Electron and Tauri v2; do menus, tray, notifications, user-consented file access, native dialogs, protocol handlers, and signed auto-update right, with the per-OS (macOS / Windows / Linux) differences called out. Pairs with desktop-ipc-security (the renderer boundary), desktop-packaging (sign / notarize / channels), and desktop-architecture (process model)."
version: 0.1.0
---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# Native integration

Wire the app into the OS the way each OS expects, not the way one platform happens to work. Every native surface (tray, menu, notification, file access, protocol, update) behaves differently on macOS, Windows, and Linux. Detect the framework, then handle the differences explicitly instead of assuming the macOS path is the only path.

## Step 1: Detect the framework first
Never impose a stack. Read the project before writing:
- **Electron:** `package.json` depends on `electron`; look for `electron-builder` or `electron-forge` and a `main` process file.
- **Tauri v2:** `src-tauri/tauri.conf.json` and `src-tauri/Cargo.toml` with `tauri = "2"`; plugins live under `@tauri-apps/plugin-*` and the matching Rust crates.
- **Native (Cocoa / Win32 / GTK):** no JS shell; integrate through the platform SDK directly.

Match the existing conventions (where the main process lives, how plugins are registered, the permission model). Native surfaces belong in the trusted process (Electron main, Tauri Rust core), never the renderer. The renderer asks; the trusted side acts. See `desktop-ipc-security`.

## Step 2: Menus and tray (per OS)
- **Application menu.** On macOS the menu bar is global and the first menu is the app name with the standard `about` / `services` / `hide` / `quit` roles; build it from menu `role`s so the OS localizes and wires shortcuts. On Windows and Linux the menu sits in the window. Use roles, not hand-rolled handlers, so platform accelerators and edit-menu behavior come for free.
- **Tray.** Electron: `new Tray(nativeImage)` then `tray.setContextMenu(menu)` (the tray menu pops automatically, no `menu.popup` needed). Tauri: `TrayIconBuilder` with a `menu`, and tray `click` / `double-click` / `enter` / `leave` events.
- **Tray icon, per OS.** macOS menu-bar icons must be **template images**: a black-plus-alpha PNG whose filename ends in `Template` (`iconTemplate.png`, plus `iconTemplate@2x.png`), then `image.setTemplateImage(true)` so it inverts in dark menu bars. Windows and Linux use a full-color icon and prefer a left-click action; Linux tray support depends on the desktop environment (AppIndicator / StatusNotifier), so test on the target DE and provide a window fallback.

## Step 3: Notifications
- Electron: the renderer `new Notification(title, options)` (HTML5) or `new Notification` from the main process. Tauri: the `notification` plugin (`@tauri-apps/plugin-notification`), which gates on `isPermissionGranted()` / `requestPermission()`.
- **Per OS.** macOS routes through Notification Center and requires the app to be signed and, in dev, may show nothing until the bundle is trusted; the app name and icon come from the bundle, not the call. Windows toasts need an **AppUserModelID** set (`app.setAppUserModelId(...)` in Electron) or the toast is dropped or mis-attributed; packaged installers set it for you. Linux uses the freedesktop notification spec via the running daemon, so behavior varies by DE and some options are ignored.
- Keep payloads short, never put secrets in a notification body (it can persist in the OS notification history), and make the click action deterministic.

## Step 4: Scoped file access and native dialogs (user-consented)
Least privilege: read and write only what the user explicitly picked or paths the app legitimately owns. Do not grant blanket filesystem access.
- **Native dialog as the consent gate.** The OS open/save dialog *is* the user consent. Electron: `dialog.showOpenDialog` / `dialog.showSaveDialog` from the main process. Tauri: the `dialog` plugin `open()` / `save()`. The returned path is the grant; operate on that, not on a path the renderer constructed.
- **Tauri scopes.** The `fs` plugin denies everything by default. Grant narrow scopes in a capability file (`src-tauri/capabilities/*.json`) using `$`-prefixed path variables (`$HOME`, `$APPCONFIG`, `$RESOURCE`) and explicit allow lists; **deny scopes win over allow scopes**, so add a deny for anything sensitive even inside an allowed root. Pair file commands with the dialog capability so the app can act on a user-selected path.
- **Electron.** There is no built-in scope system, so enforce it yourself: validate every renderer-supplied path in the main process (resolve, then check it is inside an allowed root, reject `..` traversal), and never pass a raw renderer path to `fs` without that check. See `desktop-ipc-security`.
- **macOS hardened runtime.** A sandboxed / notarized macOS app needs the right entitlements and uses security-scoped bookmarks to keep access to a user-picked file across launches; a plain path will fail under the sandbox.

## Step 5: Deep links and protocol handlers (the per-OS trap)
Registering `myapp://` is one call; *receiving* the URL differs sharply by OS, and this is where most bugs live.
- **Register.** Electron: `app.setAsDefaultProtocolClient('myapp')`. In dev (unpackaged) pass `process.execPath` and the script path so the OS can relaunch you; packaged, the scheme is declared in the bundle (see below). Tauri: the `deep-link` plugin with the scheme declared in `tauri.conf.json`.
- **Receive, per OS.**
  - **macOS:** the OS delivers the URL through the `open-url` event (`app.on('open-url', (e, url) => ...)`); the URL is the event argument. Packaging must declare `CFBundleURLTypes` / `CFBundleURLSchemes` in `Info.plist`.
  - **Windows and Linux:** the URL arrives as a **command-line argument to a new process**, not as an event. Take the single-instance lock (`app.requestSingleInstanceLock()`), then read the URL from the `second-instance` event's `commandLine` (typically `commandLine.pop()`); on cold start read it from `process.argv`. Linux also needs `MimeType=x-scheme-handler/myapp` in the `.desktop` file.
- **Single instance is mandatory.** Because Windows/Linux spawn a new process per link, without the single-instance lock you get a second window instead of focusing the running app. Tauri's `deep-link` plugin documents integrating with the `single-instance` plugin for exactly this. Always validate and parse the incoming URL as untrusted input before acting on it.

## Step 6: Signed auto-update
An unsigned or unverified update channel is a remote-code-execution path. Updates must be cryptographically verified before install, and that cannot be skipped.
- **Electron (`electron-updater`).** Supports macOS, Windows, and Linux; validates the code signature on both macOS and Windows and publishes the update metadata automatically. macOS auto-update (Squirrel.Mac) **requires the app to be code-signed and notarized**, full stop. Windows has no OS-level runtime integrity guarantee, so rely on the signature check the updater performs, sign the installer, and serve metadata (`latest.yml`) and artifacts over HTTPS.
- **Tauri (`updater` plugin).** Signature verification is **mandatory and cannot be disabled**: generate a keypair with `tauri signer generate`, put the **public** key in `tauri.conf.json`, keep the private key secret (CI secret), and the plugin checks each artifact against it with **Minisign (Ed25519)**. Endpoints support `{{target}}` / `{{arch}}` / `{{current_version}}` variables; the server returns JSON with `url`, `version`, and the `signature`.
- **Common rules.** Serve everything over HTTPS, support staged rollout, and gate the actual install behind a user prompt for a foreground app. Wiring the channel, signing, and notarization is `desktop-packaging`; this skill is the in-app integration that consumes it. Shipping a new update endpoint or a release is outbound: get the operator's explicit yes first.

## Step 7: Verify
The failable check runs **on the target OS** and proves both that the integration works and that the permission/path boundary holds. Pick the surface you touched:
- **Tray / menu / notification:** launch the packaged (or `tauri dev` / `electron .`) app on the target OS; confirm the tray icon renders (and inverts on a macOS dark menu bar), the menu items fire, and a notification appears in the OS notification center. A surface that only works on your dev OS is not done.
- **File access:** open the native dialog, pick a file, confirm the app reads/writes it, **and** confirm a path the user did *not* pick is rejected (Tauri: out-of-scope path errors; Electron: your main-process path guard rejects a `..` traversal). The negative case must fail closed.
- **Deep link:** with the app installed, trigger `myapp://test` from a browser or `open` / `xdg-open` / `start`; confirm the *running* instance focuses and receives the URL (not a second window), on each target OS you support.
- **Auto-update:** point the updater at a test release and confirm a tampered or wrong-signature artifact is **refused** (Tauri Minisign mismatch; Electron signature-validation failure). An update that installs without a valid signature is a failed check, not a passing one.

## References
- Electron: [Tray](https://www.electronjs.org/docs/latest/api/tray), [nativeImage template images](https://www.electronjs.org/docs/latest/api/native-image), [Deep Links](https://www.electronjs.org/docs/latest/tutorial/launch-app-from-url-in-another-app), [Code Signing](https://www.electronjs.org/docs/latest/tutorial/code-signing), [Updates](https://www.electronjs.org/docs/latest/tutorial/updates), [electron-builder auto-update](https://www.electron.build/auto-update).
- Tauri v2: [System Tray](https://v2.tauri.app/learn/system-tray/), [Notifications](https://v2.tauri.app/plugin/notification/), [File System](https://v2.tauri.app/plugin/file-system/), [Dialog](https://v2.tauri.app/plugin/dialog/), [Permissions](https://v2.tauri.app/security/permissions/), [Deep Linking](https://v2.tauri.app/plugin/deep-linking/), [Single Instance](https://v2.tauri.app/plugin/single-instance/), [Updater](https://v2.tauri.app/plugin/updater/).
- Pack neighbors: the renderer boundary and path validation: `desktop-ipc-security`. Sign / notarize / channels: `desktop-packaging`. Process model and security baseline: `desktop-architecture`. Outbound (publishing a release / endpoint) stops and gets the operator's explicit yes first.
