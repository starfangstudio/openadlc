---
name: android-build-commands
description: >-
  Module-scoped gradlew task reference for Android. Triggers: "build the app", "assemble
  the APK", "make a debug/release build", "build an AAB", "install on device/emulator",
  "run the unit/instrumented tests", "run lint", "clean the build", "what gradle command
  builds/tests this module". Covers assemble/install/bundle/test/connectedAndroidTest/
  lint/clean plus the speed and single-test flags to verify a change without a full rebuild.
version: 0.1.0
---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# Android build commands

Drive Gradle from the command line via the `./gradlew` wrapper (never a system
`gradle`). Default to **module-scoped** tasks (`:module:task`), building the
whole project is slow and usually unnecessary for verifying one change.

## Detect first

Run from the repo root (where `gradlew` lives). Before guessing a task name:

```bash
./gradlew :module-name:tasks            # tasks available for one module
./gradlew projects                      # list module paths (the :a:b form)
```

Variant tasks are camel-cased from build types and flavors: a `demo` flavor +
`debug` type produces `assembleDemoDebug`, `installDemoDebug`,
`testDemoDebugUnitTest`. Substitute the project's real variant for `Debug` below.

## Task reference (prefer the module-scoped form)

| Goal | Command |
|---|---|
| Compile + package debug APK | `./gradlew :app:assembleDebug` |
| Package release APK | `./gradlew :app:assembleRelease` |
| Build + install on device/emulator | `./gradlew :app:installDebug` |
| Build debug app bundle (AAB) | `./gradlew :app:bundleDebug` |
| Build release app bundle (AAB) | `./gradlew :app:bundleRelease` |
| Run local JVM unit tests | `./gradlew :module:testDebugUnitTest` |
| Run instrumented tests (needs device) | `./gradlew :module:connectedDebugAndroidTest` |
| Run Android lint | `./gradlew :module:lintDebug` |
| Delete build outputs | `./gradlew clean` |

Outputs land in `module/build/outputs/` (APK: `outputs/apk/`, AAB:
`outputs/bundle/`). Debug APKs are auto-signed with the debug key; release
builds require a configured signing config.

## Verify-a-change shortcuts

```bash
# Single test class or method: fastest feedback loop
./gradlew :module:testDebugUnitTest --tests com.example.MyClass
./gradlew :module:testDebugUnitTest --tests "com.example.MyClass.myMethod"

# Skip network resolution when deps are already cached
./gradlew :module:testDebugUnitTest --offline

# See why a build failed
./gradlew :app:assembleDebug --stacktrace        # or --info for more
```

After a config change, a stale daemon can cause phantom failures, re-run; if it
persists, `./gradlew --stop` then retry. Do not add `--no-daemon` by default
(it is slower).

## Rules

- **Scope every task to a module** when you know the module, full-project
  `./gradlew assembleDebug` and `./gradlew test` are last resorts.
- **Verify with a pass/fail command**, not by reading code. A green
  `:module:testDebugUnitTest` is the proof a change works.
- **`connectedAndroidTest` needs a running emulator/device**: check `adb devices`
  first; otherwise it fails with "no connected devices".
- **Builds and tests are local**: they run on this machine and need no approval.
  Publishing artifacts (`publish*`, `uploadCrashlytics`, Play/CI uploads) IS an
  outbound action: stop and get the operator's explicit yes first.

## Example (modular repo)

This codebase scopes tests and uses Spotless for formatting:

```bash
./gradlew :app-tracking-protection-impl:testDebugUnitTest
./gradlew spotlessApply && ./gradlew spotlessCheck
```

## References

- See [references/android-testing.md](references/android-testing.md) (loaded on demand) for the full
  test strategy: the pyramid, what to test at each level, and the screenshot/e2e conventions.
- Build your app from the command line: Android Developers:
  https://developer.android.com/build/building-cmdline
- Test from the command line: Android Developers:
  https://developer.android.com/studio/test/command-line
