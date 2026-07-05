<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
# Getting started

Install OpenADLC once, run your first command, understand the checkpoints. Five minutes.

OpenADLC runs inside the coding harness you already use. Pick your harness for the exact steps:

- [Claude Code](claude-code.md)
- [Cursor](cursor.md)
- [Copilot](copilot.md)
- [Codex](codex.md)
- [Windsurf](windsurf.md)
- [Antigravity](antigravity.md)

Any other [APM](https://github.com/microsoft/apm) target works too. The install and the flow below are the same everywhere; only how a command surfaces in the harness differs.

## 1. Prerequisites

- A supported harness (one of the six above, or another APM target).
- [APM](https://github.com/microsoft/apm), the agent package manager. OpenADLC ships as APM packs.

## 2. Install

One command. It deploys to your harness automatically.

```bash
apm install starfangstudio/openadlc
```

This installs the always-on `adlc-core` spine: the four `/ai-*` commands and the lifecycle checkpoints. Domain packs (web, backend, iOS, and the rest) are installed on demand from the same marketplace, for example `apm install adlc-web@openadlc`. See [customize](../customize/) once you are set up.

Update later with:

```bash
apm update
```

## 3. Run your first command

From a project root, in your harness, run:

```text
/ai-discovery
```

Describe what you want to build. Intake turns it into a well-formed, classified story with acceptance criteria, and stops at a checkpoint before anything is posted. From there the loop continues:

```text
/ai-discovery  ->  /ai-plan  ->  /ai-implement  ->  /ai-review
 idea to story       story to plan      plan to deliverable     deliverable to verdict
```

One command per human decision point. Full detail per command is in [commands](../commands/).

## 4. The checkpoints, in one minute

The rule that runs through all of it: **a human owns anything that leaves your machine.**

- **Reading, local edits, local commits, local builds and tests never stop you.** No friction on local work.
- **Anything outbound stops and asks.** Posting a story, posting a sub-issue, pushing code, posting a review: at each of these the agent presents exactly what would leave, then waits for your explicit yes. Approval of one outbound action is not approval of the next.

There is no separate `ship` command on purpose. The push checkpoint lives inside `/ai-implement`, so nothing reaches a remote without your yes. See [concepts: checkpoints](../concepts/) for the full model.

## 5. Pick your models

Choose your model and effort in your harness, per stage. There is no OpenADLC config to maintain for this.

## Where to go next

- [The ADLC lifecycle](../lifecycle.md): the whole machine, end to end.
- [Commands](../commands/): one page per `/ai-*` command.
- [Config](../config/): the optional `openadlc.yaml`.
- [Customize](../customize/): your own skills and packs.

## A note on status

OpenADLC is in early development. The lifecycle runs across APM-supported harnesses through the portable pack format. Claude Code is the most exercised target today. Expect breaking changes.
