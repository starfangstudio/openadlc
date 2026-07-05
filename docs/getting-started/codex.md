<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
# Getting started: Codex

[Codex](https://openai.com/codex) is OpenAI's coding agent. OpenADLC runs in it as an [APM](https://github.com/microsoft/apm) target, and Codex is named as a harness in the ADLC spec.

## Prerequisites

- Codex, installed and working.
- [APM](https://github.com/microsoft/apm), the agent package manager.

## Install

```bash
apm install starfangstudio/openadlc
```

APM deploys the `adlc-core` spine into Codex automatically. Update later with `apm update`.

## Run a command

APM maps the four `/ai-*` commands onto Codex's own command mechanism. From a project root, invoke:

```text
/ai-discovery
```

Then `/ai-plan`, `/ai-implement`, and `/ai-review`. If your Codex surface exposes commands differently, follow how it lists installed commands; the OpenADLC behavior behind each is the same. See [commands](../commands/) for what each one does.

## Models and effort

Pick the model and effort in Codex, per stage. Nothing to configure in OpenADLC for this.

## Notes

- Domain packs install on demand: `apm install adlc-web@openadlc`, and so on. See [customize](../customize/).
- OpenADLC is in early development; Claude Code is the most exercised target today. For anything harness-specific, see the [APM docs](https://github.com/microsoft/apm) and Codex's own docs.

Back to the shared flow and the checkpoints: [Getting started](README.md).
