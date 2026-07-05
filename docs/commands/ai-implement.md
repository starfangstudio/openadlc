<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
# /ai-implement

Builds an approved plan end to end and stops at the push checkpoint. The procedure lives in the [`implement-change`](../../plugins/adlc-core/skills/implement-change/SKILL.md) skill.

| | |
|---|---|
| **Takes** | the approved dev-plan sub-issue (or a slice to start with) |
| **Produces** | the change, built, verified, reviewed, and pushed on your yes |
| **Checkpoints** | the review ask (mandatory), then the push (explicit yes) |
| **Feeds** | [`/ai-review`](ai-review.md) (embedded) |

## How to run

```text
/ai-implement <the dev-plan sub-issue (URL/#number)>
```

A plan must exist and be approved. If none does, it stops and tells you to run [`/ai-plan`](ai-plan.md) first. It never improvises a plan.

## What it does

1. **Loads the plan** from the sub-issue, selected by run-id, and reassembles the plan bundle. It marks the sub-issue in-progress (a local tracker write, no push). See [concepts: run isolation](../concepts/run-isolation.md).
2. **Asks you: SDD or TDD.** Spec-driven (build to the spec and criteria, then pin with tests) or test-driven (the failable check first, build to green). This is a mandatory ask, not a default.
3. **Builds in small slices** on the run branch `adlc/<run-id>`, using the domain pack's action skills. It honors the development dependencies the plan carried. Each slice ends in a **failable check**: a unit or integration test for logic, a fidelity and design-system check for UI (against the plan's Figma baseline), a smoke or plan check for config.
4. **Verifies each slice** and shows the diff and the passing evidence. A change with no failable check is not verified.
5. **Runs the acceptance-criteria check** (automatic, the AI's own definition of done): it judges the built slices against the criteria, met / partial / not met, with `path:line` evidence. A visual or behavioral criterion is "met" only after a **real run with saved evidence** (web: a dev-server smoke plus a saved screenshot; native: build, install, and launch on a sim or emulator plus a saved screenshot). A green build or a preview render is not enough. If any criterion is unmet, it closes the gap and re-checks rather than waving it into review.

## The checkpoints

**Review checkpoint (mandatory, never skipped).** It stops and asks two things:

- **Which reviews to run:** code (recommended default), security, compliance, adversarial lenses, design / UI fidelity, or none (only for trivial changes).
- **Depth:** one pass, or a bounded loop. For a loop it states the cap, ceiling, and exit criterion first.

It runs the picked reviews in parallel via [`/ai-review`](ai-review.md), persists each verdict to the run workspace, and you take a final look.

**Push checkpoint.** The push is outbound. It presents exactly what would go out (every repo, branch, and PR) and waits for your explicit yes. On yes it pushes each repo's `adlc/<run-id>` branch and opens one PR per repo, linked to the sub-issue. The pipeline ends here. There is no separate ship command.

## Source

- Command: [plugins/adlc-core/commands/ai-implement.md](../../plugins/adlc-core/commands/ai-implement.md)
- Skill: [plugins/adlc-core/skills/implement-change/SKILL.md](../../plugins/adlc-core/skills/implement-change/SKILL.md)
