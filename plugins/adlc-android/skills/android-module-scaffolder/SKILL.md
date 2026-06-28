---
name: android-module-scaffolder
description: >
  This skill should be used when the user asks to "scaffold a new Android feature module",
  "create an api/impl module pair", "add a new feature module wired for DI", "set up a
  -api -impl split", "generate a Gradle module for a feature", "bootstrap a new Android
  module", or "wire a new module into the DI graph". Produces a decoupled -api/-impl
  feature module that communicates through interfaces only.
version: 0.1.0
---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# Android module scaffolder

Scaffold a new feature as an `-api` / `-impl` module pair, wired into the DI graph, where
features communicate through interfaces in the `-api` module only.

## When to use

The user wants a new feature module that other features can depend on without coupling to
its implementation. The output is two Gradle modules plus the app-module wiring needed to
enter the DI graph.

## Step 1: Detect conventions before generating anything

Never assume the project's stack. Inspect first, match what exists:

```
# Module naming + structure of an existing feature pair
ls -d */*-api */*-impl 2>/dev/null | head
# DI framework in use (read, do not guess)
grep -rIl --include=*.kts --include=*.gradle -e 'anvil' -e 'hilt' -e 'dagger' -e 'metro' -e 'koin' . | head
# How an existing -impl declares its module + dependencies
cat $(ls */*-impl/build.gradle* | head -1)
# How existing modules are registered (settings + app build file)
grep -n 'include' settings.gradle* | tail
```

Record: module path style (`feature/feature-api`), DI framework, scope names, plugin
ids, and the version-catalog aliases the project uses. Mark anything you cannot determine
`unknown` and ask, never invent plugin ids or scope names.

## Step 2: Generate the `-api` module (contracts only)

The `-api` module holds interfaces and data classes. No implementation, no DI framework,
no Android resources.

- `<feature>-api/build.gradle(.kts)`: pure Kotlin/Android-library, **no** DI plugin.
- `<feature>-api/src/main/kotlin/.../<Feature>.kt`: the public interface + models.

```kotlin
// <feature>-api
interface <Feature> {
    suspend fun doThing(id: String): Result<Thing>
}

data class Thing(val id: String, val name: String)
```

Rule: an `-api` module must **not** depend on another feature's `-api` or `-impl`
(narrow, documented exceptions only, e.g. a navigation or feature-toggle api).

## Step 3: Generate the `-impl` module (implementation + DI binding)

- `<feature>-impl/build.gradle(.kts)`: applies the DI plugin; depends on its own `-api`
  and on **other features' `-api` only**, never another `-impl`.
- `<feature>-impl/src/main/kotlin/.../Real<Feature>.kt`: implements the interface and
  binds it into the detected scope.
- UI resources (layouts, drawables, strings) live here. Name strings by feature:
  `strings-<feature>.xml`, not `strings.xml`.

```kotlin
// <feature>-impl, binding idiom depends on the DETECTED framework (see Step 1)
@ContributesBinding(<DetectedScope>::class)   // Anvil/Dagger
class Real<Feature> @Inject constructor(
    // collaborators injected from other features' -api
) : <Feature> {
    override suspend fun doThing(id: String): Result<Thing> = ...
}
```

Model fallible operations with `Result<T>` / sealed classes, do not throw across module
boundaries or return null-on-failure.

## Step 4: Wire into the DI graph

A new `-impl` does nothing until it is registered. Both modules must be added to
`settings.gradle(.kts)`, and the **app module must depend on the `-impl`** so its
bindings enter the merged component. Add the version-catalog/project deps the same way
existing `-impl` modules are wired (Step 1 output is the template).

## Step 5: Verify (pass/fail, not "looks right")

```
./gradlew :<feature>-impl:assembleDebug
./gradlew :<feature>-impl:testDebugUnitTest   # if a test was generated
./gradlew spotlessApply && ./gradlew spotlessCheck
```

A clean assemble proves the module compiles and the binding is discoverable. If the DI
processor reports "could not find dagger component" or an unresolved binding, the entry
point is missing the right `@InjectWith(...)`, the `-impl` is not on the app module's
classpath, or the scope name is wrong, fix and re-run. Do not claim done without a green
build.

## Guardrails

- `-impl` -> `-impl` dependency is forbidden. If two features interact, one exposes an
  interface in its `-api`; the other injects it.
- No business logic in Activities/Fragments; no `GlobalScope`; no hardcoded user-facing
  strings.
- This skill writes local files and runs local builds only, it performs **no** outbound
  action. Pushing the branch or opening a PR is outbound: it happens only after the
  operator gives an explicit "yes".

## Anvil/Dagger note

See [references/android-architecture.md](references/android-architecture.md) for the canonical DI scope table and binding annotations.

## References

- See [references/android-architecture.md](references/android-architecture.md), [references/android-naming.md](references/android-naming.md),
  and [references/android-build-gradle.md](references/android-build-gradle.md) (loaded on demand) for the full conventions: the canonical
  Anvil/Dagger scope table, module/file naming, and version-catalog + convention-plugin rules.
- Android Developers: Common modularization patterns (api/impl dependency-inversion
  rules, feature-module dependency direction):
  https://developer.android.com/topic/modularization/patterns
- Android Developers: Using Dagger in multi-module apps:
  https://developer.android.com/training/dependency-injection/dagger-multi-module
