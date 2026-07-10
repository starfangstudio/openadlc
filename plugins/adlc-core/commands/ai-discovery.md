---
description: "This command should be used when the user types \"/ai-discovery\" (with or without arguments), or asks to \"start a story\", \"file a bug\", \"scope an epic\", \"do discovery\", \"turn this idea/Figma/screenshots/ticket into something buildable\", \"write up an intent\", or enters planning mode with documents, links, or designs. The UNIVERSAL front door for anyone (developer, manager, tech owner, product owner, QA): it opens a deep-planning conversation, keeps a living reference doc as you plan, figures out the work and its development dependencies, and on your \"done\" outputs proper intake fuel, a story / bug / epic / tech-debt / intent as an OKF bundle (a human briefing plus the full AI context as typed concepts, with acceptance criteria), posted as a new tracker issue ready for /ai-plan."
argument-hint: "[optional: an idea, files, links, Figma URLs; or run bare to start planning together]"

---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# /ai-discovery

The universal front door to the lifecycle. Anyone (a dev, a manager, a tech owner, a product owner, a QA) uses it to turn an idea into proper **intake fuel** for the pipeline. It runs as a **deep-planning conversation**: you talk the task through, it investigates alongside you and keeps a living reference doc updated, and only when you say you are done does it produce the task and offer to post it. It writes no code and no plan; it produces what `/ai-plan` turns into a plan.

When a `references/<name>.md` link does not resolve relative to this file, locate it under the deployed adlc-core pack (search for the file name, e.g. under `apm_modules/*/adlc-core/references/`) and READ the referenced file before acting on its rule.

**Runs with no arguments.** `/ai-discovery` on its own starts the conversation. If you pass an idea, files, or links up front, they seed the conversation instead of starting from a blank page.

## 0. Domain activation
Before anything else, resolve which domain packs load for this run, by running the three-stage funnel from [standard/domains.md](../../../standard/domains.md) (this command CALLS that procedure; it does not reimplement the detector). Every step writes to the run's `~/.openadlc/runs/<workspace>/<run-id>/activation.md`, per [references/run-isolation.md](../references/run-isolation.md). Discovery has no committed technical scope yet, so this early pass mostly seats the mandatory floor and any lens the seed material already implies; step 2 below re-anchors the repo and may refresh stage 1 once the workspace shape is known.

**Stage 0 - policy candidate set (the hard boundary).** Read the org policy's approved-pack set, resolved managed > project > user (per `openadlc.example.yaml`; org policy can only tighten, never loosen). No policy present, or an untweaked default, means ALL packs are approved (the dumb-proof default); a free user's own configured picks are their candidate set. The model NEVER activates a discretionary pack outside this candidate set. The rail-1 mandatory floor is EXEMPT from this tightening: it loads before and independent of stage 0, so a policy that narrows the candidate set can never drop a floor member.

**Stage 1 - repo facts.** Run the deterministic file-marker sniff (`standard/domains.md` section 4) to get the matched technical-domain set. Reuse the run's existing `## Repo facts` section in `activation.md` when no marker file changed since `detected`; otherwise (re)sniff and (re)write that section per the schema `standard/domains.md` section 5 defines. This is a read-only static sniff, no network call, no model judgment. If the sniff matches zero technical domains (an empty or unrecognized repo), seat only the floor and ASK the operator which domain applies (per `standard/domains.md` section 4); never infer a technical domain from the ask alone.

**Stage 2 - ask-scoped activation.** From `candidate_set ∩ (matched_domains ∪ the cross-cutting lenses the ask implies)`, the model multi-selects the domains THIS ask actually needs, and MAY late-bind more mid-run as the work reveals a need. Every pack's marketplace `description` (its INDEX line) stays in context for the whole run; a pack's body (its skills) loads only once activated, progressive disclosure, the native skill pattern.

**The three rails (non-negotiable):**
1. **MANDATORY FLOOR:** the `adlc-core` spine (the four `/ai-*` commands + the lifecycle checkpoints), the `security` lens, and the org-policy pins load ALWAYS, before stage 2 runs, never model-optional. The floor loads before and independent of BOTH the stage-0 candidate set and stage-2 ask-scoping: a policy that tightens the candidate set (for example `packs.disabled`) narrows only the discretionary stage-2 set and can NEVER drop a floor member (`adlc-core`, the `security` lens, the org pins).
2. **AMBIGUITY -> INCLUDE:** when unsure whether a domain or lens applies, activate it; activation fails OPEN. This is distinct from the lifecycle's GATES and consent checkpoints, which never fail open, they only ever stop and ask.
3. **AUDIT:** log the activation set with a per-domain reason to `activation.md`'s `## Activation` section (append; never overwrite the stage-1 `## Repo facts` section):
```markdown
## Activation
- <domain>: <reason: policy | repo-facts | ask-match | floor>
```

State the activated domains and packs; let the operator correct.

## 1. Open the conversation
With no task yet, load what the pipeline needs (`load-context`, `codebase-researcher` on standby), create the run workspace + living doc and **open it for the operator** (step 2), then greet, and make the navigation explicit:

> Hello, let's plan this together. Tell me everything about the task, and paste any documents, links, or Figma URLs. I will investigate as we go and keep a **living doc** open for you to watch it fill in.
>
> **How this works:** each round I will update the doc, give you a short summary, flag the open questions, and suggest what to refine next. You decide how deep we go.
> **When you are ready:** say **"done"** (or "create it" / "post it") and I will turn it into the task and post it to your tracker (GitHub / Jira). Say **"show the doc"** to reopen it anytime.
>
> Tell me about the task and I will start.

There is no required input; the operator drives the pace. Take whatever they give (free text, attached files, URLs, Figma links).

## 2. The run workspace + living doc
Mint the run-id ONCE here (intake is the first writing step) and create the per-run workspace, both per [references/run-isolation.md](../references/run-isolation.md): the run-id is **workspace-level** (one id for a change that may span several repos) and the workspace is the out-of-repo `~/.openadlc/runs/<workspace>/<run-id>/`, which IS the OKF bundle (per [references/okf.md](../references/okf.md)), with the living doc inside it as `briefing.md` (the human face; always markdown, no `.html` option). Carry the run-id forward to plan/implement/review; never write run artifacts inside the repo, never under the repo's `.claude/` (no `.claude/runs/`, `.claude/sessions/<name>/`), and never to a slug-only path. **Open it immediately** (`code <path>`, or the editor's open command) so the operator can watch it update, and re-open it whenever they say "show the doc". Keep it updated every round: the problem and goal, everything the operator told you, attached docs/links (summarized + cited), discovery findings, the resolved workspace shape + member repos + primary tracker, the emerging type, the acceptance criteria as they form, the development dependencies, open questions, and decisions. It is the source the final task is generated from, a working artifact, not the deliverable.

## 3. Plan deeply, together (loop until the operator says done)
**First, detect the workspace shape and anchor the primary tracker.** Before investigating anything, resolve where you are, across the four workspace shapes in [references/run-isolation.md](../references/run-isolation.md):
1. **Single repo** , the cwd is one git repo. That repo is the workspace; `git remote get-url origin` is its tracker; state it.
2. **Monorepo** , one git repo holding many packages. Still one tracker; package structure is internal.
3. **Poly-repo product** , an `openadlc.yaml` at the workspace root declares `workspace.repos` + `primary`. The run SPANS the member repos it touches; the PARENT story posts to the **primary** repo's tracker.
4. **Undeclared parent of repos** , a folder holding several repos with no `workspace:` declaration. STOP and ask the operator: which single repo is the target, OR offer to declare them a workspace (write `workspace.repos` + `primary` into `openadlc.yaml`). Never silently anchor discovery on the parent or its child projects.

When the operator says "this repo" or "this repo's github", they mean the resolved target (the single repo, or the primary repo of a declared workspace). Record the resolved workspace shape, the member repos, and the primary tracker in the living doc.

This is a conversation. Each round:
1. Take what the operator added and investigate it against the codebase (`codebase-researcher`, read-only), the linked docs, and the designs. Surface findings, open questions, risks, and the **development dependencies** (what must exist or ship first, prerequisites, blockers, the services / data / libraries it relies on, the order between pieces). On a poly-repo product, note which member repos the work appears to touch and any **cross-repo dependency order** (e.g. shared-components before web-app). Fan out parallel read-only agents where threads are independent ([references/orchestration.md](../references/orchestration.md)).
2. **Update the living doc.**
3. **End the round with a short summary and a clear menu, never go silent.** Tell the operator: what is captured now, the top open questions, **2-3 concrete suggestions for what to refine next** (e.g. "research how sessions persist", "pin the password rules", "tighten the acceptance criteria"), and remind them they can **say "done" to create the task**. Recommend a deeper research/refinement loop only when it genuinely helps ([references/loop-control.md](../references/loop-control.md)); default light.

Cite what you find; mark anything unverified `unknown`; never invent.

**The operator ends planning** by saying "done" / "create it" / "post it". Until then keep looping with the summary + menu each round, never leave them unsure how to continue or how to finish. If the input includes a Figma or design surface, note it in the doc so `/ai-plan` loads the `adlc-design` pack on-demand.

## 4. On "done": write the OKF bundle
When the operator says planning is done, generate the task from the living doc as ONE OKF bundle in the out-of-repo run workspace (`~/.openadlc/runs/<workspace>/<run-id>/`, per [references/run-isolation.md](../references/run-isolation.md) and [references/okf.md](../references/okf.md)). The bundle is flat and conformant:
- **The briefing** (`briefing.md`, `type: Briefing`): the human face. Prettified, simplified, easy to follow no matter how complex the idea. Problem, goal, scope, **acceptance criteria**, open questions. This is what a person reads.
- **The classified unit** (`story.md`, `type: Story | Bug | Epic | TechDebt | Intent`) plus the AI-context concepts (`discovery.md`, `dependencies.md`, `type: Reference`): the full extended task and context, everything the planner and implementer need, nothing trimmed for readability. Write `okf_version: "0.1"` into the bundle-root `index.md`.

Keep it user-framed: the problem, the user outcome, the platforms in scope if the product names them, and acceptance criteria in user terms. Do not pick the technical domain or stack here; `/ai-plan` detects or asks for that.

The briefing and the AI concepts are not long-vs-short, they are two different jobs:
- **The briefing, built for COMPREHENSION:** a clear, human-readable summary, so a dev (or any operator) who has never seen this understands, at a glance, what needs doing and why, no matter how complex the work. This is what keeps the operator genuinely in the loop.
- **The AI concepts, built for COMPLETENESS:** every detail the planner and implementer need, full context, nothing trimmed, so the build does not deviate.

This defeats the two ways intake fuel fails: **too thin** and the AI fills the gaps with guesses and drifts from the intent; **too detailed and AI-first** and the human is locked out of a wall of context they cannot follow, and the human-in-the-loop becomes theater. Hold the briefing and the AI concepts each to their own bar. When `compression` is on (openadlc.yaml, default), the AI concepts may be compressed per [references/token-compression.md](../references/token-compression.md); the briefing never is.

### Classify the type, then define acceptance criteria
Pick the right intake type and give it testable acceptance criteria:
- **Story / feature:** the observable behavior that must be true when it is done.
- **Bug:** the bug no longer reproduces, the correct behavior, and a guard against regression.
- **Epic:** a large initiative, too high-level to plan directly. Intake breaks it into its **child stories now**, each a proper story with its own acceptance criteria, **linked to the epic**. The epic holds the outcome, the scope, and the done-condition (all child stories done); it is an organizing parent, never a plannable unit. `/ai-plan` works the child stories, not the epic.
- **Tech debt:** the target state and the measurable improvement, with nothing else regressing.
- **Intent:** a looser direction, not yet a committed unit; capture the goal, the open questions, and what discovery is still needed. (Naming note: some teams use "intent" for a fully-specified super-story; in OpenADLC it is the opposite, a not-yet-committed direction that discovery turns into a story. That rich AI-format spec is the **AI face** of a story here, not an intent.)

Write AC as a checkable list a person, and later the implementer, can tick off. Also record the **development dependencies** surfaced in discovery (prerequisites, blockers, the order between pieces) so `/ai-plan` and `/ai-implement` know them upfront. These criteria are the spine of the lifecycle: the plan maps its slices to them and `/ai-implement` checks the build against them before any review. Intake fuel with no acceptance criteria (or, for an intent, no clear next question) is not done.

## 5. Checkpoint: post, or refine further
Before asking, write the checkpoint file (`type: post-issue`) per [references/checkpoints.md](../references/checkpoints.md). Present the task and **stop and ask the operator for an explicit yes.** Two moves:
- **Post** the PARENT story to the **primary tracker** (the single repo's tracker, or the `primary` repo of a declared workspace) as the unit of work, routed through the tracker adapter (`create_issue`, `assign`), never with hardcoded GitHub-only semantics, per [references/tracker-adapters.md](../references/tracker-adapters.md).
  - **First, dedup BEFORE creating, per [references/run-isolation.md](../references/run-isolation.md):** check the tracker for an existing open issue for this work (the adapter's lookup, e.g. on GitHub `gh issue list --search "<slug>" --state open`) AND scan active `~/.openadlc/runs/<workspace>/*` for the same slug. If one exists, STOP and offer update-vs-new; do not create a duplicate. Tag the created issue with the run-id so duplicates stay detectable.
  - **Serialize the OKF bundle into the issue per the tracker, per [references/okf.md](../references/okf.md).** On **GitHub** (no attach API): the visible body is `briefing.md`, the AI concepts go inside a `<details>` as typed concept sections (each `type:` in frontmatter, opened by a `<!-- okf:concept path=... -->` hint), and anything over ~60KB spills into sequential comments. On **Jira**: the body is `briefing.md` (converted to ADF) and the bundle is attached as `<slug>.okf.tgz`. Either way the content travels with the issue: never post only a `~/.openadlc/...` path, because a teammate, CI, or a fresh agent cannot read a file on your machine. (The story is the parent; `/ai-plan` fans it out into one sub-issue per domain, and a poly-repo run spans the member repos those domains touch.)
  - **Create + assign on create, then VERIFY, per [references/tracker-adapters.md](../references/tracker-adapters.md).** On GitHub: `gh issue create --assignee @me ...` (if `@me` does not resolve, ask once whom to assign), then confirm the assignee actually set (`gh issue view <n> --json assignees`); if it is empty, redo with `gh issue edit <n> --add-assignee`. An issue posted without the assignee is incomplete. Jira maps create + assign per the adapter doc.
  - Posting is outbound: it needs an explicit yes. In v0.1 the command drafts the issue (the serialized OKF bundle, assignee set) and on your yes posts it (`gh issue create` + the assignee verify), per [references/tracker-adapters.md](../references/tracker-adapters.md); auto-post per tracker is a later integration.
  - **After it posts, write back into the living doc** (idempotency): record **POSTED**, the issue URL/number, and the assignee, so a re-run sees the work already exists and dedup catches it. The living doc is the source of truth that this run produced a tracked issue.
- **Refine** further with another bounded discovery or research loop before posting. **State the three loop-control declarations UP FRONT, before the operator says yes**, per [references/loop-control.md](../references/loop-control.md): the **default cap** (one pass), the **hard ceiling** it cannot exceed, and the **exit criterion** (a fixed N, or "until two consecutive rounds add nothing new"). The operator approves the depth knowing the bound before any round runs.

Never post without an explicit yes.

## Run end
When discovery **ends the run here** (`index.md` status `done` or `abandoned`, not continuing into `/ai-plan`), the run has reached its terminal state and the lifecycle is complete. If the run continues straight into `/ai-plan` (status `active`), it is not terminal here; the run ends at whichever command carries it to `done` or `abandoned`.

## Exit
Done when the OKF bundle exists under `~/.openadlc/runs/<workspace>/<run-id>/` (briefing + classified unit + AI concepts + `index.md`), carries clear acceptance criteria, the living doc captured the planning (including the workspace shape, member repos, and primary tracker), and you have posted the parent story to the primary tracker (the bundle serialized into the body per [references/okf.md](../references/okf.md), the operator assigned, deduped before create). The living doc records **POSTED** plus the issue URL so a re-run is idempotent. If the run continues straight into `/ai-plan`, leave `index.md`'s `status: active`; if this run ends here, set it `done` (or `abandoned`), per [references/checkpoints.md](../references/checkpoints.md). Hand the posted issue (and the run-id) to `/ai-plan`, which selects the run by run-id, never by feature-name glob.
