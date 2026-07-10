<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
# Getting started: Cursor

[Cursor](https://cursor.com) is an AI code editor. OpenADLC runs in it as an [APM](https://github.com/microsoft/apm) target.

## Prerequisites

- Cursor, installed and working.
- [APM](https://github.com/microsoft/apm), the agent package manager.

## Install

```bash
apm install starfangstudio/openadlc
```

APM deploys the `adlc-core` spine into Cursor automatically. Update later with `apm update`.

## Run a command

APM maps the four `/ai-*` commands onto Cursor's own command mechanism. From a project root, invoke:

```text
/ai-discovery
```

Then `/ai-plan`, `/ai-implement`, and `/ai-review`. If your Cursor version surfaces these differently, follow how Cursor exposes installed commands; the OpenADLC behavior behind each is the same. See [commands](../commands/) for what each one does.

## Models and effort

Pick the model and effort in Cursor, per stage. Nothing to configure in OpenADLC for this.

## Notes

- Domain packs install on demand: `apm install adlc-web@openadlc`, and so on. See [customize](../customize/).
- OpenADLC is in early development; Claude Code is the most exercised target today. For anything specific to your agentic coding tool, see the [APM docs](https://github.com/microsoft/apm) and Cursor's own docs.

Back to the shared flow and the checkpoints: [Getting started](README.md).
