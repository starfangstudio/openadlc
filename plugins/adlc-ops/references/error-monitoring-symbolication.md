<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
# Error monitoring: symbolication reference

Detail for iOS dSYM, Android ProGuard/R8, and Unity IL2CPP symbol uploads.
Consumed by the `error-monitoring` skill: do not load independently.

---

## iOS: dSYM upload (Sentry)

The Sentry wizard adds an Xcode build phase automatically:

```bash
sentry-wizard -i ios        # run once; adds build phase + .sentryclirc
```

Manual upload when CI strips the build phase:

```bash
sentry-cli --auth-token $SENTRY_AUTH_TOKEN debug-files upload \
  --org <org-slug> --project <project-slug> \
  path/to/dSYMs
```

For Xcode Cloud / GitHub Actions: pass `SENTRY_AUTH_TOKEN`, `SENTRY_ORG`, `SENTRY_PROJECT`
as secrets; the build phase script reads them automatically.

Crashlytics alternative (iOS): add the `upload-symbols` run script in Xcode build phases
(added automatically by `pod install` / SPM integration):

```
"${PODS_ROOT}/FirebaseCrashlytics/upload-symbols" \
  -gsp "${PROJECT_DIR}/GoogleService-Info.plist" \
  -p ios "${DWARF_DSYM_FOLDER_PATH}/${DWARF_DSYM_FILE_NAME}"
```

---

## Android: ProGuard/R8 mapping upload (Sentry)

The Sentry wizard writes `sentry.properties` (auto-gitignored) and patches `build.gradle`:

```bash
sentry-wizard -i android
```

What the wizard adds to `app/build.gradle`:

```groovy
plugins {
    id("io.sentry.android.gradle") version "4.x.x"
}

sentry {
    autoUploadProguardMapping = true
    autoUploadNativeSymbols   = true   // NDK symbols
    org   = "<org-slug>"
    projectName = "<project-slug>"
}
```

`sentry.properties` holds the auth token; keep it out of version control.

Crashlytics alternative (Android): add `mappingFileUploadEnabled true` under the release
build type in `build.gradle`; the Crashlytics Gradle plugin uploads automatically.

---

## Unity: IL2CPP / native symbols (Sentry)

Configure once via **Tools > Sentry** in the Unity Editor:
- Auth Token
- Organization Slug
- Project Name

The SDK uploads C# IL2CPP line-mapping files and native crash symbols (iOS dSYM,
Android .so) automatically at Unity build time.

Manual CLI fallback:

```bash
sentry-cli --auth-token <token> debug-files upload \
  --org <org-slug> --project <project-slug> \
  PATH_TO_SYMBOLS
```

IL2CPP line numbers require the "IL2CPP line numbers" option enabled in
**Tools > Sentry > Advanced**. Without it, C# stack frames show IL offsets, not
source lines.

---

## Verify symbolication

After a test crash, confirm in the Sentry/Crashlytics dashboard:
- Stack frames show class + method names (not `0x00000001004c3a80`)
- File names and line numbers appear for C# frames (Unity/IL2CPP)
- No "Missing debug information" warning on the event

If frames are unsymbolicated: re-check that the auth token has `project:write` scope
and that the correct build UUID appears under **Settings > Debug Files**.

---

## References

- Sentry iOS dSYM upload: https://docs.sentry.io/platforms/apple/guides/ios/dsym/
- Sentry Android Gradle plugin: https://docs.sentry.io/platforms/android/
- Sentry Unity native support + IL2CPP: https://docs.sentry.io/platforms/unity/native-support/
- Sentry CLI debug-files upload: https://docs.sentry.io/cli/dif/
- Crashlytics iOS dSYM upload: https://firebase.google.com/docs/crashlytics/ios/get-deobfuscated-reports
- Crashlytics Android mapping upload: https://firebase.google.com/docs/crashlytics/get-deobfuscated-reports
- Firebase Crashlytics Unity: https://firebase.google.com/docs/crashlytics/unity/get-started
