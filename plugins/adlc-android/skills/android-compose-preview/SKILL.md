---
name: android-compose-preview
description: "This skill should be used when the user asks to \"add a Compose preview\", \"preview this composable\", \"generate @Preview for each state\", \"wire up PreviewParameterProvider\", \"make this screenshot-test ready\", \"add @PreviewTest\", or \"cover loading/error/empty states in previews\" for Jetpack Compose UI. Generates one @Preview + a PreviewParameterProvider that exercises every UI state, ready for Compose Preview Screenshot Testing."
version: 0.1.0
---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# Android Compose Preview + Screenshot Scaffolding

Generate `@Preview`s and a `PreviewParameterProvider` that drive every UI state of a composable, structured so the same previews become host-side screenshot tests with no rewrite.

## When to run
A composable renders distinct visual states (loading / content / empty / error, or varying data) and lacks previews, OR previews exist but cover only the happy path, OR the user wants screenshot coverage.

## Procedure

1. **Find the states.** Read the composable's parameters and its `StateFlow`/sealed UI-state type. Enumerate every visually distinct case (each sealed subtype; boundary data like empty list, long text, max count). List them back to the user before generating.

2. **Take a state-bearing parameter.** Preview a composable that accepts the UI state as a parameter (state hoisted out of the ViewModel). If the only entry point reads a ViewModel directly, preview the inner stateless composable instead, never construct a ViewModel in a preview.

3. **Write the provider.** One `PreviewParameterProvider<T>` whose entries are the states. Back `values` with a `List` for index access and override `getDisplayName` so each preview/screenshot is labeled by state, not index:

   ```kotlin
   class ProfileStatePreviewProvider : PreviewParameterProvider<ProfileState> {
       private val states = listOf(
           ProfileState.Loading,
           ProfileState.Content(User(name = "Elise", age = 30)),
           ProfileState.Content(User(name = "A very long display name that should wrap", age = 8)),
           ProfileState.Empty,
           ProfileState.Error("Network unreachable"),
       )
       override val values = states.asSequence()
       override fun getDisplayName(index: Int) =
           states.getOrNull(index)?.let { it::class.simpleName } ?: super.getDisplayName(index)
   }
   ```

4. **Write one parameterized preview.** A single `@Preview` consuming the provider produces one render per state. Wrap in the project's theme. Add `@PreviewTest` so the same function is collected by Compose Preview Screenshot Testing:

   ```kotlin
   @PreviewTest
   @Preview(showBackground = true)
   @Composable
   private fun ProfileScreenPreview(
       @PreviewParameter(ProfileStatePreviewProvider::class) state: ProfileState,
   ) {
       AppTheme { ProfileScreen(state = state, onRetry = {}) }
   }
   ```

5. **Add cross-cutting variants only when they matter.** For light/dark or font scaling, prefer the built-in multipreview annotations over hand-rolled ones: `@PreviewLightDark`, `@PreviewFontScales`, `@PreviewScreenSizes`, `@PreviewDynamicColors` (Compose ≥ 1.6.0). Define a custom multipreview annotation only for a project-specific combination not covered above. Do not multiply the matrix needlessly, every variant × every state is a screenshot to maintain.

6. **Match conventions.** Keep previews `private`, in the same file as the composable, named `<Composable>Preview`. Reuse an existing provider/sample-data source if the module already has one, do not duplicate fixtures.

## Make it screenshot-test ready

The screenshot harness reuses the same `@Preview` + provider; `@PreviewTest` is the only annotation that turns a preview into a test. Verify the module is wired (do not invent versions, read the project's catalog):

- Plugin `com.android.compose.screenshot` applied; `android.experimental.enableScreenshotTest=true` in `gradle.properties` and `experimentalProperties["android.experimental.enableScreenshotTest"] = true` in the module.
- `screenshotTestImplementation` has `com.android.tools.screenshot:screenshot-validation-api` and `androidx.compose.ui:ui-tooling`.
- If unwired, state the missing pieces and STOP, adding plugins/versions is a separate, approval-worthy change, not part of generating previews.

## Verify (local: no approval needed)

```bash
./gradlew :<module>:compileDebugKotlin        # previews compile
./gradlew spotlessApply && ./gradlew spotlessCheck
# first run records the baseline; later runs compare against it:
./gradlew :<module>:updateDebugScreenshotTest    # write/refresh reference PNGs
./gradlew :<module>:validateDebugScreenshotTest  # compare; HTML report on diff
```

Reference PNGs land in `src/screenshotTestDebug/reference/`; the diff report is `build/reports/screenshotTest/preview/<variant>/index.html`. Treat a baseline change as a reviewable diff, never run `update…` to silence a failing `validate…` without inspecting the report. Reference images are committed locally only; pushing them is outbound: get the operator's explicit yes first.

## CRITICAL gates
- Never instantiate a ViewModel, hit a network/DB, or read non-preview-safe singletons inside a preview, feed state in via the provider.
- Adding the screenshot plugin or bumping versions is out of scope here; report it and stop.
- All gradle commands above run locally. Pushing references/reports or opening a PR is outbound: get the operator's explicit yes first.

## References
- See [references/android-compose-mvi.md](../../references/android-compose-mvi.md) (loaded on demand) for the full Compose + MVI conventions: unidirectional state, one-off events, stability, and how previews back screenshot tests.
- [Preview your UI with composable previews](https://developer.android.com/develop/ui/compose/tooling/previews), `@Preview`, `PreviewParameterProvider`, `getDisplayName`, `limit`, multipreview templates.
- [Compose Preview Screenshot Testing](https://developer.android.com/studio/preview/compose-screenshot-testing), `@PreviewTest`, plugin/source-set setup, `update`/`validate` tasks, report location.
