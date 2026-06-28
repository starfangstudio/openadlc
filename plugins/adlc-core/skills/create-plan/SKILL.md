---
name: create-plan
description: "This skill should be used when the user asks to \"plan\" a feature or change, \"scope\" work, \"write a spec\", \"design an approach\", or before implementing anything non-trivial. Produces an approved, self-contained plan an implementer can execute without re-asking."
version: 0.1.0
---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# Create a plan

Produce a precise, self-contained plan and get it approved **before** implementation. A good plan is the single biggest lever on output quality.

The input is a **plannable unit** of intake fuel: a story, a bug, or tech-debt. An **epic** is not plannable (too high-level to hold the specs, plan its child stories, which intake already split out), and a bare **intent** is not either (it needs discovery to become a story first). A plan **detects-or-asks the domain** (it is not chosen upstream): detect it from the repo, and **ask** when it is ambiguous, the repo is empty, or the story spans platforms or layers (FE+BE, android+ios, windows+macos). One story can fan out into several plans, one per domain. The plan **carries the development dependencies** surfaced in intake's deep discovery (and any captured layout intent) forward, so nothing the front door learned is lost.

**One plan + one sub-issue per DOMAIN.** A story fans out to one plan per domain (web, backend, android, ...), and each domain plan maps to one tracker sub-issue under the parent story (the tracker + PR hierarchy in [references/run-isolation.md](references/run-isolation.md)). In a poly-repo product a single domain may span several repos: each domain plan **names the repos it touches** and their **cross-repo dependency order** (base/shared repos before their consumers, e.g. `shared-components` before `web-app`), so implementation knows the merge sequence. The run-id is **workspace-level**, one id shared across every domain plan and every repo the run touches.

## Workflow

Copy this checklist and track progress:
```
Plan progress:
- [ ] Understood the plannable unit (story / bug / tech-debt, not an epic or bare intent); ambiguities surfaced
- [ ] Detected or asked the domain (one story can fan to several plans; one plan + one sub-issue per domain)
- [ ] Named the repos this domain touches and their cross-repo dependency order (poly-repo product)
- [ ] Explored the relevant code (read-only); facts cited
- [ ] Carried the development dependencies (and any layout intent) from intake into the plan
- [ ] Restated the acceptance criteria; mapped each to the slice(s) that satisfy it
- [ ] Wrote the required sections: context, acceptance criteria, approach, dependencies, flows, contracts, design refs (UI), validation, constraints, scope, risks
- [ ] Broke the work into slices; mapped each slice to the acceptance criteria it satisfies and gave it a failable check
- [ ] Re-opened every file the plan claims to touch; confirmed it exists
- [ ] Marked unknowns as [NEEDS INPUT: …]; invented nothing
- [ ] Operator approved or corrected the plan; Status set to approved
```

- **Precondition:** if a fresh `~/.openadlc/runs/<workspace>/<run-id>/context.md` from `load-context` exists for this work, read it before exploring; skip re-deriving anything it already covers and explore only what it leaves open. Reuse that run's run-id; do not mint a new one.

1. **Detect or ask the domain.** Read the intake fuel and detect the domain from the repo (build files, language, framework, layout). **Ask** when it is ambiguous, the repo is empty, or the story spans platforms or layers (FE+BE, android+ios, windows+macos). The domain is decided here, not upstream; when a story spans more than one, fan it out into one plan per domain.
2. **Explore read-only.** Investigate the relevant code before proposing anything. Cite findings as `path:line`. Mark anything unverified as `unknown`; never invent facts.
3. **Interview if needed.** For larger features, ask the operator about edge cases, UX, and trade-offs they may not have considered. Don't ask what the code already answers.
4. **Carry the dependencies.** Pull the development dependencies surfaced in intake's deep discovery (and any captured layout intent) into the plan, so the implementer inherits everything the front door learned.
5. **Write the required sections** (below) and the slice breakdown.
6. **Verify the plan against reality.** Re-open every file the Approach claims to touch and confirm it exists at the cited path. A plan that references a file that isn't there is a hallucination; fix it before presenting.
7. **Get approval.** Present the plan; the operator approves or corrects it. On approval, set `Status: approved <date>` in `spec.md`. Do not start implementing until the status is approved.

## Required sections

A complete plan leaves the implementer needing nothing more. Include every section that applies; a "where applicable" section is skipped only when genuinely irrelevant, and the skip itself shows it was considered.

- **Context**: why this work is needed and the problem it solves. Two-plus sentences or a linked task. "Clean up the code" is not acceptable.
- **Acceptance criteria**: **restate the acceptance criteria** from the intake fuel as a testable list. Each criterion is checkable, and each is **mapped to the slice(s) that satisfy it**. This is the definition of done the implement step checks the build against.
- **Approach**: specific enough that an implementer can start without asking questions. Name the files / interfaces involved; include ordering (lowest- to highest-risk).
- **Dependencies**: the **development dependencies carried from intake's deep discovery** (upstream services, shared modules, migrations, other in-flight stories, infra or access this work blocks on). Restate each so the implementer inherits it; required even if the answer is "none", it shows the carry happened. For a poly-repo product, also state the **repos this domain touches** and their **cross-repo merge order** (base/shared repos before their consumers), so `implementation-lead` can sequence the multi-PR merge (per [references/run-isolation.md](references/run-isolation.md)).
- **Flows** (where applicable): the **happy flow** step by step, and the **error / edge flows** that apply (failure, invalid input, empty, permission denied, offline, timeout). For UI, include the states: loading, empty, error, success, permission.
- **Contracts** (where applicable): the data shapes, API request / response, types, and `.json` schemas the slices build against.
- **Design refs** (UI only): the Figma node links and the **downloaded image as a dated fidelity baseline** (version / timestamp pinned), written to this run's `~/.openadlc/runs/<workspace>/<run-id>/design-baseline/<node>.png` (never a bare `design-baseline/`). Designs are volatile (a design-system update overnight, half a screen changed on a call), so the baseline is dated and `/agentic-implement` re-checks the live design for drift before building. Also specify, so the build does not flail: **what to mock** (seeded data, auth state, flags, stubbed backend) and the **fastest route to the screen** (deep link, preview / storybook route, seeded navigation) so the running screen can be rendered and screenshotted cheaply, and **which viewport(s) / devices** to capture for the fidelity diff. Capture the per-node **layout intent** (resize mode + constraint), bound tokens, the Code Connect component, and instance overrides (the `figma-extract` bundle), so the implementer can translate, not transcribe. When intake already captured layout intent, the plan **carries it forward** rather than re-deriving it.
- **Validation**: the exact **failable checks** that prove correctness, per slice and end to end. Module-specific, not a generic suite. For UI, the check is a fidelity + design-system comparison against the baseline.
- **Constraints**: what must NOT be touched (modules, files, patterns). Required even if the answer is "none", it shows it was considered.
- **Scope**: the smallest unit that works; state and justify anything wider, and list what is explicitly out of scope.
- **Risks & rollback** (where applicable): new dependencies, migrations, breaking changes, and how to roll back.
- **Cross-cutting concerns** (where applicable, route each to its pack): **security** (threat surface, authz, input validation, secrets), **privacy / data** (PII, consent, retention), **accessibility** (for UI: contrast, focus order, screen-reader labels, WCAG), **performance** (budgets, hot paths), **automation** (the CI this change needs: tests, lint, build, deploy wiring), **i18n** (localizable strings, RTL), **observability** (what to log or measure). Name the ones that apply and how each is met; explicitly note the ones that do not, so the skip is a decision, not an oversight.

If anything stays unclear after exhausting questions, produce the best plan you can and mark gaps `[NEEDS INPUT: <what's missing>]`.

## Slice breakdown (Plans.md)

Decompose the Approach into thin vertical slices, each independently shippable and verifiable. Use the SPIDR lens to split: by **S**pike (de-risk an unknown), **P**ath (happy path then alternates), **I**nterface (one input/UI at a time), **D**ata (one data variant), or **R**ules (one business rule at a time). Each slice gets: a one-line goal, the files it touches, the **acceptance criterion it satisfies**, and its own **failable check** (the test, or for UI the fidelity check) as the pass/fail verification command.

**Tag every slice for parallelism.** After the verify command, append:
- `[parallel-safe] deps: none` if no prior slice's output is required.
- `[sequential] deps: S1, S3` listing every slice that must finish first.

Group slices into **execution waves**: a wave is the maximal set of slices whose deps are all satisfied by completed prior waves. The implementer (or a fan-out subagent pattern from the orchestration doctrine) can run all slices in a wave concurrently. See [references/orchestration.md](references/orchestration.md) for fan-out, parallel-barrier, and pipeline patterns.

Write the breakdown to `~/.openadlc/runs/<workspace>/<run-id>/plan/Plans.md` (beside `spec.md`) as a checklist:

```
# Plans: <feature>
- [ ] S1 <goal>, files: …, AC: <criterion>, verify: `<cmd>` [parallel-safe] deps: none
- [ ] S2 <goal>, files: …, AC: <criterion>, verify: `<cmd>` [parallel-safe] deps: none
- [ ] S3 <goal>, files: …, AC: <criterion>, verify: `<cmd>` [sequential] deps: S1, S2

# Wave map
Wave 1 (parallel): S1, S2
Wave 2 (parallel): S3
```

## Output

Write `spec.md` and `Plans.md` to **`~/.openadlc/runs/<workspace>/<run-id>/plan/`**, the out-of-repo per-run workspace from [references/run-isolation.md](references/run-isolation.md). If `load-context` already minted a run-id for this work (a `~/.openadlc/runs/<workspace>/<run-id>/context.md` exists), reuse it; otherwise this is the first writing step, so mint the run-id ONCE here (`<slug>-<UTC-timestamp>`) and carry it forward. One source of truth the implementer and reviewer share, selected downstream by run-id, never by feature-name glob. Put it at that path, **not** the repo root, the repo's `.claude/`, or any slug-only path.

The plan is NEVER committed and never lives in git: only the code change ships (on `adlc/<run-id>`, as one PR), per [references/run-isolation.md](references/run-isolation.md). The implementer (in any worktree) reads the plan from the stable absolute `~/.openadlc/runs/<workspace>/<run-id>/` path; it does not need to travel in the repo. The out-of-repo workspace is itself the audit trail of what was approved.

`spec.md` starts with a frontmatter the implementer can verify in a later session. Record the `run_id` and the run branch (`adlc/<run-id>`, branched from `origin/<default>` per run-isolation), so downstream steps select this plan by run-id:

```markdown
---
feature: <name>
run_id: <slug>-<UTC-timestamp>
branch: adlc/<run-id>
status: draft        # -> approved <date> on operator sign-off
created: <date>
---
```

Keep observed-vs-assumed honest: unobserved claims stay marked `unknown`, not promoted to fact.

## References

- Run isolation (run-id, per-run workspace, run branch, worktree, dedup): [references/run-isolation.md](references/run-isolation.md)
- Parallelism doctrine (fan-out, pipeline, parallel-barrier, loop-until-dry, adversarial-verify panel, judge-panel, multi-modal sweep): [references/orchestration.md](references/orchestration.md)
