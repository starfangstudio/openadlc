<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
# Add your own pack

A pack is a directory under `plugins/` with a manifest and its units (skills, agents, references, and, for the core, commands). One manifest that APM deploys to every agentic coding tool. **Market wide, own narrow.**

## The manifest

`plugins/<pack>/.claude-plugin/plugin.json`:

```json
{
  "name": "adlc-web",
  "version": "0.1.0",
  "license": "LicenseRef-OpenADLC-Source-Available-1.0",
  "description": "<trigger-rich one-liner: what the pack does and when to load it>",
  "author": { "name": "OpenADLC" },
  "owner": { "name": "OpenADLC", "contact": "https://openadlc.com" },
  "adlc": "0.1",
  "units": { "skills": 6, "agents": 2, "commands": 0, "references": 0 },
  "evals": "conformance",
  "capabilities": {}
}
```

What the checker requires:

- **`name`, `version`, `description`, `license`:** required, non-empty strings. `version` must be semver. `description` is at most 600 characters.
- **`adlc`, `units`, `evals`, `capabilities`:** must be present. `adlc` is the standard version the pack targets. `units` is a per-kind count object (`skills`, `agents`, `commands`, `references`). `evals` is `conformance` or `conformance+gate`. `capabilities` is an object, `{}` for guidance packs (default-deny).
- **`author`, `owner`:** optional, but shape-checked when present (`author` needs a name, `owner` needs name and contact). A certified pack must declare a reachable `owner`.

`units` is generated from the folder tree, not hand-counted. Refresh it with [`tools/migrate-manifests.py`](../../tools/migrate-manifests.py).

## Steps to add a pack

From [CONTRIBUTING.md](../../CONTRIBUTING.md):

1. **Open an issue** describing the domain and why it is not covered (intake before code; the lifecycle applies here too).
2. **Scaffold** `plugins/adlc-<name>/.claude-plugin/plugin.json` plus a `README.md` listing the skills and agents, then author the skills to the house format (see [add your own skill](own-skill.md)). Use an existing pack as the template; the `adlc-author` agent helps.
3. **Author each skill** with a trigger-rich third-person description, numbered steps, a References section, and a failable check. Detect-first; never impose a stack.
4. **Add your pack** to [`.claude-plugin/marketplace.json`](../../.claude-plugin/marketplace.json).
5. **Run the checker** until it passes, then open the PR and sign the CLA when prompted.

## The two tiers

- **Community:** valid and useful, passes the machine floor, not held to the full certified bar. Most contributions start here.
- **Certified:** a golden-path domain the project stands behind and keeps current. Full conformance plus a maintainer review.

## Verify

```bash
python3 tools/check-packs.py <name>
```

The machine floor is: this checker passes, no em-dashes anywhere, and docs ship with the code. See [pack-format](../pack-format.md) for the full unit and citation rules, and [concepts: packs](../concepts/packs.md) for how packs load on demand.
