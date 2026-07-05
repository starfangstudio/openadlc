<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
# Edit a checkpoint

Each stage's steps live in plain markdown: its **command** file and the **skill** it drives. Edit those files to change what a stage does, or where it stops, including the push gate.

## Where a stage lives

A command runs the pipeline; the skill holds the procedure. For example, the implement stage:

- Command: [plugins/adlc-core/commands/ai-implement.md](../../plugins/adlc-core/commands/ai-implement.md)
- Skill: [plugins/adlc-core/skills/ai-implement/SKILL.md](../../plugins/adlc-core/skills/ai-implement/SKILL.md)

The other three stages follow the same pattern under [plugins/adlc-core/commands/](../../plugins/adlc-core/commands/) and [plugins/adlc-core/skills/](../../plugins/adlc-core/skills/). The [commands docs](../commands/) map each command to its source and skill.

## What you can change

- **The steps of a stage:** edit the numbered steps in the command or skill to change how it works.
- **Where it stops:** move, add, or adjust a checkpoint, including the push gate at the end of implement.
- **What it asks:** change the review menu, the default depth, or the method prompt (SDD or TDD).

## What not to weaken

The consent checkpoint is the point of the lifecycle. A change that removes the human yes before an outbound action breaks the discipline (and pack conformance forbids weakening the human-in-the-loop checkpoints). Tune where a stage stops; do not remove the stop before something leaves the machine. See [concepts: checkpoints](../concepts/checkpoints.md).

## After you edit

- **Keep docs in lockstep.** A change to a command or skill updates `docs/` in the same change. CI enforces it with the `docs-current` check. See [CONTRIBUTING.md](../../CONTRIBUTING.md).
- **Stay conformant.** No em-dashes, and cite references by name (no `${CLAUDE_PLUGIN_ROOT}`). Run the checker:

```bash
python3 tools/check-packs.py adlc-core
```

Green means your edit still clears the structural bar.
