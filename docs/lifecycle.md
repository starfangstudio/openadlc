<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
# The ADLC lifecycle

OpenADLC is four commands and a law. The commands carry a task from a fuzzy idea to pushed code; the law (a human owns the release decision) makes sure nothing leaves your machine without you saying yes.

```
idea ──/ai-discovery──▶ intake fuel ──/ai-plan──▶ sub-issue ──/ai-implement──▶ pushed
            (◆ post)        (story / bug / epic        (◆ post)                  (◆ push)
                             / tech-debt / intent)
                                                              └ /ai-review (embedded, checkpoint never skips)
```

`◆` = a consent checkpoint. Intake fuel is classified (story / bug / epic / tech-debt / intent), never just "a story". An **epic is split at intake into linked child stories**; `/ai-plan` works those stories, never the epic (too high-level to hold the specs). One piece of fuel can fan out into several plans. `/ai-review` also runs standalone, on any code.

## The four commands

| Command | Takes | Produces | Checkpoint |
|---|---|---|---|
| `/ai-discovery` | an idea + docs / screenshots / links / Figma, from any role | **intake fuel** (story / bug / epic / tech-debt / intent) as an OKF bundle (a human briefing + the full AI context as typed concepts), with acceptance criteria and surfaced dev dependencies | post the fuel, or refine |
| `/ai-plan` | intake fuel / issue | a **dev plan** (one or more) + a remote sub-issue | approve / edit / refine, then post |
| `/ai-implement` | an approved sub-issue | the change, **built, reviewed, pushed** | the push |
| `/ai-review` | a diff / branch / PR / any code | a **BLOCK / APPROVE** verdict | post the verdict (only if you ask) |

## Four things run through all of it

1. **The consent checkpoint is everywhere.** Every outbound boundary (posting intake fuel, posting a sub-issue, pushing, posting a review) needs an explicit human yes. It is a law, not a single station: at each boundary the agent stops, presents exactly what would leave your machine, and waits for your yes.
2. **One bundle, two jobs.** Every piece of intake fuel and every plan ships as one OKF bundle: `briefing.md` built for **comprehension** (a cold reader gets it at a glance, so the operator stays in the loop) plus the typed AI concepts built for **completeness** (every detail, so the build does not deviate). Too thin, the agent guesses and drifts; too AI-first, the human is locked out and the loop becomes theater.
3. **Two dials per checkpoint.** Consent (approve / edit / reject) and rigor (one pass, or a bounded operator-set loop). Default one pass; depth is opt-in and always capped. This is how adversarial loops are baked into the lifecycle.
4. **Acceptance criteria, end to end.** Intake defines them, the plan restates them and maps each slice to them, implement checks the build against them before any review.

---

## /ai-discovery: idea to intake fuel

The universal front door, for any role: dev, manager, tech owner, product owner, QA. Turns a fuzzy idea, with whatever evidence you have, into clean, postable, classified intake fuel. It runs as a deep-planning conversation (no arguments needed), keeps a living reference doc as you plan, and produces the fuel only when you say you are done. It anchors on the target repo + tracker first (asking which if the working dir is not a single git repo). Writes no code and no plan, and does not choose the domain.

**Input:** none required, run it bare to start the planning conversation; or seed it with an idea, files, links, or Figma URLs.

**Steps**
1. **Gather** everything. If the idea is too thin, ask 2-3 sharp questions first. If a Figma or design surface is in play, note it so the plan loads `adlc-design` on-demand.
2. **Deep discovery** (one pass, or a bounded loop): what exists, what it touches, the constraints, the risks, and the **development dependencies** (what must land first, what this blocks, the systems it couples to). Read-only; cite what you find.
3. **Classify the fuel** as one of: story / bug / epic / tech-debt / intent. Never just "a story".
4. **Write the fuel as an OKF bundle:** a human briefing (`briefing.md`) plus the full AI context as typed concepts (`story.md`, `discovery.md`, `dependencies.md`), per [the OKF reference](../plugins/adlc-core/references/okf.md).
5. **Always define acceptance criteria**, for any item type:
   - **Story / feature:** the observable behavior that must be true when done.
   - **Bug:** the bug no longer reproduces, the correct behavior, a regression guard.
   - **Epic:** the outcome that holds when its child stories are all done. Intake splits the epic into those **linked child stories** (each a story with its own AC); `/ai-plan` works the stories, not the epic.
   - **Tech debt:** the target state and the measurable improvement, nothing else regressing.
   - **Intent:** the goal and the constraints it must respect, before it is sliced into work.
6. **Consent checkpoint: post or refine.** Post the fuel to the tracker as a new issue (outbound, needs a yes), or refine it with another discovery pass.

**Output:** intake fuel (classified, an OKF bundle, acceptance criteria, surfaced dev dependencies), posted, feeding `/ai-plan`.

---

## /ai-plan: intake fuel to plan

Turns intake fuel into a buildable plan, the complete contract for the build. Authors nothing itself; the plan is written by the `create-plan` skill. One piece of fuel can fan out into several plans.

**Input:** a plannable unit, a story, bug, or tech-debt (text, a file, or a tracker issue). Not an epic (plan its child stories) or a bare intent (discovery first).

**Steps**
1. **Resolve** the input; it must be a plannable unit (story / bug / tech-debt). An epic is too high-level, redirect to its child stories; an intent needs discovery first. Pull in the acceptance criteria, the surfaced dev dependencies, any layout intent, and the discussion.
2. **Detect or ask the domain** (web, backend, android, ios, unity, ...) and load that pack. Detect from the repo when it is clear; **ask** when it is ambiguous, the repo is empty, or the fuel spans platforms or layers (FE + BE, android + ios, windows + macos). A cross-platform piece fans out into one plan per domain. Load a cross-cutting pack (security, privacy, AI) when relevant. Load `adlc-design` only when the fuel mentions Figma or a design surface.
3. **Explore** read-only (`codebase-researcher`).
4. **Plan** (`create-plan`): **restate the acceptance criteria**, then slices with each criterion mapped to a slice, flows (happy + error), contracts, design refs, tests, the **carried dev dependencies** (and any layout intent from intake), and the **cross-cutting concerns that apply** (security, accessibility, automation / CI, performance, privacy, i18n, observability), each routed to its pack, plus the .md / .json artifacts the implementer consumes. The plan is a complete contract and **maps each slice to the criteria it satisfies**.
5. **Plan-approval checkpoint: approve / edit / refine.** Approve as written, edit scope / approach / rollback, or refine with a bounded loop (iterate, or fan out a few approaches and judge).
6. **Post the sub-issue** (on yes, outbound): the briefing is the visible body. On GitHub the AI concepts ride inline in a collapsible block (overflow into comments); on Jira the bundle is attached as a tarball. The source bundle stays in the out-of-repo run workspace (`~/.openadlc/runs/<workspace>/<run-id>/plan/`, never committed); see [the OKF reference](../plugins/adlc-core/references/okf.md).

**Output:** an approved plan (or several), each a complete contract carrying the dev dependencies, plus a remote sub-issue, feeding `/ai-implement`.

---

## /ai-implement: plan to pushed

Builds an approved plan end to end and ends at the release checkpoint (the push). The procedure lives in `implement-change`.

**Input:** the dev-plan sub-issue.

**Steps**
1. **Load** the plan from the sub-issue (read-only), including the carried dev dependencies it must honor (build order, what blocks what). No approved plan, no build.
2. **Choose the method, then build in slices** (`implement-change`). First ask the operator: **SDD or TDD** (spec-driven, or test-first), their choice. Each slice ends in a failable check: a unit / integration test for logic, a fidelity + design-system check for UI (`adlc-design`, compared to the Figma baseline), a smoke / plan check for config / IaC. For UI, re-fetch the live design first and flag drift from the plan's baseline before building.
3. **Verify** each slice with that failable check.
4. **Acceptance-criteria check** (automatic, the AI's definition of done): judge the built slices against the criteria, met / partial / not met, with `path:line` evidence. For UI, this includes comparing rendered screenshots (device / browser / desktop) against the Figma baseline. Only proceed if the AI judges the job done; otherwise close the gap and re-check, or surface a blocker. No human attention is spent reviewing unfinished work.
5. **Review checkpoint** (mandatory, never skipped; stop and ask): (a) which reviews (code / security / compliance / adversarial / design-UI / none), (b) depth (one pass or a bounded loop).
6. **Run** the picked reviews. **The operator takes a final look.**
7. **Release checkpoint: the push.** Outbound, explicit yes, no standing approval. The pipeline ends here; there is no separate ship command.

**Output:** the change, built, reviewed, and pushed on your yes.

---

## /ai-review: change to verdict

Independent, fresh-eyes review. Runs **embedded** inside implement (the review checkpoint never skips; you are always asked which reviews to run) and **standalone** on any code.

**Review types (pick one or more):** code (default), security, compliance, adversarial lenses, design / UI fidelity, none (trivial only). For UI, design fidelity is itself a compliance question (did the build match the approved design?), checked by comparing rendered screenshots against the Figma baseline.

**Output:** a `BLOCK / APPROVE` verdict with `path:line` evidence. Posting the verdict back is outbound and stops at the consent checkpoint.

---

## Checkpoints and asks

A **checkpoint** is a mandatory step that never skips. Some are **automatic** (verify, the acceptance-criteria check), some **ask** the operator (SDD / TDD, which reviews), some are **consent checkpoints** (an outbound yes). A consent checkpoint is the outbound kind of checkpoint, where the agent presents what would leave your machine and waits for your yes; not every checkpoint is a consent checkpoint, and not every checkpoint asks you anything.

## The loop control

Every operator-facing checkpoint offers two dials: **consent** (whether to proceed) and **rigor** (how hard to push first). Rigor is a bounded, operator-set loop in one of two flavors:

- **Iterate (refine):** run again on the last output. Stop when a round adds nothing, or at the cap.
- **Fan out and judge (diversify):** run N independent attempts, then pick or synthesize the best.

The bound is not optional: before it runs, a loop declares its exit criteria (a fixed cap, or "until converged" defined as two empty rounds), a hard ceiling it cannot exceed, and a staged escalation so depth is added only while it keeps finding something new. Loops fan out wherever there is no data dependency (N attempts, N lenses, the slices in a wave run concurrently, then a judge). Default is one pass. An unbounded or automatic loop is the runaway this design exists to prevent. Full text: [loop-control.md](../plugins/adlc-core/references/loop-control.md).

## How it runs: parallel and lean

The lifecycle is built to be fast and lean, not just correct. Two execution rules run through every command:

- **Parallel by default.** Wherever there is no data dependency, fan out: intake's discovery and plan's exploration spread across read-only agents, implement runs the slices in a wave concurrently (worktrees isolate them), review runs its lenses in parallel, and loops fan out their attempts. Flows nest and scale to the work. Wall-clock approaches the slowest path, not the sum.
- **Lean by default.** Loops declare a round cap and a hard ceiling; UI builds reach the screen via a planned fast route instead of flailing; heavy reads go to subagents to keep the main context lean. Fast, high-quality, and lean is the bar; a loop or build that runs away is a bug.
- **Compressed where it is free.** AI-internal and inter-agent output is compressed (technique adapted from Caveman, MIT, reimplemented natively, on by default at `lite`); the human-facing artifacts (story, plan, review, consent) are never compressed. See [token-compression.md](../plugins/adlc-core/references/token-compression.md).

See [orchestration patterns](../plugins/adlc-core/references/orchestration.md).

## Domain packs, on-demand

`adlc-core` is always on (the four commands, the lifecycle skills, the consent checkpoint). Everything else loads when the work calls for it: the domain pack by detected domain (android, ios, backend, unity, web, ...), a cross-cutting pack when relevant (security, privacy, ai, design). The `adlc-design` pack and its Figma skills load **only** when the issue mentions Figma or a design surface, never otherwise. Figma is the only supported design tool for now. Because designs are volatile (a design-system update overnight, half a screen changed on a call), the pack pins a dated screenshot baseline at plan time and re-checks the live design at implement time, flagging any drift.

## Implementation method: SDD or TDD, your choice

At the start of `/ai-implement` you pick the method for this build; it is the operator's call, not a default:

- **TDD (test-driven):** per slice, the failable check first, build to green, refactor.
- **SDD (spec-driven):** per slice, build to the spec and acceptance criteria, then write the tests that pin the behavior.

Either way the slice ends in a failable check. The check generalizes; it is not always a unit test:

| Work | The failable check |
|---|---|
| Logic / API / data | a unit or integration test |
| UI from a design | a fidelity + design-system check (pixels, tokens, components) vs the Figma baseline |
| Config / IaC | a plan / dry-run or smoke check |
| Spike / throwaway, docs-only | none; say so |

## The consent checkpoint (and the law)

The push is the obvious checkpoint, but it is not the only one. Posting intake fuel, posting a sub-issue, and posting a review verdict are all outbound, and each stops at a consent checkpoint. The law (Law L1: a human owns the release decision) holds at every boundary where something would leave your machine: the agent stops, presents exactly what would go out, and waits for your explicit yes. It is a step the agent performs, not a toggle or a setting, and it is intrinsic to the lifecycle. Reading, local edits, local commits, and local builds and tests are never stopped.

---

## Worked example: a new Android setting, designed in Figma

1. `/ai-discovery` with the Figma link and a sentence. Deep discovery against the app, dev dependencies surfaced. Out: intake fuel classified as a story, as an OKF bundle, with acceptance criteria, the Figma noted. **Consent checkpoint: you post it to GitHub as a new issue.**
2. `/ai-plan` on the issue. Detects Android (it would ask if the surface were ambiguous or spanned platforms), loads `adlc-android`; sees Figma, loads `adlc-design`. `create-plan` restates the criteria, writes the slices, carries the dev dependencies and layout intent, and maps each slice to a criterion. **Plan-approval checkpoint: you approve.** It posts a sub-issue with the plan attached.
3. `/ai-implement` against the sub-issue. Builds the slices with your chosen method, SDD or TDD (UI slices checked for token / component / pixel fidelity against the Figma baseline), verifies each, then the **AC check** confirms every criterion is met. **Review checkpoint:** you pick code + design-UI. You take the final look. **Release checkpoint: you approve the push.** Pipeline ends.

---

The per-command source (the exact runtime instructions) lives in [plugins/adlc-core/commands/](../plugins/adlc-core/commands/). This page is the map; those files are the territory.
