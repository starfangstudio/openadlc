---
name: android-shared-composables
description: "This skill should be used when the user asks to \"extract a reusable composable\", \"pull this UI into a shared component\", \"make a design-system component\", \"add a slot to this composable\", \"deduplicate Compose UI\", \"this Composable takes too many params\", or wants to refactor copy-pasted Jetpack Compose UI into a reusable, slot-based component with a clean API."
version: 0.1.0
---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# Android shared composables

Extract duplicated Jetpack Compose UI into a reusable, stateless, slot-based component with an API that matches the official Compose guidelines. Apply when the same UI shape appears in 2+ places, or a single composable has grown too many parameters.

## When to extract (and when not to)
- Extract when the **same visual shape** repeats in 2+ call sites, or a screen mixes layout + business logic.
- Do NOT extract on a single use "for later": premature shared components ossify the wrong API. Extract on the second occurrence when the duplication is the same knowledge (identical semantics); for merely look-alike UI wait for the third (rule of three, same rule as the design-system conventions).
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

## Where it lives (module rules)
- Shared UI belongs in the **design-system / common-ui module** (or the owning feature's `-impl` if used by only that feature). Never duplicate it across `-impl` modules.
- A composable used by multiple features goes in the shared UI module both depend on, not copied. See `android-architecture` rule for the `-api`/`-impl` split.
- Keep resources (strings, drawables) beside the component in its module; name string files by feature/component.

## Anti-patterns to flag
- `modifier` missing, not first-optional, or applied to an inner node instead of the root.
- Internal `mutableStateOf` in a component meant to be reused (breaks hoisting/testability).
- A `style`/`variant` enum that switches large structural branches, split into prefixed composables.
- Passing a ViewModel, navigation controller, or domain model into a leaf UI component, pass plain data + lambdas.
- Hardcoded colors/dimens/strings instead of theme tokens and resources.

## Verify
- `./gradlew :<module>:compileDebugKotlin` passes.
- `./gradlew spotlessApply && ./gradlew spotlessCheck` clean.
- Each `@Preview` renders. If the project has screenshot/Paparazzi tests, run the module's: `./gradlew :<module>:testDebugUnitTest`.
- Confirm every former call site now uses the shared component and no duplicated copy remains.

## Design-system note
In a design-system-driven codebase, prefer the project's design-system components (e.g. `ButtonPrimary`, `TextInput`) over raw Material/platform widgets, many such projects lint-fail on raw widgets. Pick by intent (primary/secondary/destructive), not by style flag.

## References
- See [references/android-design-system.md](../../references/android-design-system.md) (loaded on demand) for the full design-system conventions: pick-by-intent components, tokens over literals, and the promote-on-second-use rule.
- Android Developers: Style guidelines for Jetpack Compose APIs: https://developer.android.com/develop/ui/compose/api-guidelines
- androidx, Component API guidelines (slots, modifier, naming): https://android.googlesource.com/platform/frameworks/support/+/androidx-main/compose/docs/compose-component-api-guidelines.md
