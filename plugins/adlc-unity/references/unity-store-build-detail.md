<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
Consumed by the `unity-store-build` skill. Load on demand; do not load independently.

## Android: batchmode build script

```csharp
// Editor/BuildScript.cs
using UnityEditor;
using UnityEditor.Build.Reporting;

public static class BuildScript
{
    public static void BuildAndroidAAB()
    {
        // Signing -- read from env to keep secrets out of source
        PlayerSettings.Android.useCustomKeystore        = true;
        PlayerSettings.Android.keystoreName             = System.Environment.GetEnvironmentVariable("KEYSTORE_PATH");
        PlayerSettings.Android.keystorePass             = System.Environment.GetEnvironmentVariable("KEYSTORE_PASS");
        PlayerSettings.Android.keyaliasName             = System.Environment.GetEnvironmentVariable("KEY_ALIAS");
        PlayerSettings.Android.keyaliasPass             = System.Environment.GetEnvironmentVariable("KEY_ALIAS_PASS");

        // Architectures and backend (IL2CPP + ARM64 required for Play)
        PlayerSettings.SetScriptingBackend(NamedBuildTarget.Android, ScriptingImplementation.IL2CPP);
        PlayerSettings.Android.targetArchitectures      = AndroidArchitecture.ARM64 | AndroidArchitecture.ARMv7;

        // Target SDK: set to match the compliance requirement (see android-compliance skill)
        // PlayerSettings.Android.targetSdkVersion = AndroidSdkVersions.AndroidApiLevel35;

        var options = new BuildPlayerOptions
        {
            scenes           = EditorBuildSettings.scenes.Select(s => s.path).ToArray(),
            locationPathName = "Builds/Android/game.aab",
            target           = BuildTarget.Android,
            options          = BuildOptions.None,
        };
        EditorUserBuildSettings.buildAppBundle = true;

        var report = BuildPipeline.BuildPlayer(options);
        if (report.summary.result != BuildResult.Succeeded)
            throw new System.Exception($"Android build failed: {report.summary.result}");
    }
}
```

## Android: CI invocation

```bash
/path/to/Unity -batchmode -quit \
  -projectPath "$PROJECT_PATH" \
  -executeMethod BuildScript.BuildAndroidAAB \
  -buildTarget Android \
  -logFile "$LOG_PATH/android-build.log"
```

Output: `Builds/Android/game.aab`. Confirm file exists and is non-zero before proceeding.

## iOS: Unity Xcode project generation script

```csharp
// Editor/BuildScript.cs (add alongside Android method)
public static void BuildiOS()
{
    // Bundle ID must match your App Store Connect record
    PlayerSettings.SetApplicationIdentifier(NamedBuildTarget.iOS, "com.example.game");
    PlayerSettings.SetScriptingBackend(NamedBuildTarget.iOS, ScriptingImplementation.IL2CPP);

    var options = new BuildPlayerOptions
    {
        scenes           = EditorBuildSettings.scenes.Select(s => s.path).ToArray(),
        locationPathName = "Builds/iOS",   // directory, not a file
        target           = BuildTarget.iOS,
        options          = BuildOptions.None,
    };

    var report = BuildPipeline.BuildPlayer(options);
    if (report.summary.result != BuildResult.Succeeded)
        throw new System.Exception($"iOS export failed: {report.summary.result}");
}
```

## iOS: Unity batchmode invocation

```bash
/path/to/Unity -batchmode -quit \
  -projectPath "$PROJECT_PATH" \
  -executeMethod BuildScript.BuildiOS \
  -buildTarget iOS \
  -logFile "$LOG_PATH/ios-unity.log"
```

Output: `Builds/iOS/` containing `Unity-iPhone.xcworkspace` (or `.xcodeproj`).

## iOS: xcodebuild archive and export IPA

Requires macOS with Xcode installed. Signing identity and provisioning profile must be available in the macOS keychain before running.

```bash
# 1. Archive
xcodebuild archive \
  -workspace "Builds/iOS/Unity-iPhone.xcworkspace" \
  -scheme "Unity-iPhone" \
  -configuration Release \
  -archivePath "Builds/iOS/game.xcarchive" \
  CODE_SIGN_IDENTITY="Apple Distribution: Your Team Name" \
  PROVISIONING_PROFILE_SPECIFIER="your-provisioning-profile-name" \
  | tee "$LOG_PATH/xcodebuild-archive.log"

# 2. Export IPA (ExportOptions.plist must match your distribution method)
xcodebuild -exportArchive \
  -archivePath "Builds/iOS/game.xcarchive" \
  -exportPath "Builds/iOS/export" \
  -exportOptionsPlist "CI/ExportOptions.plist" \
  | tee "$LOG_PATH/xcodebuild-export.log"
```

Output: `Builds/iOS/export/<GameName>.ipa`.

## ExportOptions.plist (App Store minimum)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>method</key><string>app-store</string>
  <key>teamID</key><string>YOUR_TEAM_ID</string>
  <key>uploadBitcode</key><false/>
  <key>compileBitcode</key><false/>
</dict></plist>
```

## Artifact verification

```bash
# Android: confirm AAB exists and is reasonably sized
ls -lh Builds/Android/game.aab

# iOS: confirm IPA exists; inspect with unzip to check it is signed
ls -lh Builds/iOS/export/*.ipa
unzip -l Builds/iOS/export/*.ipa | grep "embedded.mobileprovision"
```

If `embedded.mobileprovision` is absent, the IPA is unsigned. Re-check the signing identity and provisioning profile in the keychain.
