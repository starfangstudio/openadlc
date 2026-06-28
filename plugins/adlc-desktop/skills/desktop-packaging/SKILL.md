---
name: desktop-packaging
description: "This skill should be used when packaging, signing, or distributing a desktop app, \"build the installer\", \"make a DMG / NSIS / MSI\", \"code-sign the app\", \"notarize for macOS\", \"sign on Windows\", \"set up auto-update\", \"wire release channels\", \"build per-OS artifacts\", \"why is the app blocked by Gatekeeper / SmartScreen\", or reviewing a release pipeline. Detect-first across electron-builder and the Tauri bundler: produce signed, notarized, per-OS artifacts that launch clean, with secrets from the environment and auto-update wired. Pairs with desktop-architecture (the app), native-integration (auto-update at runtime), and the operator's explicit yes before going outbound (publishing is outbound)."
version: 0.1.0
---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# Desktop packaging

Ship a signed, notarized build that launches on a clean machine without a Gatekeeper or SmartScreen block. An unsigned build is a broken build: it runs on your machine and nowhere else. Detect the bundler the project already uses; do not impose one.

## Step 1: Detect the bundler and targets first
Never assume the stack. Read the repo before configuring anything:
- **electron-builder:** a `build` block in `package.json` or an `electron-builder.{yml,json,js}` file; `electron-builder` in devDependencies.
- **Tauri:** `src-tauri/tauri.conf.json` and a `[package.metadata]` / Cargo workspace; the `tauri` CLI.
- **Targets:** which OSes ship and in what format. macOS `dmg` + `zip` (zip is what auto-update consumes), Windows `nsis` (per-user, no admin) or `msi`, Linux `AppImage` / `deb` / `rpm`. Match what is already declared.

If neither is present, stop and ask which bundler to use; recommend Tauri for size and electron-builder for an existing Electron app. Do not scaffold a second one.

## Step 2: Secrets come from the environment, never the repo
This is the gate on packaging. Before touching signing config, confirm no certificate, key, or password is committed:
- Certificates as base64 in CI secrets, decoded to a temp file at build time and deleted after. Never a `.p12`, `.pfx`, or `.key` in git.
- Passwords, Apple app-specific passwords, and API keys come from env vars only. Add `*.p12`, `*.pfx`, `*.key`, `*.cer`, and `*.mobileprovision` to `.gitignore` and verify they are not already tracked.
- Reference them by name in config (electron-builder reads `CSC_LINK` / `CSC_KEY_PASSWORD`; Tauri reads `APPLE_CERTIFICATE`, `TAURI_SIGNING_PRIVATE_KEY`). A committed secret is a leak even after deletion; if one is found, treat it as compromised and rotate.

## Step 3: macOS, sign then notarize then staple
Notarization is separate from signing and is required for Gatekeeper to pass on a machine that never saw the app.
- **Sign** with a Developer ID Application certificate and **Hardened Runtime on**. Hardened Runtime breaks anything needing a loosened sandbox unless you declare entitlements, so add an `entitlements.plist` for what the app actually uses (JIT, allow-unsigned-memory, etc.) and nothing more.
- **Notarize** with `notarytool` (the `altool` path is gone). Supply `APPLE_ID`, `APPLE_APP_SPECIFIC_PASSWORD` (not your account password), and `APPLE_TEAM_ID`, or an App Store Connect API key. Apple scans the upload and returns a ticket.
- **Staple** the ticket to the artifact so the app validates offline. electron-builder notarizes and staples for you when `mac.notarize` is configured and the credentials are in the env; Tauri notarizes during `tauri build` when `APPLE_*` env vars are set. Verify with `spctl -a -vvv YourApp.app` and `xcrun stapler validate`.

## Step 4: Windows, sign with a modern certificate
SmartScreen reputation is now earned by download volume; since 2024 an EV certificate no longer buys an instant bypass, so OV and EV behave the same for SmartScreen.
- **Certificate options:** OV/EV certs now require the private key on a hardware token or HSM (CA/Browser Forum rule), which does not automate cleanly in CI. Prefer **Azure Trusted Signing** (now Azure Artifact Signing) for cloud signing with no token, integrated with `signtool` and GitHub Actions, for eligible US/CA/EU/UK orgs and self-employed individuals.
- **Sign** every executable, not just the installer: the app `.exe`, sidecars, and the NSIS uninstaller. Tauri's bundler signs all of these since 1.5; electron-builder signs via `win.signtoolOptions` (or the Azure Trusted Signing integration). Use SHA-256 and an RFC 3161 timestamp so signatures stay valid after the cert expires.
- **Gotcha:** an unsigned or low-reputation build shows "Windows protected your PC". That is expected for a brand-new cert until reputation builds; it is not a config bug. Verify with `signtool verify /pa /v Your-Setup.exe`.

## Step 5: Per-OS artifacts and channels
Build the right artifact per platform and keep the channel metadata honest:
- **macOS:** `dmg` for download, `zip` for auto-update (electron-updater needs the zip). **Windows:** `nsis` (per-user install, no admin prompt) is the friendliest default. **Linux:** `AppImage` plus `deb`/`rpm` as needed. Build each OS on its own runner; you cannot notarize macOS or sign Windows from a foreign OS.
- **Channels:** map a version suffix to a channel. electron-builder reads `1.2.3-beta` as the `beta` channel; set `generateUpdatesFilesForAllChannels: true` so `latest.yml`, `beta.yml`, and `alpha.yml` are all emitted. A `latest` user never sees prerelease; a `beta` user sees beta and latest.

## Step 6: Wire auto-update
- **electron-builder:** `electron-updater` reads `latest.yml` / `latest-mac.yml` from the first `publish` provider (GitHub Releases, generic HTTPS, S3). Auto-update keys off that first provider only, so upload the `.yml` metadata alongside the artifacts there.
- **Tauri:** the updater plugin checks `endpoints` for a `latest.json` carrying `version`, the per-target `url`, and a `signature`. Generate the keypair with `tauri signer generate`; ship the public key in `tauri.conf.json` (`plugins.updater.pubkey`), keep `TAURI_SIGNING_PRIVATE_KEY` in the env, and set `createUpdaterArtifacts: true`. **Lose the private key and you can never push an update to installed apps**, so back it up.
- Updates download new signed artifacts; the runtime install/restart flow lives in `native-integration`. Publishing artifacts or a release is outbound: stop and get the operator's explicit yes before anything leaves the machine.

## Step 7: Verify on a clean machine
The failable check is the only one that counts: take the signed artifact to a machine (or fresh VM) that has never built or trusted this app, install it, and confirm it launches with no Gatekeeper or SmartScreen block. Then verify the signature locally:
- macOS: `spctl -a -vvv YourApp.app` reports `accepted source=Notarized Developer ID` and `xcrun stapler validate YourApp.app` passes.
- Windows: `signtool verify /pa /v Your-Setup.exe` succeeds and the publisher name shows in the UAC/SmartScreen dialog.
- Auto-update: bump the version, publish to a staging channel, and confirm an older install detects and applies the update. A build that signs in CI but is blocked on a clean machine is not done.

## References
- The app and process model: `desktop-architecture`. Runtime auto-update (install/restart, deep links): `native-integration`. Publishing is outbound: get the operator's explicit yes first, per the global rules.
- electron-builder notarization: https://www.electron.build/docs/notarization/ . Auto-update and channels: https://www.electron.build/docs/features/auto-update/ and https://www.electron.build/tutorials/release-using-channels.html
- Tauri distribute and signing: https://v2.tauri.app/distribute/sign/macos/ , https://v2.tauri.app/distribute/sign/windows/ , and the updater plugin: https://v2.tauri.app/plugin/updater/
- Windows code-signing options (Azure Trusted Signing, OV vs EV, SmartScreen): https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/code-signing-options
