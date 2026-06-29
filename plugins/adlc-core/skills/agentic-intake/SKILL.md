---
name: agentic-intake
description: "Use when the user types /agentic-intake, or asks to start a story, file a bug, scope an epic, do discovery, or turn an idea, Figma, screenshots, or a ticket into something buildable. The universal front door to the lifecycle: it opens a deep-planning conversation, keeps a living doc, classifies the work into intake fuel with acceptance criteria, and only on the user's explicit yes posts it as a tracker issue."
version: 0.1.0
---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# Agentic Intake

The universal front door to the OpenADLC lifecycle. Turn any idea, bug, or epic into well-formed, classified intake fuel with clear acceptance criteria. Write no code and no plan; produce what `/agentic-plan` turns into a plan. Nothing is posted to a tracker without the user's explicit yes.

## Steps

1. Greet the user and ask for the task: a feature, a bug, an epic, tech-debt, or a rough direction. Accept pasted documents, screenshots, links, and Figma URLs.
2. Open a living briefing (`briefing.md`, the human face) and keep it updated every round so the user can watch it fill in. It lives in the run workspace, which is the OKF bundle for this run.
3. Run deep discovery, loopable: investigate the repo and the inputs, and surface the development dependencies as you go. After each round give a short summary, flag the open questions, and suggest what to refine next. The user decides how deep to go.
4. Classify the work as a story, bug, epic, tech-debt, or intent. Split an epic into its linked child stories, never just one story. Always produce clear acceptance criteria.
5. Write the result as one OKF bundle: `briefing.md` (the prettified human face, built for comprehension) plus typed AI-context concepts (`story.md`, `discovery.md`, `dependencies.md`, built for completeness), with `okf_version: "0.1"` in `index.md`. Do not choose the domain here; that is the plan step.
6. CHECKPOINT, consent: when the user says "done", "create it", or "post it", present exactly what would be posted and STOP for an explicit yes. On GitHub the issue shows `briefing.md` as the body with the AI concepts unwrapped into a collapsible `<details>` (overflow to sequential comments past ~60KB); on Jira/ADO the body is `briefing.md` and the bundle is attached as `<slug>.okf.tgz`. Assign yourself on create and verify the assignee stuck. Nothing is posted without that yes. After posting, record the issue URL back in the bundle.

Next: `/agentic-plan` against the posted issue.

## Verify
The intake stops for an explicit yes before any tracker post; the output is one OKF bundle (briefing + classified unit + AI concepts) with acceptance criteria.
