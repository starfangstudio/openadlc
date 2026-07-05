---
description: "This command should be used when the user types \"/ai-implement\", or asks to \"implement the plan\", \"build the sub-issue\", \"code this up\". Runs against an approved dev-plan sub-issue, builds in slices, verifies each, checks the build against the acceptance criteria, then stops to ask which reviews to run, then stops and asks the operator for an explicit yes before the push to remote. The procedure lives in the implement-change skill."
argument-hint: "[the dev-plan sub-issue (URL/#number) or a slice to start with]"

---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# /ai-implement

Builds an approved plan end to end and ends at the push checkpoint. The procedure lives in the **`implement-change`** skill; this command runs the pipeline.

When a `references/<name>.md` link does not resolve relative to this file, locate it under the deployed adlc-core pack (search for the file name, e.g. under `apm_modules/*/adlc-core/references/`) and READ the referenced file before acting on its rule.

Input: $ARGUMENTS (the dev-plan sub-issue, or a slice)

## Pipeline
1. Load the plan from the sub-issue (this command) -> 2. **choose the method (ask: SDD or TDD)**, then **`implement-change`** drives the build in slices, using the domain pack's action skills -> 3. **verify** each slice with a check that can fail (tests; the operator looks at the diff) -> 4. **acceptance-criteria check**: the AI judges the built slices against the plan's acceptance criteria, is the job done? -> 5. **review checkpoint: stop and ask which reviews to run** -> 6. run the picked reviews -> 7. **operator takes a final look** -> 8. **push checkpoint: ask the operator for an explicit yes to push to remote** -> pipeline ends.
- **Models:** Sonnet by default; Opus for a large or complex slice. Never Haiku.
- **Outbound:** none until the push checkpoint.

## 1. Load the plan
Resolve the sub-issue (read-only) and **select the run by run-id, NOT by globbing `.claude/plans/*` or matching the feature name** (per [references/run-isolation.md](references/run-isolation.md)): read the `run_id` from the sub-issue (or the spec.md frontmatter), **reassemble the plan OKF bundle from the sub-issue** (per [references/okf.md](references/okf.md): on GitHub parse the markers across the body + comments; on Jira/ADO download and untar `<slug>.okf.tgz`), and load the domain plan from the out-of-repo `~/.openadlc/runs/<workspace>/<run-id>/plan/` at its stable absolute path. The plan names the repos this domain touches and their cross-repo dependency order. A plan must exist and be approved; if none, stop and tell the operator to run `/ai-plan` first. Never improvise a plan here.

**Concurrency check (per run-isolation):** detect an in-progress run (`git worktree list`, another live `adlc/*` branch, or an active `~/.openadlc/runs/<workspace>/*` with no terminal state). If a different run is active in this checkout, do NOT share it: auto-create an isolated worktree for this run and have the operator reopen there. A single run with no collision works on `adlc/<run-id>` in place.

**Set the sub-issue in-progress at implement start (via the adapter).** Once the sub-issue is resolved, move it to in-progress through the tracker adapter's `set_status` action ([references/tracker-adapters.md](references/tracker-adapters.md)): GitHub maps this to a `status: in progress` label or the Project status field; Jira transitions the sub-task, ADO sets the work-item state. This is a local-only tracker write (no PR, no push), done before the build starts so the work is visibly claimed. Do not hardcode GitHub-only semantics here; route through the adapter so the same step works on Jira and ADO.

## 2-3. Choose the method, build, and verify
**First, ask the operator which method to use, SDD or TDD** (spec-driven: build to the spec and acceptance criteria, tests pin the behavior; or test-driven: the failable check first, build to green, refactor). Leave the choice to them; it is a mandatory step, not a default.

Then invoke **`implement-change`**: build in small, reviewable slices. In EACH repo this run touches, code commits go on the run branch `adlc/<run-id>` (per [references/run-isolation.md](references/run-isolation.md): branched from that repo's default at latest, `origin/<default>`; NEVER main or a shared branch; never commit the out-of-repo run workspace; `implementation-lead` integrates slice work into `adlc/<run-id>`, with slice worktrees nested as `adlc/<run-id>/<slice-id>`), using the detected domain pack's action skills (and the `adlc-design` pack's Figma skills for UI slices, when the sub-issue calls for them). **Honor the development dependencies carried from intake into the plan**, and on a poly-repo product **the cross-repo dependency order the plan names**: respect their ordering, build prerequisites (and base/shared repos) before dependents, and flag any that block a slice. Each slice ends in a **failable check**: a unit/integration test for logic, a fidelity + design-system check for UI (compared against the plan's Figma baseline in `~/.openadlc/runs/<workspace>/<run-id>/design-baseline/`), a smoke/plan check for config/IaC; verify artifacts land under `~/.openadlc/runs/<workspace>/<run-id>/verify/`. For UI work, re-fetch the live design first and flag any drift from the plan's baseline before building. Verify each slice with its check. Show the diff and the passing evidence. A change with no failable check is not verified.

## 4. Acceptance-criteria check (automatic, the AI's definition of done)
Before asking the operator anything, check what the slices actually built against the acceptance criteria carried in the plan, criterion by criterion. For each: **met / partial / not met**, with `path:line` evidence and the verifying check. For UI, this includes a **fidelity comparison**: capture the rendered screens (device / browser / desktop) and compare them against the plan's Figma baseline; a visible mismatch is an unmet criterion. Then the headline call: **does the AI judge the job done?**

**VERIFY-REAL-RUN GATE (a visual or behavioral criterion is "met" only after a real run with persisted evidence).** A green build is not "met". A SwiftUI / preview / snapshot render is not "met". The criterion is met ONLY when the thing actually ran and the evidence was saved to the run workspace:
- **Web:** a dev-server smoke (the app started and served the screen) plus a saved screenshot under `~/.openadlc/runs/<workspace>/<run-id>/verify/`.
- **Native:** build **and install AND launch** on a sim/emulator, then a saved screenshot of the launched screen under that same `verify/` path. The build passing is not enough; the binary must come up.

Cite the cautionary example: the iOS home build passed verify with screenshots, but the shipped, unsigned binary did not actually launch. Build-green and a preview render both lied; only a real launch would have caught it. So for any visual or behavioral criterion, persist the real-run evidence or mark the criterion **not met**, no exceptions.

- If every criterion is met, say so and proceed to the review checkpoint.
- If any criterion is unmet or partial, **do not wave it into review.** Close the gap (back to the build) and re-check, or, if it is blocked or the criteria themselves are wrong, stop and surface it to the operator.

This is the AI's own gate, not an operator prompt: an honest "is this actually done?" before a human spends attention on the review.

## 5. Review checkpoint (mandatory step, never skipped, stop and ask)
This step always runs; the ask is not skippable, though the answers may be "none, one pass". Ask the operator **two things**:

**(a) Which reviews to run** (one or more; recommend based on what the change touches):
- **Code review** (recommended default).
- **Security review** (recommended when the change touches auth, crypto, network, secrets, or a public surface).
- **Compliance review** (recommended when it touches PII, consent, retention, or a regulated flow).
- **Adversarial lenses** (one or more relevant lenses for a fresh-eyes pass).
- **Design / UI fidelity** (recommended when the change builds UI from a design; via the `adlc-design` pack, on-demand).
- **None** (not recommended; only for genuinely tiny or trivial changes).

**(b) Depth: one pass, or a loop.** Run the picked reviews once, or as a bounded loop (review, fix, re-review until clean, or N passes). Default: one pass. **Before the operator says yes to a loop, state the four loop-control declarations up front** so they know how many iterations and the spend before they commit, per [references/loop-control.md](references/loop-control.md):
- **Default cap** (the exit criterion's N, e.g. one pass).
- **Hard ceiling** (the loop cannot exceed it even if not converged; from managed config, a project may lower it, never raise it).
- **Exit criterion** (concrete: a fixed cap, or "until converged" with a hard definition, two consecutive rounds add nothing new).
- **Per-round cost estimate** (tokens / $ per round and the projected total at the cap, drawn from the cost ledger so it is real, not a guess; see [references/cost-ledger.md](references/cost-ledger.md)).

Each round still ends in a one-screen summary with its actual cost and the running total, so the operator can stop early.

Run exactly what the operator picked, at the chosen depth, via `/ai-review`.

## 6-7. Run reviews, final look
Run the picked reviews **in parallel** (each a fresh, independent pass). Present the verdicts. The operator takes a **final look** at what was built.

**Persist the review verdicts (every run).** Write each review's verdict to `review-<lens>-<UTC-timestamp>.md` (one file per review lens) and the payload to `review-payload.json` in the run workspace (`~/.openadlc/runs/<workspace>/<run-id>/`), e.g. `review-code-20260628T141233Z.md`, per [references/run-isolation.md](references/run-isolation.md). This happens every run, BLOCK or APPROVE; posting back to the tracker stays gated, but the persisted verdict is not optional. Never leave the review as only a commit message, a teammate, CI, or a fresh agent must be able to read the full verdict from the run workspace.

## 8. Push checkpoint: the push
The push to remote is outbound. Before asking, write the checkpoint file (`type: push`) per [references/checkpoints.md](references/checkpoints.md); the operator may also resolve it from the cockpit while you wait. **STOP and ask the operator for an explicit yes:** present exactly what would go out (every repo, branch, and PR) and ask for an explicit yes. No standing approval. On yes, for EACH touched repo push its `adlc/<run-id>` branch and open **one PR per repo**, each linked to this domain's sub-issue (per [references/run-isolation.md](references/run-isolation.md)). On a poly-repo product, `implementation-lead` **sequences the multi-PR merge in cross-repo dependency order**: base/shared repos merge before their consumers (e.g. shared-components before web-app). **Dedup first:** for each repo check for an existing open PR for this run and offer update-vs-new; tag each PR with the run-id. Never push or merge the out-of-repo run workspace. Record the decision. **Set `index.md`'s `status: done`** (or `abandoned` if the run ends without pushing), per [references/checkpoints.md](references/checkpoints.md): this is the run's terminal state. The pipeline ends here. There is no separate ship command.

## Guardrails
All work is local until the push checkpoint. Work on the run branch `adlc/<run-id>` (or its worktree on concurrency), never main or a shared checkout, per [references/run-isolation.md](references/run-isolation.md). Never push, PR, comment, or publish without an explicit per-action yes.
**Cost ledger (persist per-phase token/$).** As each phase runs (load, build per slice, acceptance-criteria check, each review pass), append its token and $ usage to the run's cost ledger in the run workspace, per [references/cost-ledger.md](references/cost-ledger.md). This is what makes the loop-control cost view in step 5(b) real instead of a guess, and what makes model-routing measurable (Sonnet-vs-Opus spend per slice). The ledger is local to the run workspace and never committed.
**Token compression**: when `compression.enabled` (openadlc.yaml, on by default), communicate tersely for AI-internal and inter-agent output per [references/token-compression.md](references/token-compression.md); never compress the human-facing artifacts (the diff summary, the review verdict, the consent prompt).
