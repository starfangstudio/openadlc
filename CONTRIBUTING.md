<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
# Contributing to OpenADLC

Thanks for helping build a disciplined, open layer for agentic coding.

## The lifecycle

OpenADLC is built the way it asks you to build: intake, plan, implement, review. For anything non-trivial, open an issue first so the plan is agreed before the code.

## Contributor License Agreement (CLA)

Contributions are accepted under a Contributor License Agreement, checked on every pull request (CLA Assistant gates the PR; sign once and you are cleared for future PRs). The CLA grants StarFang the rights needed to offer the commercial seat license on the source-available implementation, while you keep ownership of your work.

The full CLA text is in `CLA.md`.

## Pull requests

- Keep changes small and focused. One concern per PR.
- Tests are first-class. A change to behavior comes with a test that proves it.
- Match the surrounding code. Prefer deleting lines over adding them.
- No AI-generated timelines or effort estimates in docs or PRs.

## Docs are not optional

Documentation lives in `docs/` and is the single source for both this repo and the website. **A change to a command, skill, hook, or config updates its docs in the same PR.** CI enforces it: a PR that touches `commands/`, `hooks/`, or `openadlc.example.yaml` without touching `docs/` fails the `docs-current` check. Keep them in lockstep. Stale docs are a bug.

## Contributing a pack

OpenADLC is a marketplace. New domains and stacks come from the community; we curate and certify. **Market wide, own narrow.**

**The two tiers:**
- **Community pack:** valid and useful, not held to the full certified bar. It must pass the machine floor (below) and not break the marketplace. Most contributions start here.
- **Certified pack:** a golden-path domain we stand behind and keep current. Full conformance plus a maintainer review. Reserved for the domains OpenADLC commits to.

**The machine floor (CI must be green, see `.github/workflows/ci.yml`):**
1. **Conformance:** `python3 tools/check-packs.py <your-pack>` passes (valid frontmatter, a skill name matching its directory, a manifest with name/version/description).
2. **No em-dashes** anywhere (commas, colons, parentheses instead).
3. **Docs ship with the code:** a change to a command, hook, or config updates `docs/` in the same PR.

**To add a pack:**
1. Open an issue describing the domain and why it is not covered (intake before code; the lifecycle applies to us too).
2. Scaffold `plugins/adlc-<name>/.claude-plugin/plugin.json` + a `README.md` listing the skills and agents, then author the skills to the house format. Use any existing pack as the template (e.g. `adlc-web`); the `adlc-author` agent helps.
3. Each skill: a trigger-rich third-person description, numbered steps, a References section, and a failable check. Detect-first; never impose a stack.
4. Add your pack to `.claude-plugin/marketplace.json`.
5. Run `python3 tools/check-packs.py <name>` until it passes, then open the PR and sign the CLA when prompted.

We review the machine floor first, then quality and scope (does it overlap an existing pack, are the boundaries clean). Certification is a separate, later step.

## License

OpenADLC is dual-licensed: the `standard/` tree is CC-BY-4.0 (a genuine open standard), and the implementation (`plugins/`, hooks, adapters, the harness, the four `/agentic-*` commands) is under the OpenADLC source-available license (see the `LICENSE` file). By contributing you agree to the CLA above, which licenses your work under these terms and grants StarFang the rights needed to offer the commercial seat license.
