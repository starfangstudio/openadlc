---
name: unity-ui
description: >-
  This skill should be used when the user asks to "build a HUD", "add a main menu",
  "create a shop screen", "add an inventory panel", "set up mobile UI", "wire design tokens
  into Unity", "apply the brand theme to UI", "make UI responsive for all aspect ratios",
  "handle safe areas on iPhone/Android", "create a pause screen", "build a leaderboard UI",
  "add a results screen", "set up a UXML layout", "style UI with USS", "migrate from uGUI
  to UI Toolkit", or "fix UI on notched / tall / wide devices". Covers UI Toolkit (UXML/USS)
  for HUD, menus, and shop screens; responsive mobile layout with safe-area handling;
  consuming adlc-design design tokens as USS variables in a per-game theme; and the limited
  cases where uGUI or world-space Canvas still applies.
version: 0.1.0
---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# unity-ui

Build mobile game UI in Unity using UI Toolkit (UXML/USS) as the default for all screen-space
HUD, menus, and shop surfaces. Detect what the project already uses before writing a single file.

## Step 1: Detect first

Inspect the project before generating anything. Never impose a system the project has not adopted.

```bash
# What UI system(s) exist already?
find . -name "*.uxml" | head -5
find . -name "*.uss" | head -5
find . -name "*.tss" | head -5
find . -name "*.prefab" | xargs grep -l "Canvas\|UIDocument" 2>/dev/null | head -5

# Panel Settings asset (needed for UI Toolkit runtime)
find . -name "*.asset" | xargs grep -l "PanelSettings" 2>/dev/null | head -5

# Design-token USS (from adlc-design pack)
find . -name "tokens*.uss" -o -name "*design-tokens*" 2>/dev/null | head -5

# Assembly structure (UI code must live in the right asmdef)
find . -name "*.asmdef" | head -10
```

Record: `ui-toolkit` / `ugui` / `mixed`, Panel Settings path, existing UXML/USS naming
convention, token file location. Mark anything not found `unknown` -- do not invent paths.

## Step 2: Choose the right system

| Surface | System | Reason |
|---|---|---|
| HUD, menus, shop, inventory, results, leaderboard | **UI Toolkit (UXML/USS)** | GPU-batched, responsive Flexbox, CSS-like theming, USS variables |
| World-space labels / health bars above units | **uGUI Canvas (World Space)** | UI Toolkit has no native world-space support in Unity 6 |
| 3-D diegetic surfaces (in-world screens) | **uGUI or custom shader quad** | same limitation |
| Legacy screens already in uGUI | Keep uGUI; migrate only if performance requires it |

If the project already uses UI Toolkit consistently, add to it. If it uses uGUI consistently
and has no performance problem, do not migrate -- note the choice and continue.

## Step 3: UI Toolkit -- UXML layout

One `.uxml` file per screen or reusable component. Name: `ScreenName.uxml` / `ComponentName.uxml`.

For the default folder layout, the root element pattern, and touch-target rules,
see [references/unity-ui-detail.md](references/unity-ui-detail.md).

## Step 4: USS variables and the adlc-design token bridge

Design tokens live in the adlc-design pack. This skill consumes them -- it does not define them.
Cross-reference: `adlc-design / design-tokens` for the full token schema and export pipeline.

For the token USS file structure, per-game theme USS, TSS wiring, and example component styles,
see [references/unity-ui-detail.md](references/unity-ui-detail.md).

Rule: never hardcode color hex or pixel sizes in USS that should be tokens. If a token is missing,
add it to adlc-design and regenerate -- do not inline the value as a workaround.

## Step 5: Responsive mobile layout and safe areas

Safe areas are not automatic in UI Toolkit. Attach `SafeAreaAdapter` (a MonoBehaviour) to the
UIDocument GameObject to apply `Screen.safeArea` margins at runtime.

Thumb-reach rule: primary actions (attack, shop buy, continue) sit in the bottom 40% of
the screen. Navigation / close in top corners is acceptable only if also reachable bottom-right.

For the `SafeAreaAdapter` implementation and aspect-ratio USS media queries,
see [references/unity-ui-detail.md](references/unity-ui-detail.md).

## Step 6: Panel Settings

One Panel Settings asset per game (or per distinct render layer if you layer UI).
For Sort Order values, Scale Mode, and reference resolution settings,
see [references/unity-ui-detail.md](references/unity-ui-detail.md).

## Step 7: Verify

Run across all target aspect ratios in the Unity Editor using the Game view's aspect-ratio
switcher. Required set for these games: 16:9, 19.5:9 (tall phones), 4:3 (iPad).

Checklist:
- [ ] Safe-area margins applied and no content clipped by notch/home indicator.
- [ ] All interactive elements meet the 48 dp touch target minimum.
- [ ] No USS values hardcoded that belong to design tokens.
- [ ] Theme TSS assigned in Panel Settings; USS variables resolve (not magenta/default).
- [ ] Layout holds at 16:9, 19.5:9, and 4:3 without overflow or empty space >20% of screen.
- [ ] World-space UI (if any) uses uGUI Canvas in World Space mode with explicit sorting layer.

## Outbound checkpoint

Local work needs no approval. Outbound here (submitting a build to TestFlight, Google Play, or any CI/CD pipeline): stop, present exactly what would go out, and ask the operator for an explicit "yes" first.

## References

- Unity 6 UI Toolkit introduction: https://docs.unity3d.com/6000.4/Documentation/Manual/ui-systems/introduction-ui-toolkit.html
- Unity USS custom properties (variables): https://docs.unity3d.com/6000.1/Documentation/Manual/UIE-USS-CustomProperties.html
- Unity Theme Style Sheet (TSS): https://docs.unity3d.com/6000.0/Documentation/Manual/UIE-tss.html
- Unity USS variables in UI Builder: https://docs.unity3d.com/6000.3/Documentation/Manual/UIB-styling-ui-using-uss-variables.html
- Unity Screen.safeArea scripting API: https://docs.unity3d.com/6000.1/Documentation/ScriptReference/Screen-safeArea.html
- Unity comparison of UI systems: https://docs.unity3d.com/Manual/UI-system-compare.html
- Cross-reference: `adlc-design / design-tokens` for the token schema and export pipeline.
- Detail reference: [references/unity-ui-detail.md](references/unity-ui-detail.md)
