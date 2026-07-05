---
name: android-shared-composables
description: "This skill should be used when the user asks to \"extract a reusable composable\", \"pull this UI into a shared component\", \"make a design-system component\", \"add a slot to this composable\", \"deduplicate Compose UI\", \"this Composable takes too many params\", \"why isn't my composable skippable\", \"make this composable stable\", \"fix an unstable lambda param\", or wants to refactor copy-pasted Jetpack Compose UI into a reusable, slot-based component with a clean, recomposition-stable API."
version: 0.2.0
---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# Android shared composables

Extract duplicated Jetpack Compose UI into a reusable, stateless, slot-based component with an API that matches the official Compose guidelines and stays skippable across recomposition. Apply when the same UI shape appears in 2+ places, or a single composable has grown too many parameters.

## When to extract (and when NOT to)
- Extract when the **same visual shape** repeats in 2+ call sites, or a screen mixes layout + business logic.
- Do NOT extract single-use UI "for later": premature shared components ossify the wrong API. Keep it local, inline it, extract on the real second use. Extract on the second occurrence when the duplication is the **same knowledge** (identical semantics); for merely look-alike UI wait for the third (rule of three). See the reusability judgment in `adlc-core` (reusability skill) for the same rule of three.
- A shared component must solve **one** problem. If it needs many flags to cover variants, split it into smaller building blocks instead.

## The extraction checklist (apply in order)

1. **Name it as a PascalCase noun.** `ProfileCard`, `SectionHeader`: never `drawX`/`renderX`/`showX`.
2. **Make it stateless, hoist all state.** Accept state as params; emit changes via callbacks (state down, events up). Never `remember { mutableStateOf(...) }` internal UI state in a reusable component; the caller owns it.
3. **Use slots for caller-owned content.** Replace hardcoded children with `@Composable () -> Unit` lambdas. A single main slot is named `content` and placed **last** so it reads as a trailing lambda. Multiple slots get descriptive names (`leading`, `trailing`, `header`, `footer`, `actions`) with `= {}` defaults when optional.
4. **First optional param is `modifier: Modifier = Modifier`.** Apply it to the **outermost** layout node, exactly once, before any internal modifiers.
5. **Order params:** required data → required callbacks (`onClick`, `onValueChange`) → optional params (with defaults) → `modifier` → trailing `content` slot.
6. **Prefer name prefixes over a `style` enum.** Expose `PrimaryButton`/`OutlinedButton`, not `Button(style = ...)`. Variants that diverge structurally are separate composables.
7. **Pull values from design-system tokens**, not literals. Use the project's theme (`Theme.colors`, `Theme.typography`, `Theme.spacing` / `MaterialTheme.*`), no hardcoded `Color(0x...)`, `16.dp`, or raw strings (use string resources).
8. **Add an `@Preview`** (and a preview per meaningful variant/state) so the component renders in tooling and review.

## Canonical shape

```kotlin
@Composable
fun ListItemRow(
    title: String,                              // required data
    onClick: () -> Unit,                        // required callback
    selected: Boolean = false,                  // optional, defaulted
    leading: @Composable () -> Unit = {},       // optional slot
    modifier: Modifier = Modifier,              // first optional; outermost node
    content: @Composable () -> Unit,            // main slot, trailing
)
```

## Stability and recomposition (make it skippable)

A reusable component is recomposed often, so it must **skip** when its inputs are unchanged. Compose skips a composable only when every parameter is stable (or unchanged and comparable). Strong Skipping mode is **on by default** since Compose Compiler 1.5.4+ (bundled with Kotlin 2.0+), so composables with unstable params can now skip when their instances are referentially equal, but relying on that hides real instability. Fix the types, do not lean on Strong Skipping.

What makes a param stable:
- **Stable by construction:** primitives, `String`, `enum`, function types, and any type the compiler infers stable (all `val`, stable-typed properties).
- **`@Immutable`:** promise the object never changes after construction (public properties are effectively final and deeply immutable). Use for value/data classes you fully control. Breaking the promise is a correctness bug (stale UI).
- **`@Stable`:** weaker promise: the object may change, but changes are observable via Compose snapshot state, and `equals` is consistent. Use for holder types built on `mutableStateOf`.
- **Unstable by default:** `List`/`Set`/`Map` (interfaces, could be a mutable impl), classes from modules the compiler cannot see (no metadata), and any `var` of an unstable type.

Unstable-lambda pitfalls:
- A **method reference** (`onClick = viewModel::submit`) can allocate a new instance per recomposition and defeat skipping. Prefer a **remembered lambda** (`val onClick = remember { { viewModel.submit() } }`) or a plain lambda that captures only stable values.
- A lambda that captures an **unstable** value is itself unstable. Hoist the value or wrap it.

Stable collections:
- Prefer `kotlinx.collections.immutable` (`ImmutableList`, `PersistentList`) for list params: the compiler treats them as stable. Convert at the boundary with `.toImmutableList()`.
- Or annotate a wrapper `@Immutable data class Rows(val items: List<Row>)`, or enable the compiler's stability-configuration file to mark a known-immutable third-party type stable.

### Before / after (unstable param made stable)

```kotlin
// BEFORE: List param is unstable → ListSection never skips, recomposes every frame
@Composable
fun ListSection(rows: List<Row>, onSelect: (Row) -> Unit) { /* ... */ }

// caller: new lambda instance every recomposition, also unstable
ListSection(rows = uiState.rows, onSelect = { viewModel.select(it) })
```

```kotlin
// AFTER: immutable collection + hoisted stable callback → skippable
@Composable
fun ListSection(rows: ImmutableList<Row>, onSelect: (Row) -> Unit) { /* ... */ }

// caller
val onSelect = remember(viewModel) { viewModel::select }   // stable reference
ListSection(rows = uiState.rows.toImmutableList(), onSelect = onSelect)
```

### Verify skippable/restartable with compiler reports
Turn on Compose compiler metrics and read the report; do not eyeball it.

```
# build.gradle(.kts): enable reports for this module
./gradlew :<module>:assembleRelease \
  -Pandroidx.compose.compiler.reports.enabled=true \
  -Pandroidx.compose.compiler.metrics.enabled=true
```

(Older setups pass `-P` with `plugin:androidx.compose.compiler.plugins.kotlin:reportsDestination=...`; match the project's Compose Compiler Gradle plugin config.) The report lands in `<module>/build/compose_compiler/`. Open `<module>-composables.txt` and confirm the target reads `restartable skippable fun ListSection`. If it says `restartable fun` without `skippable`, a param is unstable, `<module>-classes.txt` lists each type as `stable`/`unstable`; fix the flagged one and re-run.

## Parameter-count discipline
- Too many params is a design smell, not a formatting problem. Hoist state so the component takes fewer, plainer inputs.
- Group related config into an `@Immutable` config/state object (`data class RowStyle(...)`) instead of 6 loose flags. One stable object beats six params and helps skipping.
- If params still sprawl, the component is doing too much: split it (see "solve one problem" above).

## Where it lives (module rules)
- Shared UI belongs in the design-system / common-ui module both callers depend on; a component used by only one feature stays in that feature's `-impl`. Never copy it across modules.
- For the `-api`/`-impl` split and where module-level UI lives, see `android-module-scaffolder`.

## Anti-patterns to flag
- `modifier` missing, not first-optional, or applied to an inner node instead of the root.
- Internal `mutableStateOf` in a component meant to be reused (breaks hoisting/testability).
- A `style`/`variant` enum that switches large structural branches, split into prefixed composables.
- Passing a ViewModel, navigation controller, or domain model into a leaf UI component, pass plain data + lambdas.
- Raw `List`/`Map` params or per-recomposition method-reference callbacks that silently break skipping.
- Hardcoded colors/dimens/strings instead of theme tokens and resources.

## Verify
- `./gradlew :<module>:compileDebugKotlin` passes.
- `./gradlew spotlessApply && ./gradlew spotlessCheck` clean.
- Compose compiler report shows the component `restartable skippable` (see the stability section).
- Each `@Preview` renders. If the project has screenshot/Paparazzi tests, run the module's: `./gradlew :<module>:testDebugUnitTest`.
- Confirm every former call site now uses the shared component and no duplicated copy remains.

## References
- See [../../references/android-design-system.md](../../references/android-design-system.md) (loaded on demand) for the design-system conventions it covers: pick-components-by-intent, tokens/strings over literals, the promote-on-second-use / rule-of-three rule, and the previewable-and-accessible contract.
- Android Developers: Style guidelines for Jetpack Compose APIs: https://developer.android.com/develop/ui/compose/api-guidelines
- Android Developers: Compose stability + fixing recomposition: https://developer.android.com/develop/ui/compose/performance/stability
- androidx, Component API guidelines (slots, modifier, naming): https://android.googlesource.com/platform/frameworks/support/+/androidx-main/compose/docs/compose-component-api-guidelines.md
