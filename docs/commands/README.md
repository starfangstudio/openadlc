<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
# Commands

Four commands, one per human decision point. This is the lifecycle, top to bottom.

```
/ai-discovery  ->  /ai-plan  ->  /ai-implement  ->  /ai-review
 idea to story       story to plan      plan to deliverable     deliverable to verdict
```

| Command | Takes | Produces | You decide |
|---|---|---|---|
| [`/ai-discovery`](ai-discovery.md) | an idea, bug, or epic (from any role) | classified intake fuel with acceptance criteria | approve the work before it is filed |
| [`/ai-plan`](ai-plan.md) | a story, bug, or tech-debt | a buildable plan, mapped slice by slice to the criteria | approve the plan before it is built |
| [`/ai-implement`](ai-implement.md) | an approved plan sub-issue | code, each slice ending in a check that passes or fails | approve the push before code leaves your machine |
| [`/ai-review`](ai-review.md) | a diff, branch, PR, or any code | a BLOCK or APPROVE verdict | approve the verdict before it is posted |

## What holds across all four

- **The consent checkpoint is everywhere.** Reading, local edits, local commits, and local builds never stop you. Anything outbound (posting a story, posting a sub-issue, pushing, posting a review) stops and asks for an explicit yes, at the boundary where it happens. See [concepts: checkpoints](../concepts/checkpoints.md).
- **Work travels as OKF bundles.** The story and the plan are Open Knowledge Format bundles: a human briefing plus the full AI context. See [concepts: OKF bundles](../concepts/okf-bundles.md).
- **Runs are isolated.** Each run gets a workspace-level run-id and an out-of-repo workspace at `~/.openadlc/runs/<workspace>/<run-id>/`; code lands on an `adlc/<run-id>` branch. See [concepts: run isolation](../concepts/run-isolation.md).
- **Acceptance criteria, end to end.** Intake defines them, the plan maps each slice to them, implement checks the build against them before any review.

There is no `ship` command on purpose: the push checkpoint lives inside [`/ai-implement`](ai-implement.md).

The command source files are the runtime instructions: [plugins/adlc-core/commands/](../../plugins/adlc-core/commands/). The [lifecycle map](../lifecycle.md) shows how the four fit together.
