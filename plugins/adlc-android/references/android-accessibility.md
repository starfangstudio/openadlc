<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
# Android accessibility

Every interactive or meaningful element must be operable by TalkBack, Switch Access, and large-text users. Build it in; don't bolt it on at review.

## Labels (TalkBack)
- **Text composables/`TextView` need no `contentDescription`**: TalkBack reads the text. Adding one double-speaks.
- **Non-text actionable elements (icon buttons, image buttons) need a localized `contentDescription`** describing the *action/destination*, not the glyph: "Search", not "magnifying glass". Views: `android:contentDescription` (or `app:tint`-only icons → set it in code).
- **Purely decorative `Image`/`Icon` → `contentDescription = null`** (Compose) / `importantForAccessibility="no"` (Views). A focus stop with no meaning is noise.
- Never put user-facing label text inline: use string resources (see `android-naming.md`).

## Touch targets: 48dp minimum
- Any clickable/touchable element must be **≥ 48dp × 48dp** (Material/WCAG minimum), even if the visible glyph is smaller (e.g. a 24dp icon).
- Compose: use `IconButton` (handles it), or `Modifier.minimumInteractiveComponentSize()`, or `Modifier.sizeIn(minWidth = 48.dp, minHeight = 48.dp)`. Do not shrink targets below 48dp to fit a layout.
- Views: `minWidth`/`minHeight` = `48dp`, or `TouchDelegate` to expand the hit rect of a small visual.

## Color & contrast: never rely on color alone
- Convey state/meaning with **text, icon, or shape in addition to color** (error vs. success, selected vs. not). Color-blind users must still parse it.
- Text contrast ratio **≥ 4.5:1** (normal text) / **≥ 3:1** (large text ≥ 18sp, or 14sp bold) against its background. Use theme tokens designed to meet this, not hardcoded hex.
- Respect system font scaling: size text in **`sp`** (never `dp`); test at 200% font size, layouts must not clip or truncate.

## Compose semantics
- Standard components (`Button`, `Switch`, `Checkbox`, `IconButton`) ship correct `role`/`stateDescription`: prefer them over hand-rolled clickable `Box`es.
- **Group a logically-single item** (avatar + name + timestamp row) with `Modifier.semantics(mergeDescendants = true) {}` so TalkBack reads one utterance and stops once. Keep the `clickable` on the parent only, not each child.
- **Mark headings** with `Modifier.semantics { heading() }` so users can jump heading-to-heading.
- **Custom toggle/selectable** → `Modifier.toggleable/selectable(..., role = Role.Checkbox/Switch)` and set `stateDescription` for non-obvious states. Don't reinvent state announcement.
- **Custom gestures** (swipe-to-dismiss, drag) must expose an equivalent via `semantics { customActions = listOf(CustomAccessibilityAction(label, action)) }`: gesture-only actions are invisible to TalkBack/Switch Access.
- Strip noisy/duplicate subtree semantics with `Modifier.clearAndSetSemantics {}`; hide decorative-only nodes. Use a stable `Modifier.testTag(...)` for a11y/UI tests, not `contentDescription`.

## Views (XML) checklist
- `labelFor` to associate a label with its `EditText`; `hint` for example input.
- Logical focus/reading order via `accessibilityTraversalBefore/After` when visual order ≠ DOM order.
- Group related views with `screenReaderFocusable=true` + children `importantForAccessibility="no"` (the merge-descendants equivalent).

## Verify (don't claim done without this)
- Turn on **TalkBack** and swipe through the screen: every actionable element is reachable, announced meaningfully, with sensible order and no dead/duplicate stops.
- Run **Accessibility Scanner** (Play Store app) on the screen, fix flagged target-size, contrast, and missing-label issues.
- Add `composeTestRule` assertions on semantics (`onNodeWithContentDescription`, `assertHasClickAction`, state) for the states you ship.

## References
- Principles for improving app accessibility, https://developer.android.com/guide/topics/ui/accessibility/principles
- Accessibility in Jetpack Compose (semantics, merge, headings, 48dp), https://developer.android.com/codelabs/jetpack-compose-accessibility
- Test your app's accessibility (TalkBack, Accessibility Scanner), https://developer.android.com/guide/topics/ui/accessibility/testing
