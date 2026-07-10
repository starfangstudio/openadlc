<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
# OpenADLC docs

This directory is the single source of truth for documentation, consumed by both this repository and the website (openadlc.com).

## The rule: docs ship with the code

Docs are written and updated as the work happens, never after. A change to a command, skill, or config updates its doc in the same change. This is enforced (see [CONTRIBUTING.md](../CONTRIBUTING.md), the `docs-current` check), because stale docs are worse than no docs.

## Start here

[**The ADLC lifecycle**](lifecycle.md): the four commands, the checkpoints, the loops, and the acceptance-criteria thread, end to end. The single map of how OpenADLC works.

## Structure

- [`getting-started/`](getting-started/) : install, first run, the checkpoints in five minutes, one page per agentic coding tool.
- [`commands/`](commands/) : the four /ai-* commands, one page each.
- [`config/`](config/) : the `openadlc.yaml` reference.
- [`customize/`](customize/) : bring your own skill or pack, and edit a checkpoint.
- [`concepts/`](concepts/) : OKF bundles, run isolation, checkpoints, and packs.

Deeper reference: [`pack-format.md`](pack-format.md), the pack wire format that [`customize/`](customize/) builds on, and [`eval-format.md`](eval-format.md), the behavioral-eval format the pack eval suites follow.

Pages are plain Markdown so the site and the repo render the same source.
