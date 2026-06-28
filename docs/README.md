<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
# OpenADLC docs

This directory is the single source of truth for documentation, consumed by both this repository and the website (openadlc.com).

## The rule: docs ship with the code

Docs are written and updated as the work happens, never after. A change to a command, skill, hook, or config updates its doc in the same change. This is enforced (see [CONTRIBUTING.md](../CONTRIBUTING.md), the `docs-current` check), because stale docs are worse than no docs.

## Start here

[**The ADLC lifecycle**](lifecycle.md): the four commands, the checkpoints, the loops, and the acceptance-criteria thread, end to end. The single map of how OpenADLC works.

## Structure (as it grows)

- `getting-started/` : install, first run, the checkpoints in five minutes.
- `commands/` : the four-command harness, one page each.
- `config/` : the `openadlc.yaml` reference.
- `customize/` : bring-your-own packs, overrides, preferences.
- `concepts/` : the lifecycle, and the open standards we build on (Agent Skills, MCP, AGENTS.md).

Pages are plain Markdown so the site and the repo render the same source.
