<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
# Customize

OpenADLC is opinionated where it matters (the lifecycle discipline) and open everywhere else. Three ways to make it yours:

- [**Add your own skill**](own-skill.md): drop a `SKILL.md` into a pack. It loads when its description matches the work.
- [**Add your own pack**](own-pack.md): author skills, agents, and references to the portable pack format, one manifest that APM deploys to every agentic coding tool.
- [**Edit a checkpoint**](edit-a-checkpoint.md): change what a stage does, or where it stops, by editing its command and skill files.

You can also load or disable packs from [config](../config/) (`packs.enabled` / `packs.disabled`), and pick your model and effort per stage in your agentic coding tool.

## Two rules that apply to any change here

- **No em-dashes, anywhere.** Use commas, colons, or parentheses. This is a hard fail in [`tools/check-packs.py`](../../tools/check-packs.py) and CI.
- **Docs ship with the code.** A change to a command, skill, or config updates `docs/` in the same change. CI enforces it (the `docs-current` check). See [CONTRIBUTING.md](../../CONTRIBUTING.md).

For the concepts behind packs, see [concepts: packs](../concepts/packs.md). For the full format, see [pack-format](../pack-format.md).
