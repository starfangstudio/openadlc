<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
# docs build progress

Tracks the build of the docs tree that `docs/README.md` promises. One directory per firing. Every claim is verified against the actual commands, skills, references, and config in this repo before it is written. The repo is the source of truth.

## Plan

| # | Directory | What it holds | Status |
|---|---|---|---|
| 1 | `getting-started/` | One page per harness (Claude Code, Cursor, Copilot, Codex, Windsurf, Antigravity), plus a shared 5-minute path. | Done |
| 2 | `commands/` | One page per `/ai-*` command (discovery, plan, implement, review). | Done |
| 3 | `config/` | The `openadlc.yaml` reference, every key explained. | Done |
| 4 | `customize/` | Bring your own skill, your own pack, edit a checkpoint. | Done |
| 5 | `concepts/` | OKF bundles, run isolation, checkpoints, packs. | Done |
| 6 | (final) | Link-check the whole tree and reconcile `docs/README.md`. | Done |

## Sources of truth (verified against)

- `README.md`, `docs/lifecycle.md`, `docs/pack-format.md`
- `plugins/adlc-core/commands/ai-{discovery,plan,implement,review}.md`
- `plugins/adlc-core/skills/*/SKILL.md`
- `plugins/adlc-core/references/{okf,run-isolation,loop-control,orchestration,token-compression,cost-ledger,tracker-adapters}.md`
- `openadlc.example.yaml`, `apm.yml`, `.claude-plugin/marketplace.json`
- `standard/{spec,adoption,onepage,principles,pack-format,conformance}.md`
- `CONTRIBUTING.md`, `tools/docs-current.sh`, `tools/check-packs.py`

## Log

- Firing 1: built `getting-started/` (`README.md` + 6 harness pages). Verified harness list and install flow against `README.md` (lines 11, 65 to 77, 101, 127) and `standard/spec.md` (sections 1, 7). Per-harness behavior stated only where the repo supports it; where the repo is silent (exact per-harness invocation), pages point to APM and the harness rather than invent it.
- Firing 2: built `commands/` (`README.md` + one page per command). Verified every claim against the four command sources in `plugins/adlc-core/commands/`. Source-skill links: intake to its namesake skill, plan to `create-plan` (the command names it), implement to `implement-change` (the command names it), review to its namesake `ai-review` skill. Forward links to `concepts/` pages (okf-bundles, run-isolation, checkpoints) are intentional; those pages land in firing 5 and the final firing link-checks them.
- Firing 3: built `config/` (`README.md`). Verified every key against `openadlc.example.yaml`. Kept the file's own live-vs-roadmap divider: `version` and `workspace` are live in v0.1; `checkpoints`, `review`, `style`, `compression`, `packs` are declared but not yet enforced. Noted the commands reference some keys (compression default) as intended behavior while the config file marks the block roadmap, so readers are not misled. Forward links to `concepts/` and `customize/` are intentional.
- Firing 4: built `customize/` (`README.md`, `own-skill.md`, `own-pack.md`, `edit-a-checkpoint.md`). Grounded every rule in `tools/check-packs.py` (hard fails: em-dash, `${CLAUDE_PLUGIN_ROOT}` in prose, bad frontmatter, name != dir; soft warns; manifest shape), a real manifest (`plugins/adlc-core/.claude-plugin/plugin.json`), a real skill frontmatter (`create-plan/SKILL.md`), `CONTRIBUTING.md` (add-a-pack steps, tiers), `docs/pack-format.md`, and `README.md` "Make it yours" (edit-a-checkpoint points at `ai-implement.md` + its skill, verified present). Forward links to `concepts/packs.md` and `concepts/checkpoints.md` are intentional.
- Firing 5: built `concepts/` (`README.md`, `okf-bundles.md`, `run-isolation.md`, `checkpoints.md`, `packs.md`). Verified against `plugins/adlc-core/references/okf.md` and `run-isolation.md` (bundle layout, concept types, tracker serialization, run-id/workspace/branch, four workspace shapes, tracker+PR hierarchy, harness portability, dedup), `standard/spec.md` (section 4 checkpoints, section 5 packs), `standard/adoption.md` (honored vs enforced, Core/Governed), and `docs/pack-format.md` + `marketplace.json` (units, tiers, spine + domain packs). All forward links from earlier firings now resolve. Content tree complete; firing 6 link-checks the whole tree (Workflow, adversarial) and reconciles `docs/README.md`.
- Firing 6 (final): ran a Workflow, a deterministic link + em-dash sweep plus 22 adversarial per-page verifiers (one per authored page, each checking claims against the repo). Result: 133 internal links OK, 0 em-dashes, 3 "broken links" that are false positives (the literal `references/<name>.md` placeholder shown inside code fences/spans in `customize/own-skill.md` and the pre-existing `pack-format.md`, not real links, left as-is). One confirmed content fix: `customize/README.md` listed commands as a portable pack unit; corrected to "skills, agents, and references" to match `pack-format.md:37`, `concepts/packs.md`, and `own-pack.md` (commands are core-only, harness-native). Reconciled `docs/README.md`: linked the five built directories, fixed the `config/` and `concepts/` and `customize/` descriptions to match what was built, and added a pointer to `pack-format.md`. Docs tree complete and internally consistent. Note: `docs/eval-format.md` also exists (not part of this task, not authored or modified here).
