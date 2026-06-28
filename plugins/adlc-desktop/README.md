<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
# adlc-desktop

The desktop app domain pack (build Electron / Tauri / native desktop apps). Detect-first. Pairs with `adlc-design` (tokens, a11y, Figma) for the renderer UI and `adlc-security` for IPC / CSP hardening.

## Skills
- `desktop-architecture`: Electron vs Tauri vs native; the main / renderer process model; where logic lives; the security baseline (context isolation, no nodeIntegration, sandbox).
- `desktop-ipc-security`: secure IPC between main and renderer (Electron contextBridge / Tauri commands), validate every message, never expose Node or system APIs to the renderer, a strict CSP.
- `native-integration`: OS integration, menus, tray, notifications, file system, native dialogs, deep links, and auto-update; per-OS differences.
- `desktop-packaging`: build, code-sign, notarize (macOS) and sign (Windows), distribute, and wire auto-update channels (electron-builder / Tauri bundler).

## Agents
- `desktop-architect`: design the process model, IPC surface, and native integration. Read-only, produces a plan.
- `desktop-reviewer`: review desktop changes (IPC security, packaging / signing, native integration) before the operator's explicit yes to go outbound.

## Status
Stable. Authored skills and agents for building desktop apps, following [the pack format](../../docs/pack-format.md).
