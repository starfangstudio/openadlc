<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
# Getting started: Antigravity

[Antigravity](https://antigravity.google) is Google's agentic IDE. OpenADLC runs in it as an [APM](https://github.com/microsoft/apm) target.

## Prerequisites

- Antigravity, installed and working.
- [APM](https://github.com/microsoft/apm), the agent package manager.

## Install

```bash
apm install starfangstudio/openadlc
```

APM deploys the `adlc-core` spine into Antigravity automatically. Update later with `apm update`.

## Run a command

APM maps the four `/ai-*` commands onto Antigravity's own command mechanism. From a project root, invoke:

```text
/ai-discovery
```

Then `/ai-plan`, `/ai-implement`, and `/ai-review`. If your Antigravity version surfaces these differently, follow how it exposes installed commands; the OpenADLC behavior behind each is the same. See [commands](../commands/) for what each one does.

## Models and effort

Pick the model and effort in Antigravity, per stage. Nothing to configure in OpenADLC for this.

## Notes

- Domain packs install on demand: `apm install adlc-web@openadlc`, and so on. See [customize](../customize/).
- OpenADLC is in early development; Claude Code is the most exercised target today. For anything harness-specific, see the [APM docs](https://github.com/microsoft/apm) and Antigravity's own docs.

Back to the shared flow and the checkpoints: [Getting started](README.md).
