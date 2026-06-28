<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
# Pack format

A pack is a directory under `plugins/` with a manifest and units (skills, agents, references, and the core commands). This is the format a Community or Certified pack follows. The structural bar is enforced by `tools/check-packs.py` (the conformance eval) and CI.

## The manifest (`.claude-plugin/plugin.json`)

```json
{
  "name": "adlc-web",
  "version": "0.1.0",
  "description": "<trigger-rich one-liner: what the pack does and when to load it>",
  "author": { "name": "OpenADLC" },
  "owner": { "name": "OpenADLC", "contact": "https://openadlc.com" },
  "adlc": "0.1",
  "units": { "skills": 6, "agents": 2, "commands": 0, "references": 0 },
  "evals": "conformance",
  "capabilities": {}
}
```

- **name / version / description:** required. `version` is the PACK version; units are not separately versioned (G6).
- **author:** kept for Claude Code compatibility (the harness reads it).
- **owner `{name, contact}`:** required (G2). The contact is what keeps a pack current; a certified pack needs a reachable one.
- **adlc:** the ADLC standard version the pack targets.
- **units:** generated from the folder tree (counts of skills/agents/commands/references). Run `tools/migrate-manifests.py` to refresh.
- **evals:** the eval bar the pack clears. `conformance` (the structural eval) for guidance packs; `conformance+gate` is reserved for a pack that also ships a behavioral eval; none do yet.
- **capabilities:** default-deny (G4). `{}` for guidance / markdown packs. Declare anything a unit needs beyond reading and emitting guidance.
- **license** *(live, required)*: a per-pack license identifier so each pack states its own terms, required and validated by `tools/check-packs.py` (it warns on a value outside the known vocabulary). The OpenADLC packs here use `LicenseRef-OpenADLC-Source-Available-1.0` (source-available + commercial: publicly viewable, free for individuals and the public, a commercial seat for use by a team or organization; see the `LICENSE` file). The ADLC standard in `standard/` is `CC-BY-4.0`. See the root [README](../README.md).

## Units

- **skill** (`skills/<name>/SKILL.md`): the portable, primary unit. A trigger-rich third-person description, numbered steps, a References section, and a failable check. The name must match its directory.
- **agent** (`agents/<name>.md`): a read-only subagent (architect or reviewer).
- **reference** (`references/<name>.md`): on-demand detail a skill cites. Cite it by pack-relative name, never with a harness-specific variable: same-pack as `[references/<name>.md](references/<name>.md)`, another pack's named in prose (the `references/<name>.md` reference in the **<owner>** pack). `${CLAUDE_PLUGIN_ROOT}` resolves on only one of the deploy targets, so `check-packs.py` rejects it in any prose unit; the agent locates the named file at runtime.
- **command** (`commands/<name>.md`): harness-native (the `/agentic-*` entry points); adapter-mapped per harness, not a portable unit (G7).
- **rule:** a first-class portable convention unit (G7); domain packs carry on-demand rules.

## Tiers

- **Community:** valid and useful; passes the machine floor; not held to the full certified bar.
- **Certified:** a golden-path domain we stand behind and keep current; full conformance plus a maintainer review.

See `CONTRIBUTING.md` for how to add a pack, and `tools/check-packs.py` for the bar.
