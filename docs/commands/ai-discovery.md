<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
# /ai-discovery

The universal front door. Anyone (developer, manager, tech owner, product owner, QA) turns an idea into well-formed **intake fuel** for the pipeline. It writes no code, no plan, and does not pick the technical domain.

| | |
|---|---|
| **Takes** | nothing (run it bare), or an idea, files, links, or Figma URLs to seed it |
| **Produces** | classified intake fuel (an OKF bundle) with acceptance criteria, posted to your tracker |
| **Checkpoint** | post the fuel, or refine further |
| **Feeds** | [`/ai-plan`](ai-plan.md) |

## How to run

```text
/ai-discovery
```

Run bare to start a planning conversation from a blank page, or pass an idea, files, or links to seed it.

## What it does

1. **Opens a deep-planning conversation.** You talk the task through; it investigates alongside you and keeps a **living doc** open so you watch the work take shape. Each round it updates the doc, gives a short summary, flags open questions, and suggests what to refine next. You set the pace.
2. **Anchors the repo and tracker first.** It resolves where you are across four workspace shapes (single repo, monorepo, declared poly-repo product, or an undeclared parent of repos). If it is an undeclared parent, it stops and asks which repo, or offers to declare a workspace. See [concepts: run isolation](../concepts/run-isolation.md).
3. **Runs deep discovery** (read-only): what exists, what it touches, the constraints, the risks, and the **development dependencies** (what must land first, what this blocks). It cites what it finds and never invents.
4. **Classifies the fuel** as one of: story, bug, epic, tech-debt, or intent. An **epic** is split here into linked child stories, each with its own acceptance criteria; `/ai-plan` works those stories, never the epic. An **intent** is a not-yet-committed direction that discovery turns into a story.
5. **Always defines acceptance criteria**, as a checkable list, for whatever type it is.
6. **Writes the fuel as one OKF bundle**: a `briefing.md` built for comprehension (a cold reader gets it at a glance) plus the typed AI concepts built for completeness (every detail, so the build does not drift). See [concepts: OKF bundles](../concepts/okf-bundles.md).

## The checkpoint: post, or refine

It presents the fuel and stops for your explicit yes. Two moves:

- **Post** the story to your tracker as a new issue. Posting is outbound, so it waits for your yes. It dedups first (no duplicate issue), serializes the bundle into the issue so the content travels with it, and assigns you.
- **Refine** with another bounded discovery loop. It states the cap, ceiling, and exit criterion before you say yes.

It never posts without an explicit yes.

## Source

- Command: [plugins/adlc-core/commands/ai-discovery.md](../../plugins/adlc-core/commands/ai-discovery.md)
- Skill: [plugins/adlc-core/skills/ai-discovery/SKILL.md](../../plugins/adlc-core/skills/ai-discovery/SKILL.md)
