---
name: unity-store-build
description: >-
  This skill should be used when the user asks to "produce a store build", "build an
  AAB for Google Play", "export a signed Android build", "create an IPA for App Store",
  "archive the iOS build", "set up keystore signing in Unity", "configure Android signing
  config", "build in batchmode for CI", "generate the Xcode project from Unity",
  "run xcodebuild archive/export on a Unity iOS build", "fix an IL2CPP build failure on CI",
  "fix a provisioning profile mismatch", "my keystore is lost or wrong", or "prepare a
  release build for upload". Produces signed store-ready artifacts (AAB for Android,
  Xcode archive/IPA for iOS) from a Unity project, scripted-first for reproducible CI.
  Covers signing, keystore custody, batchmode automation, and store-build failure modes.
  Does NOT duplicate compliance gating: target SDK requirements, Privacy Manifest, and
  Data Safety live in the android-compliance and ios-store-compliance skills, cross-reference
  them before uploading. Day-to-day dev/test builds belong to unity-build-commands.
  Local building is always fine; uploading to Play Console, App Store Connect, or
  TestFlight is outbound and requires the operator's explicit yes first.
version: 0.2.0
---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# unity-store-build

Produce signed, reproducible store builds from Unity: Android AAB and iOS Xcode archive + IPA.
Prefer the scripted (batchmode/CI) path. The Editor-menu path is a fallback for one-off
local builds only.

## When NOT to use this

- Day-to-day dev/test/player builds and running Unity tests: use **unity-build-commands**.
- Target-SDK deadlines, Data Safety, Privacy Manifest, store metadata/rating: those are
  compliance content, use **android-compliance** and **ios-store-compliance**. This skill
  produces the artifact, it does not certify policy.

## Step 1: Detect first

```bash
cat ProjectSettings/ProjectVersion.txt   # Unity version + modules
grep -E "bundleIdentifier|scriptingBackend|targetArchitectures|keystoreName|keyaliasName|buildAppBundle" ProjectSettings/ProjectSettings.asset | head -40
find . -path "*/Editor/*.cs" | xargs grep -l "BuildPipeline\|BuildPlayerOptions" 2>/dev/null | head -10
```

Record bundle IDs (both platforms), signing setup (keystore path, alias), scripting
backend (IL2CPP is required for stores), target/min SDK, and whether a batchmode build
script exists. Mark anything absent as `unknown` and ask before inventing values.

## Step 2: Android, scripted (preferred)

Signing feeds from env vars so secrets never enter source. Minimal `BuildScript.cs` sketch:

```csharp
// Editor/BuildScript.cs
public static void BuildAndroid() {
    PlayerSettings.Android.useCustomKeystore = true;
    PlayerSettings.Android.keystoreName = System.Environment.GetEnvironmentVariable("KEYSTORE_PATH");
    PlayerSettings.Android.keystorePass = System.Environment.GetEnvironmentVariable("KEYSTORE_PASS");
    PlayerSettings.Android.keyaliasName = System.Environment.GetEnvironmentVariable("KEY_ALIAS");
    PlayerSettings.Android.keyaliasPass = System.Environment.GetEnvironmentVariable("KEY_ALIAS_PASS");
    PlayerSettings.SetScriptingBackend(NamedBuildTarget.Android, ScriptingImplementation.IL2CPP);
    PlayerSettings.Android.targetArchitectures = AndroidArchitecture.ARM64 | AndroidArchitecture.ARMv7;
    EditorUserBuildSettings.buildAppBundle = true;  // AAB, not APK
    var opts = new BuildPlayerOptions {
        scenes = EditorBuildSettings.scenes.Where(s => s.enabled).Select(s => s.path).ToArray(),
        locationPathName = "Builds/Android/game.aab", target = BuildTarget.Android };
    if (BuildPipeline.BuildPlayer(opts).summary.result != BuildResult.Succeeded)
        throw new System.Exception("Android build failed");
}
```

CLI invocation (exit code non-zero = failure; read the log):

```bash
"$UNITY_EXE" -batchmode -quit -projectPath "$PROJECT" \
  -executeMethod BuildScript.BuildAndroid -buildTarget Android \
  -logFile "$PROJECT/Logs/android-build.log"
```

**AAB vs APK:** Google Play requires an **AAB**; APK is only for sideload or direct
device install. **Keystore rules:** never commit a keystore or its passwords to VCS
(`.gitignore` the file, keep passwords in CI secrets, inject at build time), and back it
up out of band. A lost **upload** key can be reset by Google Play; a lost **app signing**
key on the legacy self-managed model is unrecoverable and orphans the listing. Enable
**Play App Signing** so Google holds the signing key and only the upload key is yours.

Full script (target-SDK line, error handling) and the Editor-menu fallback are in
[../../references/unity-store-build-detail.md](../../references/unity-store-build-detail.md)
(sections "Android: batchmode build script", "Android: CI invocation"). Target SDK, Data
Safety, and Play policy live in **android-compliance**.

## Step 3: iOS, scripted (preferred)

Unity emits an Xcode project, not an IPA. Two stages.

**Stage A, Unity generates the Xcode project** (bundle ID matches the App Store Connect
record, backend IL2CPP, output path a **directory**):

```bash
"$UNITY_EXE" -batchmode -quit -projectPath "$PROJECT" \
  -executeMethod BuildScript.BuildiOS -buildTarget iOS \
  -logFile "$PROJECT/Logs/ios-unity.log"
```

Output: `Builds/iOS/` with `Unity-iPhone.xcworkspace`.

**Stage B, Xcode archives and exports the IPA** (macOS + Xcode; signing identity and
provisioning profile must already be in the keychain):

```bash
xcodebuild archive -workspace "Builds/iOS/Unity-iPhone.xcworkspace" \
  -scheme "Unity-iPhone" -configuration Release \
  -archivePath "Builds/iOS/game.xcarchive"
xcodebuild -exportArchive -archivePath "Builds/iOS/game.xcarchive" \
  -exportPath "Builds/iOS/export" -exportOptionsPlist "CI/ExportOptions.plist"
```

`ExportOptions.plist` tells `-exportArchive` how to sign and package (`method` =
`app-store`, `teamID`, signing style); it must match the profile's distribution type or
export fails. Full `BuildiOS()`, the commands, and a minimal `ExportOptions.plist` are in
[../../references/unity-store-build-detail.md](../../references/unity-store-build-detail.md)
(sections "iOS: Unity Xcode project generation script", "iOS: xcodebuild archive and
export IPA", "ExportOptions.plist (App Store minimum)"). Privacy Manifest and store
metadata live in **ios-store-compliance**.

## Step 4: Failure modes

| Symptom | Cause | Fix |
| --- | --- | --- |
| `xcodebuild` export fails, "no matching provisioning profile" / "doesn't include signing certificate" | Profile does not match bundle ID, team, or `method` in ExportOptions.plist | Align bundle ID + `teamID` + `method`; refresh the profile in the keychain; confirm the distribution cert is present |
| Signing fails, "keystore was tampered with, or password was incorrect" | Wrong keystore password/alias, or a corrupted/truncated keystore (bad copy, LFS pointer) | Re-verify env-injected passwords; restore the keystore from backup; `keytool -list -keystore` to confirm it opens |
| Cannot sign the release at all, keystore missing | Keystore lost, was only in VCS-ignored local state | Upload key: request a reset in Play Console. Legacy self-managed signing key: unrecoverable, migrate the listing to Play App Signing going forward |
| IL2CPP build fails on CI, "Android NDK not found" / toolchain error | NDK/SDK path not set on the runner, or version mismatch with the Unity install | Install the exact NDK the Unity version expects; set `ANDROID_NDK_ROOT`/SDK paths for the batchmode process |
| IL2CPP C++ compile killed / OOM on CI | IL2CPP is memory-hungry; runner has too little RAM or swap | Use a larger runner (8GB+); reduce parallel `il2cpp` jobs; ensure swap is enabled |
| Gradle build fails, "plugin requires Gradle X" / AGP mismatch | Unity's bundled Gradle/AGP drifted from a custom `mainTemplate.gradle` or an installed Gradle | Use Unity's bundled Gradle, or pin the wrapper to the version Unity expects; reconcile custom Gradle templates |
| iOS archive succeeds but the IPA is unsigned | Export step ran without a valid profile/identity in the keychain | See Step 5 verify; re-import the distribution cert and profile, re-run `-exportArchive` |

## Step 5: Verify the artifact is store-ready

Existence and non-zero size are not enough; check the signature.

```bash
# Android AAB: exists, non-zero, and signed (v2/v3 block present)
ls -lh Builds/Android/game.aab
jarsigner -verify -verbose Builds/Android/game.aab   # or: apksigner verify --verbose <aab-or-apk>

# iOS IPA: exists and contains an embedded provisioning profile (else it is unsigned)
ls -lh Builds/iOS/export/*.ipa
unzip -l Builds/iOS/export/*.ipa | grep "embedded.mobileprovision" \
  || echo "UNSIGNED: re-check signing identity and provisioning profile"
```

A green signature check plus a `Build succeeded` log with exit code `0` is the proof.
Full notes: [../../references/unity-store-build-detail.md](../../references/unity-store-build-detail.md)
(section "Artifact verification").

## Outbound checkpoint

Local work needs no approval. Outbound here (uploading an AAB to the Play Console with its
target track, or an archive/IPA to App Store Connect / TestFlight via notarytool,
Transporter, or fastlane): stop, present exactly what would go out, and ask the operator
for an explicit "yes" first.

## References

- Full code, ExportOptions, and verification: [../../references/unity-store-build-detail.md](../../references/unity-store-build-detail.md)
- Unity: build from the command line, https://docs.unity3d.com/6000.4/Documentation/Manual/build-command-line.html
- Unity: BuildPipeline.BuildPlayer, https://docs.unity3d.com/ScriptReference/BuildPipeline.BuildPlayer.html
- Google Play App Signing, https://support.google.com/googleplay/android-developer/answer/9842756
- Apple: exporting a signed archive, https://developer.apple.com/documentation/xcode/distributing-your-app-for-beta-testing-and-releases
