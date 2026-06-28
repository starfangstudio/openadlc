---
name: android-navigation
description: "This skill should be used when the user asks to \"add a screen\", \"navigate between screens\", \"pass arguments to a destination\", \"set up Navigation Compose\", \"make navigation type-safe\", \"wire up a deep link\", \"launch an activity from another feature\", or \"decouple navigation across modules\" in an Android app. Covers type-safe Navigation Compose 2.8 (@Serializable routes) and the decoupled cross-module activity-starter pattern."
version: 0.1.0
---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# Android Navigation

Two layers, picked by where the boundary is:

- **Within one feature / Compose app** -> type-safe Navigation Compose 2.8 (`@Serializable` routes).
- **Across feature modules** (`-impl` must never depend on another `-impl`) -> a decoupled activity-starter that resolves a destination from a marker params type. Keeps the DI graph acyclic.

Detect what the project already uses before adding anything. Match it. Do not introduce a second navigation system.

## Type-safe Navigation Compose 2.8

Requires `androidx.navigation:navigation-compose:2.8.0+` and the Kotlin Serialization plugin (`kotlin("plugin.serialization")`).

1. Define routes as `@Serializable` types, `object` for no-arg, `data class` for args. Keep them in the feature, not shared globally.

```kotlin
@Serializable object Home
@Serializable data class Profile(val id: String)
```

2. Build the graph with typed `composable<T>`; navigate with a route instance.

```kotlin
NavHost(navController, startDestination = Home) {
    composable<Home> {
        HomeScreen(onOpenProfile = { id -> navController.navigate(Profile(id)) })
    }
    composable<Profile> { entry ->
        val profile: Profile = entry.toRoute()   // type-safe args
        ProfileScreen(profile.id)
    }
}
```

3. Read args in a ViewModel from `SavedStateHandle`: never thread the `NavController` into the ViewModel.

```kotlin
class ProfileViewModel(state: SavedStateHandle) : ViewModel() {
    private val profile = state.toRoute<Profile>()
}
```

Rules:
- Routes flow down, events flow up. Pass lambdas (`onOpenProfile`) into composables, do not pass the `NavController` down the tree.
- Custom argument types need a custom `NavType`; prefer primitives/`String` IDs and re-fetch in the destination over passing large objects.
- One `NavHost` owns the back stack. Nested graphs use a typed `navigation<T>` builder.

## Decoupled cross-module navigation (activity-starter)

When a feature must launch a screen owned by another module, the caller must not see the target `Activity`. Route through a single injected starter that maps a marker params type to its destination. This is the only sanctioned way to cross an `-impl` boundary.

Contract lives in a navigation `-api` module so every feature depends on the api, never on each other's `-impl`:

```kotlin
interface ActivityParams : Serializable        // marker for a destination's typed args

interface ActivityStarter {                     // injected; resolves params -> Activity
    fun start(context: Context, params: ActivityParams, options: Bundle? = null)
    fun startIntent(context: Context, params: ActivityParams): Intent?
    fun startForResult(context: Context, params: ActivityParams, launcher: ActivityResultLauncher<Intent>)
}
```

- Each destination defines its own `data class XParams(...) : ActivityParams` in **its own** `-api`. The caller injects `ActivityStarter`, builds the params, calls `start`. It never imports the target Activity.
- The owning `-impl` registers a mapper from its params type to its Activity, wired through DI so the starter can resolve it at runtime.
- Deep links resolve a destination by a stable string screen name + serialized arguments, not by importing a class.

Verify the boundary holds: grep the caller module for the target Activity's class name, it must not appear.

```bash
grep -rn "TargetActivity" <caller-impl>/src/main && echo "LEAK: caller references impl directly"
```

## Navigation 3 (emerging: do not adopt by default)

`androidx.navigation3` models the back stack as a mutable list (`NavDisplay` + a `NavBackStack`). It is **alpha** as of mid-2026. Do not migrate a production app to it. Mention it only if the user explicitly asks about Nav3 or is building a greenfield experiment that can tolerate alpha churn; otherwise use Navigation Compose 2.8.

## Verify

- `./gradlew :<module>:testDebugUnitTest`: destination/args tests pass.
- `./gradlew :<module>:assembleDebug`: graph compiles (typed routes fail at compile time, not runtime).
- Navigate the real flow (run the app) for any back-stack or deep-link change; a passing build does not prove the back stack behaves.
- `./gradlew spotlessApply && ./gradlew spotlessCheck`.

## Outbound checkpoint

Local work needs no approval. Outbound here (shipping a deep-link change that registers an externally reachable URL host): stop, present exactly what would go out, and wait for an explicit "yes" (global consent law).

## Activity-starter example

A `GlobalActivityStarter` is a production instance of the activity-starter pattern: `start`/`startIntent`/`startForResult` overloads, an `ActivityParams : Serializable` marker, `DeeplinkActivityParams(screenName, jsonArguments)`, and `ParamToActivityMapper` bindings contributed per `-impl`. Names above are generalized; map them onto whatever the target project calls its starter.

## References

- Type safety in Navigation Compose: Android Developers: https://developer.android.com/guide/navigation/design/type-safety
- Migrating to type-safe destinations: Android Developers: https://developer.android.com/guide/navigation/type-safe-destinations
- Navigation 3 (alpha): Android Developers: https://developer.android.com/guide/navigation/navigation-3
