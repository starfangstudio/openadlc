<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
# Concepts

The ideas the commands are built on. Read these to understand why the lifecycle behaves the way it does.

- [**OKF bundles**](okf-bundles.md): how the story and the plan travel, one artifact that a human and an agent both read.
- [**Run isolation**](run-isolation.md): the run-id, the out-of-repo workspace, and the per-run branch that let parallel runs share a repo without colliding.
- [**Checkpoints**](checkpoints.md): where a human stays in control, and the consent stop before anything leaves your machine.
- [**Packs**](packs.md): the portable unit of guidance, an always-on spine plus domain packs that load on demand.

For the whole machine end to end, see [the lifecycle](../lifecycle.md). For the open standards underneath (AGENTS.md, Agent Skills, MCP, OKF), see the [standard](../../standard/spec.md).

> **A note on vocabulary.** The [standard](../../standard/spec.md) defines *harness* in the tool sense (the thing that runs an agent: Claude Code, Codex, Copilot); OpenADLC's own product copy calls these *agentic coding tools*. Same referent, two audiences: the standard stays vendor-neutral, the product speaks plainly.
