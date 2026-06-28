<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
# Android Architecture Rules

Adapted from a privacy-focused browser's production conventions (a feature-modular, Anvil/Dagger codebase). Apply the *patterns*; match whatever the target project actually uses.

## Core principle: decoupling over everything
Features communicate through `-api` modules only. An `-impl` module must never depend on another `-impl` module. If two features interact, one exposes an interface in its `-api`, the other injects it. This keeps the DI graph clean and prevents circular dependencies.

## Module structure
Every feature follows the `-api` / `-impl` split:
```
my-feature/
  my-feature-api/    # interfaces, data classes, no implementation, no DI framework
  my-feature-impl/   # implementation, UI, DI bindings, resources
```
- `-impl` depends on its own `-api` and on other features' `-api` only, never another `-impl`.
- `-api` modules must not depend on other `-api` modules (narrow, documented exceptions only, e.g. a navigation or feature-toggle api).
- UI resources (layouts, drawables, strings) live inside `-impl`, not a separate UI module.
- Name string files by feature: `strings-my-feature.xml`, not `strings.xml`.
- Module discovery is project-dependent: some projects auto-discover modules via `settings.gradle` (e.g. scanning 2 levels deep, no manual `include` needed); others list them explicitly. Independently, a new `-impl` must still be added to `app/build.gradle` to enter the DI/Dagger graph. Don't conflate "discovered by settings.gradle" with "wired for DI".

## Dependency injection
Detect the project's framework first and stay idiomatic. Defaults: **Hilt** for app-level greenfield; **Metro** for new KMP/modular; **Koin** for small/fast; **Anvil/Dagger** for large modular (the reference model below); **manual** for libraries.

### Anvil / Dagger scope reference (large-modular model)
| Scope | Use for |
|---|---|
| `AppScope` | App-lifetime singletons |
| `ActivityScope` | Activity-scoped (has activity context) |
| `FragmentScope` | ViewModels and Fragment-scoped things |
| `ViewScope` | Custom views needing injection |
| `ReceiverScope` / `ServiceScope` | BroadcastReceiver / Service |

- Use `@SingleInstanceIn(AppScope::class)`: **not** `@Singleton` (javax), which conflicts with the app component's scope.
- Bind with `@ContributesBinding(SomeScope::class)`; mark injectable Android entry points with `@InjectWith(SomeScope::class)`.
- `FragmentScope`/`ViewScope` parent to the Activity component (can access activity context); `ReceiverScope`/`ServiceScope` parent to the App component (no activity context).
- Debugging "could not find dagger component": the class is missing the right `@InjectWith(...)`, or its factory isn't in the expected `injectorFactoryMap`.

## State & errors
- Unidirectional state (MVI): expose UI state via `StateFlow`; events flow up, state flows down.
- Model errors with sealed classes / `Result<T>` for fallible operations, don't throw across module boundaries or return nullable-on-failure.
- No business logic in Activities/Fragments. No `GlobalScope`. No hardcoded user-facing strings.

## Design system
Prefer the project's design-system components over raw platform/Material widgets when one exists (many projects lint-fail on raw widgets). Pick components by intent (primary/secondary/destructive), not by style.
