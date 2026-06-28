---
name: agentic-plan
description: "Use when the user types /agentic-plan, or asks to plan a story or bug, scope work, write a spec, or design an approach before building. Turns one buildable unit of intake fuel into a complete, buildable plan that maps each acceptance criterion to a slice, and stops for the user's approval before posting a sub-issue."
version: 0.1.0
---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# Agentic Plan

Turn one buildable unit of intake fuel (a story, a bug, or tech-debt, never an epic) into a complete, buildable plan. Nothing is posted without the user's explicit yes.

## Steps

1. Read the intake fuel (the issue). Detect the domain from the repo, and ASK when it is ambiguous, empty, or the item spans platforms or layers (frontend plus backend, iOS plus Android, and so on). One item can fan out into several plans.
2. Restate the acceptance criteria, then build a thorough plan that is a complete contract: each acceptance criterion mapped to a slice, the approach, happy and error flows, contracts, tests, design references (Figma baseline), the development dependencies and any layout intent carried from intake, and every cross-cutting angle that applies (security, accessibility, performance, privacy).
3. Keep the plan in two faces: a human-readable summary and the full build context. Save the plan files locally.
4. CHECKPOINT, consent: present the plan and STOP. The user approves or edits it. Only on an explicit yes, post a remote sub-issue, with the human-readable plan as the body and the plan files attached if the tracker supports it. Nothing is posted without that yes.

Next: `/agentic-implement` against the posted sub-issue.

## Verify
The plan restates every acceptance criterion and maps each to a slice; it stops for approval before any sub-issue is posted.
