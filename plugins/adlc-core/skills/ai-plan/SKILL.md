---
name: ai-plan
description: "Use when the user types /ai-plan, or asks to plan a story or bug, scope work, write a spec, or design an approach before building. Turns one buildable unit of intake fuel into a complete, buildable plan that maps each acceptance criterion to a slice, and stops for the user's approval before posting a sub-issue."
version: 0.1.0
---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# AI Plan

Turn one buildable unit of intake fuel (a story, a bug, or tech-debt, never an epic) into a complete, buildable plan. Nothing is posted without the user's explicit yes.

When a `references/<name>.md` link does not resolve relative to this file, locate it under the deployed adlc-core pack (search for the file name, e.g. under `apm_modules/*/adlc-core/references/`) and READ the referenced file before acting on its rule.

## Steps

1. Read the intake fuel: when it is a tracker issue, reassemble its OKF bundle first (on GitHub parse the markers across the body and comments; on Jira/ADO download and untar `<slug>.okf.tgz`). Detect the domain from the repo, and ASK when it is ambiguous, empty, or the item spans platforms or layers (frontend plus backend, iOS plus Android, and so on). One item can fan out into several plans.
2. Restate the acceptance criteria, then build a thorough plan that is a complete contract: each acceptance criterion mapped to a slice, the approach, happy and error flows, contracts, tests, design references (Figma baseline), the development dependencies and any layout intent carried from intake, and every cross-cutting angle that applies (security, accessibility, performance, privacy).
3. Keep the plan as an OKF bundle: a `briefing.md` human-readable summary plus the full build context as typed concepts (`spec.md`, `Plans.md`, contracts). Save the bundle locally in the run workspace.
4. CHECKPOINT, consent: present the plan and STOP. Before asking, write the checkpoint file (`type: post-subissue`, `checkpoints.md`); the user may also resolve it from the cockpit while you wait. The user approves or edits it. Only on an explicit yes, post a remote sub-issue: on GitHub the plan `briefing.md` is the body with the plan concepts unwrapped into a collapsible `<details>` (overflow to sequential comments past ~60KB); on Jira/ADO the body is the `briefing.md` and the bundle is attached as `<slug>.okf.tgz`. On GitHub, create the sub-issue, assign yourself, link it as a NATIVE sub-issue of the parent, then VERIFY the parent link landed (an unlinked sub-issue is an incomplete post). Nothing is posted without that yes. Set `index.md`'s `status: done` if the run ends here (`checkpoints.md`).

Next: `/ai-implement` against the posted sub-issue.

## Verify
The plan restates every acceptance criterion and maps each to a slice; it stops for approval before any sub-issue is posted.
