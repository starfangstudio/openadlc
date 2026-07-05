<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
# Checkpoints

A **checkpoint** is a mandatory step that never skips. Some are automatic, some ask you a question, and some are the consent stop before anything leaves your machine. Together they are how a human stays in control of the lifecycle.

## The three human checkpoints

The ADLC standard defines three (see [the spec, section 4](../../standard/spec.md)):

| Checkpoint | Where | You decide |
|---|---|---|
| **Plan approval** | after planning | whether the approach is right before any code is written |
| **Code review** | after building | whether the change is safe and correct before it ships |
| **Consent checkpoint** | before anything outbound | whether what would leave your machine is allowed to go |

Plan approval and code review are strong defaults you can tune to your risk (see [config](../config/)). The consent checkpoint is different: the release decision is always a human's, so it always applies and is not a setting you turn off.

## Three kinds of checkpoint

Not every checkpoint asks you something:

- **Automatic:** the agent runs them itself, like verifying a slice with a failable check, or the acceptance-criteria check (the AI's own "is this actually done?").
- **Ask:** the agent stops and asks you, like choosing SDD or TDD, or which reviews to run.
- **Consent:** the outbound kind. The agent presents exactly what would leave, and waits for your explicit yes.

## The consent checkpoint

The rule: the agent obtains explicit approval immediately before each outbound action, and presents what will go out before asking.

**What counts as outbound** (it stops for at least these): pushing commits, opening or updating a PR, merging; any comment, review, message, or email to another person or system; any network write (API POST/PUT/DELETE, MCP or tool writes); any release, deploy, or publish.

**What "explicit approval" means:** it is per-action (approving one is not approving the next), it follows a clear presentation of what would leave, and it is never standing or implied.

**What is never stopped** (so the checkpoint stays meaningful): reading local files, the web, and read-only queries; editing local files and local commits with no push; local builds and tests; talking to you.

It is a step the agent performs, intrinsic to the lifecycle, not a toggle. This is Law L1 (a human owns the release decision).

## Honored vs enforced

- A **solo dev** honors their own checkpoints, locally and for free. They tune the plan and review checkpoints; the consent checkpoint is always present.
- An **organization** enforces the chosen checkpoints centrally across every seat, with a central audit trail that proves it happened. That is what the Governed level adds. See [adoption](../../standard/adoption.md).

For an unattended or autonomous run, a checkpoint must be enforced, not merely honored, because no human is present in the moment to decide.

## Where checkpoints show up in the commands

- [`/ai-discovery`](../commands/ai-discovery.md): post the story (consent), or refine.
- [`/ai-plan`](../commands/ai-plan.md): approve, edit, or refine the plan; post the sub-issue (consent).
- [`/ai-implement`](../commands/ai-implement.md): the verify and acceptance-criteria checks (automatic), the review ask (mandatory), the push (consent).
- [`/ai-review`](../commands/ai-review.md): post the verdict (consent); persisting it locally is not gated.

## Source

- [The lifecycle](../lifecycle.md), [the spec, section 4](../../standard/spec.md), [adoption](../../standard/adoption.md).
