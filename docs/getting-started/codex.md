<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
# Getting started: Codex

[Codex](https://openai.com/codex) is OpenAI's coding agent. OpenADLC runs in it as an [APM](https://github.com/microsoft/apm) target, one of the supported agentic coding tools.

## Prerequisites

- Codex, installed and working.
- [APM](https://github.com/microsoft/apm), the agent package manager.

## Install

```bash
apm install starfangstudio/openadlc
```

APM deploys the `adlc-core` spine into Codex automatically. Update later with `apm update`.

## Run a pipeline

APM installs the OpenADLC skills and agents into Codex. It does not install `/ai-*` slash commands. From a project root, use Codex's skill or tool primitive to invoke the installed `ai-discovery` skill.

Continue with the installed `ai-plan`, `ai-implement`, and `ai-review` skills. These are the same four lifecycle pipelines described in [commands](../commands/); only the entry point differs.

## Models and effort

Pick the model and effort in Codex, per stage. Nothing to configure in OpenADLC for this.

## Notes

- Domain packs install on demand: `apm install adlc-web@openadlc`, and so on. See [customize](../customize/).
- OpenADLC is in early development; Claude Code is the most exercised target today. For anything specific to your agentic coding tool, see the [APM docs](https://github.com/microsoft/apm) and Codex's own docs.

Back to the shared flow and the checkpoints: [Getting started](README.md).
