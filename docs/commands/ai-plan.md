<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
# /ai-plan

Turns intake fuel into a buildable plan: the complete contract for the build. It authors nothing itself; the plan is written by the [`create-plan`](../../plugins/adlc-core/skills/create-plan/SKILL.md) skill.

| | |
|---|---|
| **Takes** | a plannable unit: a story, bug, or tech-debt (text, a file, or a tracker issue) |
| **Produces** | one dev plan per domain (an OKF bundle) plus a remote sub-issue |
| **Checkpoint** | approve, edit, or refine, then post the sub-issue |
| **Feeds** | [`/ai-implement`](ai-implement.md) |

Not an epic (plan its child stories) and not a bare intent (needs discovery at intake first).

## How to run

```text
/ai-plan <story text | path to a file | tracker issue URL or #number>
```

## What it does

1. **Resolves the input** and selects the run by run-id (never by matching a feature name). When the input is a tracker issue, it reassembles the intake bundle from it. It pulls in the acceptance criteria, the development dependencies, and any layout intent.
2. **Detects or asks for the domain.** It detects from the repo (a web framework, `build.gradle`, `Package.swift`, a server framework, and so on) when the signal is clear, and **asks** when the repo is empty, ambiguous, or the work spans platforms or layers. One parent story fans out into **one plan and one sub-issue per domain**. It loads the domain pack, plus a cross-cutting pack (security, privacy, AI) when relevant, and `adlc-design` only when the work touches Figma or a design surface.
3. **Explores read-only** via `codebase-researcher`, citing `path:line`.
4. **Plans** via `create-plan`: it restates the acceptance criteria, breaks the work into slices with **each criterion mapped to a slice**, and writes the flows, contracts, tests, design references, carried dependencies, and the cross-cutting concerns that apply. The plan is an OKF bundle: a `briefing.md` a person follows plus the full plan concepts the implementer consumes. See [concepts: OKF bundles](../concepts/okf-bundles.md).

All plan artifacts land in the out-of-repo run workspace (`~/.openadlc/runs/<workspace>/<run-id>/plan/`), never inside the repo. See [concepts: run isolation](../concepts/run-isolation.md).

## The checkpoint: approve, edit, or refine

It presents the plan and stops for you. Three moves:

- **Approve** it as written.
- **Edit** the scope, approach, or rollback before anything is posted.
- **Refine** with a bounded loop (iterate to tighten it, or generate a few approaches and judge). It states the cap, ceiling, and exit criterion before you say yes.

On approval it posts **one native sub-issue per domain**, linked under the parent story and assigned to you, with the plan bundle serialized into the body. Posting is the only outbound step and it needs your explicit yes.

## Source

- Command: [plugins/adlc-core/commands/ai-plan.md](../../plugins/adlc-core/commands/ai-plan.md)
- Skill: [plugins/adlc-core/skills/create-plan/SKILL.md](../../plugins/adlc-core/skills/create-plan/SKILL.md)
