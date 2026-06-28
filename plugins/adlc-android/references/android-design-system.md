<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
# Android design system

## Core rule
- **Never use raw platform widgets** (`Button`, `TextView`, `Switch`, `AlertDialog`, `BottomSheetDialog`, …) when a design-system equivalent exists. Many projects **lint-fail the build** on raw widgets.
- **Pick components by intent, not by style:** primary / secondary / ghost / destructive for actions, etc. The variant communicates meaning.

## Tokens & strings
- Use design tokens for color, spacing, and type, never hardcode hex or dp for themed values.
- No hardcoded user-facing strings: use string resources (`strings-<feature>.xml`).

## Reusability: build once, use everywhere
The design system *is* the UI reuse layer; treat it as such.
- **Reach for an existing component before writing UI.** Check the design system first; only build new when nothing fits. Don't re-style a raw widget to mimic one that already exists.
- **Promote a pattern to a shared component on the second occurrence when the duplication is the same knowledge** (identical semantics, not just similar looks); for merely look-alike UI wait for the third use (rule of three). Slot-based API (`content`/trailing lambdas) so callers compose rather than fork it. Extracting on the first use is premature. Same rule as `android-shared-composables`.
- **Style via tokens + a theme, not per-screen overrides.** One source of truth for color/space/type means a restyle touches one layer. A one-off visual tweak is a smell, fold it into the token set or a component variant.
- **Every shared component is previewable and accessible** (see `android-compose-preview`, `android-accessibility`) and is a contract, change it deliberately, with tests.
- For extracting reusable composables specifically, see `android-shared-composables`.

## Example: a custom design system
Components live under a shared `common.ui.view.*` package. Buttons by intent:
| Variant | Class |
|---|---|
| Primary | `ButtonPrimary` |
| Secondary | `ButtonSecondary` |
| Ghost | `ButtonGhost` |
| Ghost Alt | `ButtonGhostAlt` |
| Destructive | `ButtonDestructive` |
| Destructive Ghost | `ButtonGhostDestructive` |

## New projects
- Detect the existing design system first and stay idiomatic. If none exists, use Material 3 with a centralized theme and a small set of wrapped components, so a future swap touches one layer.
