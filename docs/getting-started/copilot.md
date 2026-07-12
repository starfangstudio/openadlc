<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
# Getting started: Copilot

[GitHub Copilot](https://github.com/features/copilot) is a coding assistant. OpenADLC runs in it as an [APM](https://github.com/microsoft/apm) target, one of the supported agentic coding tools.

## Prerequisites

- Copilot, installed and working in your editor.
- [APM](https://github.com/microsoft/apm), the agent package manager.

## Install

```bash
apm install starfangstudio/openadlc
```

APM deploys the `adlc-core` spine into Copilot automatically. Update later with `apm update`.

## Run a pipeline

APM installs four prompt files under `.github/prompts/`, agents under `.github/agents/`, and skills under `.agents/skills/`. In VS Code Copilot Chat, invoke:

```text
/ai-discovery
```

Continue with `/ai-plan`, `/ai-implement`, and `/ai-review`. Copilot CLI behavior is not yet verified. See [commands](../commands/) for what each pipeline does.

## Models and effort

Pick the model and effort in Copilot, per stage. Nothing to configure in OpenADLC for this.

## Notes

- Domain packs install on demand: `apm install adlc-web@openadlc`, and so on. See [customize](../customize/).
- OpenADLC is in early development; Claude Code is the most exercised target today. For anything specific to your agentic coding tool, see the [APM docs](https://github.com/microsoft/apm) and Copilot's own docs.

Back to the shared flow and the checkpoints: [Getting started](README.md).
