<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
# Android Gradle build conventions

One source of truth for versions; shared build logic in convention plugins; no copy-pasted config across modules. Detect what the project already uses and stay idiomatic, only introduce these patterns in greenfield or when explicitly asked to migrate.

## Version catalog (`gradle/libs.versions.toml`)
- All dependency and plugin coordinates live in the catalog at `gradle/libs.versions.toml` (the default Gradle path, do not rename it). Modules reference type-safe accessors, never inline `"group:name:version"` strings.
- Four sections: `[versions]`, `[libraries]`, `[plugins]`, `[bundles]`. Group related deps that always ship together into a `[bundle]`.
- **Kebab-case** every alias (`androidx-core-ktx`, `android-application`), Gradle maps `-` to `.` for accessors (`libs.androidx.core.ktx`) and IDE completion works best this way.
- Pin one `version.ref` per logical version; never hardcode the same version twice. A version bump must be a one-line change in `[versions]`.
- In build files: `alias(libs.plugins.x)` for catalog plugins, `id("convention.x")` for local convention plugins. Add `apply false` in the root build file for plugins applied only in submodules.

```toml
[versions]
agp = "8.5.0"
ksp = "2.0.0-1.0.22"
coreKtx = "1.13.1"

[libraries]
androidx-core-ktx = { group = "androidx.core", name = "core-ktx", version.ref = "coreKtx" }

[plugins]
android-application = { id = "com.android.application", version.ref = "agp" }
ksp = { id = "com.google.devtools.ksp", version.ref = "ksp" }
```

## Convention plugins (`build-logic/`)
- Shared module config (Android + Kotlin options, common deps, lint, test setup) lives in convention plugins under an included `build-logic` build, **not** copy-pasted into each module's `build.gradle.kts`, and **not** in `buildSrc` (which invalidates the whole build cache on any change).
- Keep each plugin **single-responsibility and composable** (e.g. one for Android library, one for Compose, one for Hilt/DI, one for the DI framework). A module applies the few it needs.
- A module's `build.gradle.kts` should be short: apply convention plugins + declare its own deps. If you find yourself repeating config across modules, extract a convention plugin.
- New module = create its `build.gradle.kts` applying the right convention plugins, then register it for the build (explicit `include` in `settings.gradle.kts`, unless the project auto-discovers modules) and wire it into the DI graph (see `android-architecture.md`).

## KSP over KAPT
- Use **KSP** for annotation processing (Room, Moshi, Dagger/Hilt, Glide). KAPT is deprecated and in maintenance mode, it runs a slow Java apt stub-generation pass; KSP is Kotlin-native and markedly faster, with better incremental builds.
- Migrating a module: swap the `kapt(...)` dependency for `ksp(...)`, apply the KSP plugin, and confirm every processor on it supports KSP (most major ones do). Do not mix KSP and KAPT for the same processor.

## Build hygiene
- `strings-<feature>.xml` per feature, never a shared `strings.xml`: keeps modules decoupled and avoids merge collisions (see `android-naming.md`). Treat a stray hardcoded user-facing string as a build break: move it to the feature's resources.
- Run module-scoped, not whole-suite: `./gradlew :<module>:testDebugUnitTest --stacktrace`; format gate `./gradlew spotlessApply && ./gradlew spotlessCheck`.
- A new dependency goes through the catalog. A new outbound dependency is local-only work, but publishing, releasing, or pushing the change is outbound: get the operator's explicit yes first (see the consent law in the project CLAUDE.md).

## Example: large modular project
Feature-modular Anvil/Dagger codebases extend this with one convention plugin per concern (Android, Compose, Anvil/Dagger, Room) and auto-discover modules in `settings.gradle` (no manual `include`). A new `-impl` module still must be added to `app/build.gradle` to enter the DI graph, discovery and DI wiring are separate steps.

## References
- [Migrate your build to version catalogs, Android Developers](https://developer.android.com/build/migrate-to-catalogs)
- [Now in Android `build-logic` (convention plugins reference)](https://github.com/android/nowinandroid/tree/main/build-logic)
- [Migrate from kapt to KSP, Kotlin docs](https://developer.android.com/build/migrate-to-ksp)
