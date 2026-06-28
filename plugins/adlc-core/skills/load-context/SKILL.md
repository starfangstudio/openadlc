---
name: load-context
description: "This skill should be used at the START of a non-trivial task, when the user asks to \"load context\", \"gather context\", \"what do I need to know before planning\", \"prep before implementing\", \"brief me on this feature/ticket\", or before create-plan/implement-change on unfamiliar code. Assembles a focused context brief (ticket + code + contracts + exemplar + verify command) and persists it so planning and resume can reuse it."
version: 0.1.0
---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# Load context

Assemble exactly the context a plan or implementation needs, cheapest signals first, and write it to disk so it survives the session. This is the "studying" half that pairs with the readiness gate (`gate-plan-readiness`): load context here, check sufficiency there.

## Tiered loading (stop at sufficiency)
1. **Map (cheap).** **First resolve the target workspace + tracker** (the four shapes in [references/run-isolation.md](references/run-isolation.md)): a single git repo is the workspace and `git remote get-url origin` is the tracker; a monorepo is one workspace; a **poly-repo product** declared in `openadlc.yaml` (`workspace.repos` + `primary`) is the workspace, and its `primary` repo's remote is the tracker; an **undeclared parent of several repos** is not a workspace, ASK which repo, or offer to declare them a workspace, and never anchor on the parent. Then list the relevant files and read only their names, headers, and any rule/convention descriptions, not bodies. Pull the **intake fuel** if there is one (`gh issue view <id> --comments`, or the tracker; reads are ungated). Intake fuel is the unit of work from the universal front door, classified as **story / bug / epic / tech-debt / intent**, never just "a ticket". Note its type, its acceptance criteria, and any **development dependencies** the intake surfaced: planning and implementation carry these forward, so capture them now rather than rediscovering them later.
2. **Targeted (medium).** Read the 1-3 files that will actually change and their direct call sites. For a feature-modular repo, map the `-api`/`-impl` contract boundaries the change crosses. Find the exemplar: the existing file that already does the closest thing, to copy its shape. Note the **technical domain** the change lives in as you read (FE / BE / android / ios / windows / macos, or several at once); /agentic-plan will detect-or-ask the domain, so flag it here, and flag when one story spans platforms or layers (FE+BE, android+ios) so the plan knows it may fan out.
3. **Deep (expensive).** One reference read, delegated to the `codebase-researcher` subagent so the heavy reading stays out of the main context. Only if tiers 1-2 left a real gap.

**Broad explore (many files or subsystems): fan out.** Instead of reading serially, dispatch one reader per subsystem via batched Task calls or the Workflow tool (fan-out pattern, [references/orchestration.md](references/orchestration.md)), then synthesize the briefs into one context block. Apply the parallel-barrier: collect all briefs before writing the final context brief.

Mark anything unverified `unknown`; never invent a path, a contract, or a fact. Stop as soon as you have enough to plan; over-loading is a failure mode.

## Output (persist it)
Write the brief to `~/.openadlc/runs/<workspace>/<run-id>/context.md`, the out-of-repo per-run workspace from [references/run-isolation.md](references/run-isolation.md) (never the repo's `.claude/`, never committed). If this is the first lifecycle step that writes anything (no run-id exists yet for this work), mint the run-id ONCE here (`<slug>-<UTC-timestamp>`) and create the dir; create-plan, implement-change, and plan-resume then reuse that same run-id and read this brief instead of re-deriving:

```markdown
# Context brief: <feature>
- Run-id: <slug>-<UTC-timestamp>  (workspace-level; carried forward; spec.md records run_id + branch adlc/<run-id>)
- Workspace shape: single repo | monorepo | poly-repo product | undeclared parent (asked / declared)
- Workspace + tracker: <workspace name> -> <primary repo's git remote / tracker URL>
- Repos this run may touch: <repo, repo, ...> (poly-repo product), or <the single repo>
- Intake fuel: <link or summary>, type: story | bug | epic | tech-debt | intent
- Acceptance: <what done looks like>
- Technical domain: <FE | BE | android | ios | windows | macos | several>; spans platforms/layers? <yes + which, or no>
- Dev dependencies (carried from intake): <blockers, order, shared contracts, or "none">
- Files likely to change: <path:line each>
- Contracts crossed: <-api/-impl boundaries, interfaces>
- Exemplar to follow: <path> (does the closest existing thing)
- Verify with: <exact module-scoped command>
- Open unknowns: <list, or "none">
- Tiers loaded: 1 | 1-2 | 1-3
```

Then hand off: feed this into `create-plan` (or `gate-plan-readiness` to check sufficiency before planning).

## Guardrails
Read-only investigation; this skill writes only the brief, never source. Everything here is local and ungated.

## References
- Run isolation (run-id minting, per-run workspace, repo-anchor): [references/run-isolation.md](references/run-isolation.md)
- Parallelism patterns (fan-out, parallel-barrier, pipeline, loop-until-dry, adversarial-verify panel, judge-panel, multi-modal sweep): [references/orchestration.md](references/orchestration.md)
