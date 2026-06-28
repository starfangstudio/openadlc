---
name: ux-heuristics-review
description: >-
  This skill should be used when the user asks to "run a heuristic evaluation", "audit the
  UX of this flow", "check usability of this screen", "do a Nielsen heuristics review",
  "evaluate user control and error recovery", "identify usability problems", "rate severity
  of UX issues", "check if the onboarding flow is usable", "review the checkout experience
  for friction", "find usability problems before user testing", or "evaluate the mobile UX
  for thumb reach and offline states". Runs a structured usability heuristic evaluation
  against Nielsen's 10 heuristics plus mobile-specific heuristics (thumb reach,
  interruptibility, offline/poor-network), producing a severity-ranked findings list.
  Read-only; reports findings only, never edits source.
version: 0.1.0
---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# UX heuristics review

Evaluate a flow or screen set against Nielsen's 10 usability heuristics and mobile-specific
extensions. Produce a severity-ranked findings list. This is the usability/behavior
counterpart to the visual `design-critic` agent: it judges user control, feedback, and
cognitive load, not pixels or aesthetics.

## Detect first

Identify what to evaluate before assessing anything:

```bash
# Find screen files for the named flow (adjust pattern to the platform)
grep -rln "Checkout\|OnboardingScreen\|LoginFlow" --include="*.kt" --include="*.swift" --include="*.tsx" .
# Locate nav graph / route definitions to trace the full flow
grep -rln "NavGraph\|NavigationController\|AppNavigation\|Router" --include="*.kt" --include="*.swift" --include="*.tsx" . | head -10
# Find error-handling strings and empty-state logic
grep -rn "error\|empty\|offline\|retry\|loading" --include="*.kt" --include="*.swift" --include="*.tsx" . | grep -v "//.*#" | head -40
```

Mark any screen or state you cannot locate as `unknown`. Never invent behavior from filenames
alone; read the actual source for each screen in the flow.

Read the screens in order: entry point, each transition step, success state, error states,
empty states.

## Heuristics checklist

Evaluate each screen in the flow against every heuristic below. Note violations with screen
name and a one-line description.

### Nielsen's 10 (core)

| # | Heuristic | What to look for |
|---|---|---|
| H1 | Visibility of system status | Loading indicators present; async ops show progress; no silent failures |
| H2 | Match between system and real world | Labels use user vocabulary, not internal codes or developer jargon |
| H3 | User control and freedom | Cancel/back/undo available; no dead ends; destructive actions reversible |
| H4 | Consistency and standards | Platform conventions followed; same action same label/icon across screens |
| H5 | Error prevention | Dangerous actions confirmed; inputs validated inline before submission |
| H6 | Recognition over recall | Needed context visible on screen; no need to memorize from previous step |
| H7 | Flexibility and efficiency of use | Power-user shortcuts exist; defaults serve novices; repetitive tasks reducible |
| H8 | Aesthetic and minimalist design | No irrelevant content; every element earns its space; no competing CTAs |
| H9 | Help users recognize, diagnose, and recover from errors | Error messages in plain language, pinpoint cause, suggest a fix |
| H10 | Help and documentation | Complex tasks have in-context guidance; help is searchable and task-focused |

### Mobile extensions (M)

| # | Heuristic | What to look for |
|---|---|---|
| M1 | Thumb reach | Primary actions in the thumb zone (bottom 60% of screen); destructive actions not at reach extremes |
| M2 | Interruptibility | State survives interruption (call, app switch, rotation); forms auto-save or warn before discard |
| M3 | Offline and poor-network states | Degraded-network behavior defined; cached content available; retry mechanism present; no silent data loss |

## Severity scale

Assign every finding a severity using Nielsen's 0-4 scale, mapped to labels:

| Label | Nielsen | Criterion |
|---|---|---|
| Catastrophic | 4 | Blocks task completion; must be fixed before release |
| Major | 3 | High-frequency or high-impact friction; fix before ship |
| Minor | 2 | Affects some users; schedule for near-term sprint |
| Cosmetic | 1 | Suboptimal but rarely noticed; fix if time permits |
| None | 0 | Noted but not a usability problem |

Severity factors: frequency (how often hit), impact (how hard to recover), persistence
(one-time or repeated). Weight all three; a rare-but-catastrophic failure is still
Catastrophic.

## Output format

Emit findings in this exact structure. Do not omit the heuristic tag or fix field.

```
## UX Heuristics Review: <Flow Name>

### Catastrophic
- [H<n> or M<n>] **<Screen>**: <one-line description of the violation>
  Fix: <concrete, actionable change>

### Major
- [H<n> or M<n>] **<Screen>**: ...
  Fix: ...

### Minor
- ...

### Cosmetic
- ...

### Positive
- <What the flow gets right (specific, not generic)>

### Verdict
<one-line: ready to ship / needs fixes before ship / needs significant rework>
```

If a heuristic has no violations, omit that severity section. If a screen or state is
`unknown` (not found in code), list it explicitly under a `### Unknown / not evaluated`
section rather than guessing.

## Scope and guardrails

- Read-only. This skill reads source and reports. It never edits, generates, or applies
  fixes. Route fixes to the implementing engineer or the appropriate skill.
- Evaluate behavior and information architecture, not visual design. Pixel-level critique
  belongs to the `design-critic` agent.
- Do not flag over-engineering: report usability violations only, not missing features or
  aspirational improvements the user did not request.
- When a platform convention is ambiguous (e.g., iOS vs. Android back-navigation behavior),
  name the platform and apply its specific convention (H4).

## Outbound checkpoint

Local work needs no approval. Anything outbound (publish, push, post) needs an explicit per-action "yes" from the operator first; see the global consent law.

## References

- Jakob Nielsen, "10 Usability Heuristics for User Interface Design", Nielsen Norman Group:
  https://www.nngroup.com/articles/ten-usability-heuristics/
- Jakob Nielsen, "How to Rate the Severity of Usability Problems", Nielsen Norman Group:
  https://www.nngroup.com/articles/how-to-rate-the-severity-of-usability-problems/
- NN/g, "Communicating UX Findings Using a Severity Scale" (video):
  https://www.nngroup.com/videos/prioritize-ux-findings-severity/
