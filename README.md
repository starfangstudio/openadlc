<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
<p align="center">
  <img src="brand/openadlc-mark.svg" width="92" alt="OpenADLC">
</p>

<h1 align="center">OpenADLC</h1>

<p align="center"><b>Open standard for the <a href="https://www.ibm.com/think/topics/agent-development-lifecycle-adlc">Agentic Development Lifecycle</a>.</b></p>

<p align="center">
  Runs in the harness you already use: <b>Claude Code</b>, <b>Cursor</b>, <b>Copilot</b>, <b>Codex</b>, <b>Windsurf</b>, <b>Antigravity</b>, and other APM targets.
</p>
<p align="center">
  Built on open standards: <a href="https://agents.md">AGENTS.md</a> · <a href="https://agentskills.io">Agent Skills</a> · <a href="https://modelcontextprotocol.io">MCP</a> · <a href="https://github.com/GoogleCloudPlatform/knowledge-catalog/tree/main/okf">OKF</a>.
</p>

---

AI coding agents can and will build the wrong thing before you notice. Software development is missing the equivalent of SDLC discipline for agentic work.

OpenADLC gives AI-assisted development a repeatable path from raw input to reviewed change: intake, plan, implement, review. Each stage produces an artifact the next stage can trust, and each risky boundary requires explicit human approval.

Use your existing coding harness, repo, tools, and standards. OpenADLC adds the lifecycle around them, with a human in the loop where it matters.

## The flow

Four commands, one per human decision point. This is the lifecycle, top to bottom.

```
  /ai-discovery  ->  /ai-plan  ->  /ai-implement  ->  /ai-review
   idea to story       story to plan      plan to deliverable     deliverable to verdict
   post / refine       post sub-issue     push to remote          BLOCK / APPROVE
```

Each `post`, `push`, and outbound action is a **consent checkpoint**: a stop wherever something leaves your machine (posting an issue, posting a sub-issue, pushing a change). It holds anywhere work crosses the line, not at one fixed station. There is no `ship` command on purpose: the push checkpoint lives inside `implement`, so nothing reaches a remote without your yes. `/ai-review` is embedded in `/ai-implement` at a checkpoint that never skips: you are always asked which reviews to run before you sign off. It also works standalone on any code.

| Command | You go from | to | You decide |
|---|---|---|---|
| `/ai-discovery` | an idea, bug, or epic | a well-formed, classified story with acceptance criteria | approve the work before it is filed |
| `/ai-plan` | a story | a buildable plan, mapped slice by slice to the acceptance criteria | approve the plan before it is built |
| `/ai-implement` | a plan | a deliverable: code, each slice ending in a check that passes or fails | approve the push before code leaves your machine |
| `/ai-review` | a deliverable | an independent BLOCK or APPROVE verdict across concurrent review lenses | approve the verdict before it is posted |

Reading, local edits, local commits, and local builds never stop you. Anything outbound (a push, a deploy, a publish, an API write) waits for an explicit yes, at the checkpoint where it happens.

## Why OpenADLC

- **You hold the wheel.** A human approves the work, the plan, the push, and the verdict. Nothing leaves your machine without an explicit yes; the friction is reserved for the moments that actually carry risk.
- **The whole loop in one install.** A real intake to plan to implement to review pipeline, not a kit of parts you assemble yourself.
- **One lifecycle, any domain.** The spine is identical whether the work is web, backend, iOS, or Unity. Only the domain pack changes.
- **Yours to shape.** Opinionated on the discipline, open on everything else. Swap in your own packs, skills, and checkpoints, on a maintained, source-available foundation.

## What runs through all of it

The four commands are one machine, not four tools. A few things hold across every stage:

- **The checkpoint is everywhere.** Every outbound boundary gets a human yes: posting an issue, posting a sub-issue, pushing. Not one gate at the end, a discipline that holds across the whole pipeline.
- **The work travels as OKF bundles.** The story and the plan are [Open Knowledge Format](https://github.com/GoogleCloudPlatform/knowledge-catalog/tree/main/okf) bundles, plain typed markdown: a human briefing plus the full AI context, readable by a person and an agent alike. Each stage leaves an artifact the next can trust (implement its verify evidence, review its verdict), so the work moves between stages and trackers with no lock-in.
- **Acceptance criteria, end to end.** Intake defines them, the plan restates them and maps each slice to them, and implement checks the build against them before a human is asked to review.
- **It runs lean.** Discovery, slices, and review lenses fan out in parallel, so wall-clock time is the slowest path, not the sum.
- **Loops and agent flows, bounded.** Stages orchestrate nested sub-agents and optional loops (iterate to refine, or fan out and judge, with adversarial passes baked in). Every loop is cost-capped with declared exit criteria, so running an agent past one task is continuity, not a token bonfire.

## Get started

**Prerequisites:** a supported harness (Claude Code, Cursor, Copilot, Codex, Windsurf, Antigravity, and other APM targets) and [APM](https://github.com/microsoft/apm), the agent package manager.

Install with one command; it deploys to your harness automatically:
```bash
apm install starfangstudio/openadlc
```
Update later with `apm update`.

Then, in your harness from a project root, run your first command:
```text
/ai-discovery
```
Describe what you want to build. OpenADLC turns it into a well-formed story and waits for your yes. Then `/ai-plan`, `/ai-implement`, and `/ai-review` carry it to a reviewed deliverable, stopping at each checkpoint.

## The four commands

- **`/ai-discovery`** is the universal front door, for any role, not a PM-only surface. Feed it documents, screenshots, links, or Figma; it runs deep discovery, surfaces development dependencies, and produces a typed, classified story (a story, bug, epic, tech-debt, or intent; an epic splits into linked child stories), always with clear acceptance criteria, packaged as an OKF bundle (a human briefing plus the full AI context as typed concepts). Checkpoint: post a new tracker issue, or refine further.
- **`/ai-plan`** turns a buildable unit (a story, bug, or tech-debt, never an epic) into a full plan. It detects the domain from the repo, or asks when the work is ambiguous or spans platforms, restates the acceptance criteria, and maps each one to a slice, with the approach, flows, contracts, tests, design references, dependencies, and the cross-cutting angles that apply. One item can fan out into several plans. Checkpoint: approve or edit, then it posts a remote sub-issue.
- **`/ai-implement`** builds the plan in slices, your choice of SDD or TDD, each slice ending in a check that passes or fails. It verifies each slice, runs its own acceptance-criteria check, then stops to ask which reviews to run before you take a final look. Checkpoint: approve the push, then the pipeline ends.
- **`/ai-review`** is an independent, fresh-eyes review of correctness, safety, whether the tests actually assert anything, UI fidelity, and fit. Lenses run concurrently and it returns BLOCK or APPROVE with file-and-line evidence. Every implement stops at its review checkpoint to ask which reviews to run, and the command also stands alone on any diff, branch, PR, or code you did not write.

## One lifecycle, any domain

The spine is identical whether the work is web, backend, iOS, or Unity. Only the domain pack changes.

`adlc-core` is the always-on spine: the four commands, the lifecycle skills they call, software design, codebase research, decision records, docs, and commit linking. Around it sit domain packs that load only when the work calls for them: web, iOS, Android, backend, backend-cloud, database, desktop, Unity, plus cross-cutting design, AI/LLM, security, privacy, planning, testing, quality gates, ops, and monetization.

Worked example, "add a discount-code field to the checkout page": intake takes the Figma and the flow notes and posts a typed story; plan detects web (`adlc-web`), restates the acceptance criteria, and builds the plan with the form, validation, and the pricing API contract, plus a security threat model since it touches pricing, then posts a sub-issue; implement builds and verifies the slices, you pick code plus security review, and approve the push. Swap web for backend or iOS and the lifecycle is identical. That is the whole design.

## Make it yours

OpenADLC is opinionated where it matters (the lifecycle discipline) and open everywhere else.

- **Add your own skill.** Drop a `SKILL.md` at `plugins/<pack>/skills/<name>/SKILL.md` with a name, a trigger-rich description, and the steps. It loads when its description matches the work. See [docs/pack-format.md](docs/pack-format.md).
- **Add your own pack.** Author skills, agents, and commands to the portable [pack format](docs/pack-format.md), one manifest that APM deploys to every harness, then list it in the marketplace. See [CONTRIBUTING.md](CONTRIBUTING.md).
- **Edit a checkpoint.** Each stage's steps live in its command and skill files (for example `plugins/adlc-core/commands/ai-implement.md` and the matching `skills/ai-implement/SKILL.md`). Edit the steps to change what a stage does, or where it stops, including the push gate.
- **Pick your models** and effort in your harness, per stage, with no config to maintain.

## Built on open standards

OpenADLC does not reinvent the substrate. It composes the open building blocks the ecosystem already shares:
- **[AGENTS.md](https://agents.md)**: the cross-agent instructions format.
- **[Agent Skills](https://agentskills.io)**: the portable skill format the packs are authored in.
- **[MCP](https://modelcontextprotocol.io)**: the Model Context Protocol, for tools and context.
- **[OKF](https://github.com/GoogleCloudPlatform/knowledge-catalog/tree/main/okf)**: the Open Knowledge Format. Every intake and plan artifact is an OKF bundle, plain typed markdown that a human and an agent both read, so the story and the plan move between stages and trackers without a proprietary format in the middle.

The ADLC standard itself (the `standard/` tree) is open under CC-BY-4.0, so anyone can implement it and build conformant tools. ADLC is the vendor-neutral "what"; OpenADLC is one reference "how".

## For organizations

OpenADLC is free for individuals, including a solo freelancer on paid client work. Teams and organizations need a commercial seat. An **OpenADLC Enterprise** edition is in the works: centrally enforced checkpoints, organization policy, a tamper-evident audit trail, fleet management, private and certified enterprise domain packs, and a desktop cockpit. Full docs are coming to [openadlc.com](https://openadlc.com).

## Community

- [CONTRIBUTING.md](CONTRIBUTING.md): how to contribute, the community and certified pack tiers, and the CLA.
- [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md): the behavior we expect.
- [SECURITY.md](SECURITY.md): how to report a vulnerability.
- [SUPPORT.md](SUPPORT.md): where to get help.
- [BRAND.md](BRAND.md): using the OpenADLC name and marks.

## Status

Early development. The lifecycle runs across APM-supported harnesses through the portable pack format. The core is built with publicly viewable source and is not yet ready for general use. Expect breaking changes.

## License

OpenADLC is dual-licensed. "Open" here means an open standard, publicly viewable source, and free for individuals. It is **not** OSI open source, and we do not claim it is.

- **The ADLC standard** (the `standard/` tree): [CC-BY-4.0](LICENSE-STANDARD). A genuine open standard, free for anyone to read, implement, and build on.
- **The implementation** (`plugins/`, adapters, the harness, the four `/ai-*` commands): the [OpenADLC Source-Available License](LICENSE). Publicly viewable and free for individuals and the public to read, use, and modify. Use by a team or organization requires a commercial seat license; a solo individual, including a freelancer on client work, stays free.

Contributions are covered by a [CLA](CLA.md), checked on every pull request. "OpenADLC" and "OpenADLC Verified" are trademarks of StarFang; see [BRAND.md](BRAND.md).

---

<p align="center">OpenADLC by StarFang.</p>
