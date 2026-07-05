---
name: unity-store-build
description: >-
  This skill should be used when the user asks to "produce a store build", "build an
  AAB for Google Play", "export a signed Android build", "create an IPA for App Store",
  "archive the iOS build", "set up keystore signing in Unity", "configure Android signing
  config", "build in batchmode for CI", "generate the Xcode project from Unity",
  "set target API level", or "prepare a release build for upload". Produces signed
  store-ready artifacts (AAB for Android, Xcode archive/IPA for iOS) from a Unity
  project. Covers signing configuration, batchmode/CI automation, and target-SDK
  settings. Does NOT duplicate compliance gating: target SDK requirements, Privacy
  Manifest, and Data Safety live in the android-compliance and ios-store-compliance
  skills -- cross-reference them before uploading. Locally building is always fine;
  uploading to Play Console, App Store Connect, or TestFlight is outbound and requires
  the operator's explicit yes first.
version: 0.1.0
---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# unity-store-build

Produce signed store builds from Unity for Android (AAB) and iOS (Xcode archive + IPA).

## Step 1: Detect first

Read the project before touching any setting:

```bash
# Unity version and active modules
cat ProjectSettings/ProjectVersion.txt

# Existing player settings (bundle ID, target SDK, scripting backend, architectures)
grep -E "bundleIdentifier|targetSdkVersion|minSdkVersion|scriptingBackend|targetArchitectures|keystoreName|keyaliasName|buildAppBundle" ProjectSettings/ProjectSettings.asset | head -40

# Any existing CI/build scripts
find . -name "*.cs" -path "*/Editor/*" | xargs grep -l "BuildPipeline\|BuildPlayerOptions" 2>/dev/null | head -10
find . -name "Makefile" -o -name "*.sh" -o -name "*.yml" -o -name "*.yaml" | head -10
```

Record: bundle IDs for both platforms, existing signing setup (keystore path, alias),
scripting backend (IL2CPP required for stores), target/min SDK levels, whether a
batchmode build script already exists. Mark anything absent as `unknown`; ask before
inventing values.

## Step 2: Android -- configure signing and AAB output

**In the Unity Editor (via Unity MCP or manually):**

1. Open **Edit > Project Settings > Player > Android > Publishing Settings**.
2. Enable **Custom Keystore** and load the keystore file via Keystore Manager.
   Unity does not persist keystore passwords across editor restarts; store them in
   CI secrets (env vars), not in the project.
3. Set **Keystore password**, **Key alias**, and **Key alias password**.
4. In **File > Build Profiles > Android**, enable **Build App Bundle (Google Play)**.
   Google Play requires AAB; APK is only for sideloading or direct device install.
5. Verify scripting backend is **IL2CPP** and **Target Architectures** includes
   `ARM64` (mandatory for Play since August 2019; `ARMv7` optional for coverage).

**Via scripting (batchmode/CI -- preferred for reproducible builds):**

For the full `BuildScript.cs` implementation and CI invocation commands, see
[references/unity-store-build-detail.md](../../references/unity-store-build-detail.md) (section: "Android: batchmode build script" and "Android: CI invocation").

Output: `Builds/Android/game.aab`. Verify the file exists and is non-zero before proceeding.

**Compliance bridge:** target SDK level, Data Safety declarations, and Play policy
gating live in the **android-compliance** skill. Consult it before uploading.

## Step 3: iOS -- generate Xcode project, archive, export

Unity produces an Xcode project, not an IPA directly. The build is two stages.

**Stage A -- Unity: generate the Xcode project**

Set bundle ID to match the App Store Connect record, scripting backend to IL2CPP,
and output path to a directory (not a file). For the full `BuildiOS()` script and
batchmode invocation, see [references/unity-store-build-detail.md](../../references/unity-store-build-detail.md)
(sections: "iOS: Unity Xcode project generation script" and "iOS: Unity batchmode invocation").

Output: `Builds/iOS/` containing `Unity-iPhone.xcworkspace` (or `.xcodeproj`).

**Stage B -- Xcode: archive and export IPA**

Requires macOS with Xcode installed. Signing identity and provisioning profile must
be available in the macOS keychain before running. For the full `xcodebuild` commands
and minimum `ExportOptions.plist`, see [references/unity-store-build-detail.md](../../references/unity-store-build-detail.md)
(sections: "iOS: xcodebuild archive and export IPA" and "ExportOptions.plist (App Store minimum)").

Output: `Builds/iOS/export/<GameName>.ipa`.

**Compliance bridge:** Privacy Manifest (`PrivacyInfo.xcprivacy`) and App Store
metadata/rating requirements live in the **ios-store-compliance** skill. Consult it
before uploading.

## Step 4: Verify the artifacts

For the verification commands and how to diagnose an unsigned IPA, see
[references/unity-store-build-detail.md](../../references/unity-store-build-detail.md) (section: "Artifact verification").

## Outbound checkpoint

Local work needs no approval. Outbound here (uploading an AAB to the Google Play Console with its target track, or an archive/IPA to App Store Connect / TestFlight via xcrun altool, notarytool, Transporter, or fastlane deliver): stop, present exactly what would go out, and ask the operator for an explicit "yes" first.

## References

- Unity Manual: Build for Android -- https://docs.unity3d.com/Manual/android-BuildProcess.html
- Unity Manual: Android Player Settings -- https://docs.unity3d.com/6000.4/Documentation/Manual/class-PlayerSettingsAndroid.html
- Unity Scripting: `PlayerSettings.Android.targetSdkVersion` -- https://docs.unity3d.com/ScriptReference/PlayerSettings.Android-targetSdkVersion.html
- Unity Manual: Build a player from the command line -- https://docs.unity3d.com/6000.4/Documentation/Manual/build-command-line.html
- Unity Manual: Build an iOS application -- https://docs.unity3d.com/Manual/iphone-BuildProcess.html
- Unity Scripting: `BuildPipeline.BuildPlayer` -- https://docs.unity3d.com/ScriptReference/BuildPipeline.BuildPlayer.html
- Full code samples and verification commands: [references/unity-store-build-detail.md](../../references/unity-store-build-detail.md)
