<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
# Getting started: Claude Code

[Claude Code](https://www.anthropic.com/claude-code) is Anthropic's coding CLI, and the most exercised OpenADLC target. The pack format is authored against Claude Code's plugin schema (`.claude-plugin/plugin.json`), so this is the reference agentic coding tool.

## Prerequisites

- Claude Code, installed and working.
- [APM](https://github.com/microsoft/apm), the agent package manager.

## Install

```bash
apm install starfangstudio/openadlc
```

APM deploys the `adlc-core` spine into Claude Code automatically. Update later with `apm update`.

## Run a command

The four commands surface as native slash commands. From a project root, in Claude Code:

```text
/ai-discovery
```

Then `/ai-plan`, `/ai-implement`, and `/ai-review` as the work moves through the loop. See [commands](../commands/) for what each one does.

## Models and effort

Pick the model and effort in Claude Code, per stage. Nothing to configure in OpenADLC for this.

## Notes

- Domain packs install the same way, on demand: `apm install adlc-web@openadlc`, `adlc-backend@openadlc`, and so on. See [customize](../customize/).
- The optional `openadlc.yaml` (project config) is covered in [config](../config/).

Back to the shared flow and the checkpoints: [Getting started](README.md).
