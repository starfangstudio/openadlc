<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
# Compose + MVI conventions

State flows down, events flow up. The ViewModel owns state; the UI is a pure function of it.

> **Note:** some codebases are **primarily Views/XML + a custom design system**, with Compose selective/per-module. This rule is the modern Compose default, in a Views-heavy module, `android-legacy-views` is the more relevant one. Match the module you're in.

## State
- Expose **one immutable UI state per screen** as a `data class`, surfaced via `StateFlow<UiState>`. Model loading / empty / error explicitly (fields or a sealed `UiState`), never implicit nulls.
- Collect with `collectAsStateWithLifecycle()`.
- Keep Android framework types (Context, View, Intent) out of state.

## Events
- UI sends user intents up via lambdas / an `onEvent(Event)` sink. Model events as a sealed `Event`/`Intent` type.
- One-off effects (navigation, snackbars) go through a `Channel`/`SharedFlow` consumed lifecycle-aware, **not** stored in UI state (which would replay them on recomposition/rotation).

## Composables
- No business logic, I/O, or ViewModel creation inside composables; pass state in and lambdas out (state hoisting).
- Split a stateful screen composable (reads ViewModel) from stateless content composables (take state + lambdas), the stateless ones are previewable and testable.

## Stability / performance
- Use immutable/`@Immutable` types in state; `remember` derived values; avoid allocating new lambdas/objects per recomposition.
- Defer state reads to the narrowest scope (lambdas, `derivedStateOf`) to limit recomposition.

## Previews
- Provide `@Preview` for each meaningful state (content, loading, empty, error) using a `PreviewParameterProvider`. Keep previews compiling, they back Compose screenshot tests.

## Interop (legacy)
- Compose inside Views: `ComposeView`. Views inside Compose: `AndroidView`. Migrate incrementally; don't rewrite working screens without reason.
