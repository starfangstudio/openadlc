---
name: android-automation-tags
version: 0.1.0
description: >-
  This skill should be used when the user asks to "make this screen testable
  with Maestro", "add testTags for automation", "why can't Maestro find my
  Compose element", "expose testTag as resource id", "set up Maestro selectors",
  or otherwise needs to wire Jetpack Compose semantics/testTag conventions so an
  end-to-end automation tool (Maestro, UiAutomator, Appium) can reliably locate
  elements.
---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# Android automation tags (Maestro + Compose semantics)

Make Compose UI reliably addressable by black-box automation tools. Maestro and
UiAutomator drive the app through the accessibility tree, not Compose test APIs, so elements must surface stable, externally observable selectors.

## Selector priority: match in this order
Prefer the most change-resilient selector that uniquely identifies the element
(same ordering as the `maestro-ui-testing` skill):

1. **Stable identifier** (`testTag` exposed as resource id): survives copy changes
   and localization; mandatory for localized apps, lists, and dynamic content.
2. **Accessibility label** (`contentDescription`): for icons/images; doubles as an
   a11y win, but it is user-facing and localized too.
3. **Visible text**: acceptable for single-locale smoke flows only; breaks on copy
   changes and every translation.

Tags are still a maintenance cost: add them deliberately (interactive and asserted
elements), not on every node. If a screen is single-locale and its copy is stable,
text selectors are fine; the moment localization lands, ids win.

## Wiring testTag through to Maestro
Compose `Modifier.testTag(...)` is invisible to Maestro by default. Expose tags as
resource ids via the `testTagsAsResourceId` semantics property, **set it ONCE, high
in the hierarchy** (e.g. the top-level `Scaffold`); all nested `testTag`s inherit it.

```kotlin
Scaffold(
    // Enable once at the top, all nested composables inherit it.
    modifier = Modifier.semantics { testTagsAsResourceId = true }
) {
    LazyColumn {
        item {
            Button(
                modifier = Modifier.testTag("submitOrderButton"),
                onClick = ::submit,
            ) { Text(stringResource(R.string.submit)) }
        }
    }
}
```

Reference the tag as an `id` in the flow:

```yaml
- tapOn:
    id: "submitOrderButton"
```

Requires Compose `1.2.0-alpha08`+. Do not set `testTagsAsResourceId` on every
composable, once near the root is correct and avoids tree bloat.

## Naming convention
- **camelCase**, descriptive, prefixed by feature/screen: `loginEmailField`, `cartItemRow`,
  `paywallContinueButton`. Globally unique within a screen.
- For list rows, append a stable key, not the index: `cartItemRow_${sku}`: never
  `cartItemRow_0` (index shifts as the list mutates).
- Keep the tag string in a single shared `const`/object referenced by both UI and flow
  where the project supports it, so a rename is one edit.

## Verify the tag is reachable (pass/fail)
Never assume a tag landed in the tree. Dump the live hierarchy and grep for it:

```bash
maestro hierarchy | grep -i "submitOrderButton"   # must print a node with resource-id
```

If absent: `testTagsAsResourceId` is missing/too low in the tree, the Compose version
is too old, or the node is off-screen (scroll first). Re-run after fixing.

## DI / architecture note
Tags belong in `-impl` UI code alongside the composable. Do not leak tag string
constants through an `-api` module, they are an implementation detail of the screen,
not a cross-feature contract.

## Outbound checkpoint

Local work needs no approval. Anything outbound (publish, push, post) needs an explicit per-action "yes"; see the global consent law.

## References
- Maestro: Android / Jetpack Compose support (accessibility-first selectors, `id`):
  https://docs.maestro.dev/platform-support/android-jetpack-compose
- Android Developers: Compose testing interoperability (`testTagsAsResourceId`, set once
  high in the hierarchy): https://developer.android.com/develop/ui/compose/testing/interoperability
