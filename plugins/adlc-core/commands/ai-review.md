---
description: "This command should be used when the user types \"/ai-review\", or asks to \"review this\", \"review PR <n>\", \"code review this diff/branch\", \"security review this\", or runs the review step inside /ai-implement. Reviews a diff, branch, PR, or any code with fresh, independent eyes; offers a menu of review types (code, security, compliance, adversarial lenses); prints a BLOCK or APPROVE verdict; posts back only on explicit consent."
argument-hint: "[a diff, branch, PR (URL/#number), or path to review]"
allowed-tools:
  - Bash(gh pr view:*)
  - Bash(gh pr diff:*)
  - Bash(gh pr list:*)
  - Bash(gh pr checkout:*)

---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# /ai-review

Independent review. Fetching, reading, and analyzing are local and need no approval. **Posting anything back (PR comments, a verdict) is outbound: STOP and ask the operator for an explicit yes first.**

When a `references/<name>.md` link does not resolve relative to this file, locate it under the deployed adlc-core pack (search for the file name, e.g. under `apm_modules/*/adlc-core/references/`) and READ the referenced file before acting on its rule.

Target: $ARGUMENTS (a diff, branch, PR, or code). Empty inside `/ai-implement` means: the change just built.

## 0. Domain activation
Before anything else, resolve which domain packs load for this run, by running the three-stage funnel from [standard/domains.md](../../../standard/domains.md) (this command CALLS that procedure; it does not reimplement the detector). Every step writes to the run's `~/.openadlc/runs/<workspace>/<run-id>/activation.md`, per [references/run-isolation.md](../references/run-isolation.md). **Embedded** in `/ai-implement`, the domains are already activated by that run; reuse `activation.md` rather than re-running the funnel. **Standalone**, run the funnel fresh against the target's repo.

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

## Two ways it runs
- **Embedded** in `/ai-implement`: the implement pipeline stops and asks which review types to run; this command runs the picked ones.
- **Standalone**: review a teammate's PR, a fresh pass on a risky change, or any code outside a pipeline.

## The review types (pick one or more)
- **Code** (recommended default): correctness, logic, whether the tests actually assert anything, fit with the codebase conventions.
- **Security**: via the domain's `security-reviewer` and the OWASP lenses, when the change touches auth, crypto, network, secrets, or a public surface.
- **Compliance**: via the privacy/compliance lens, when it touches PII, consent, retention, or a regulated flow. **For UI, compliance also means design fidelity**: did the build match the approved design, or is it not what was designed?
- **Adversarial lenses**: one or more relevant fresh-eyes lenses (a pentest mindset, a `test-critic` on the tests, a perspective-diverse pass).
- **Design / UI fidelity**: via the `adlc-design` pack (the `design-critic` agent plus the pixel / token / component checks), when the change builds UI from a design. It **compares the rendered screens (device / browser / desktop) against the plan's Figma baseline** in `~/.openadlc/runs/<workspace>/<run-id>/design-baseline/` (per [references/run-isolation.md](../references/run-isolation.md)), and flags if the live design has drifted from that baseline. Loaded on-demand, only for UI work.
- **None**: not recommended; only for genuinely trivial changes.

## Pipeline
0. **activate domains** (the three-stage funnel, step 0) -> 1. Resolve the target (read-only); when embedded in a run, select the plan by run-id, never by feature-name glob (per [references/run-isolation.md](../references/run-isolation.md)). On a poly-repo product a run spans several repos: review the **per-repo diff** of each touched repo's `adlc/<run-id>` branch -> 2. load each touched repo's review contract (`CLAUDE.md` + touched rules) -> 3. dispatch the picked reviews **concurrently** to fresh-context agents (**`pr-reviewer`** for the merge verdict; the domain reviewer; `security-reviewer`; `test-critic`; the `design-critic` for UI) -> 4. **`pr-review-confidence`** drops low-signal findings -> 5. **PERSIST the verdict, every run:** write each lens's report to the out-of-repo `~/.openadlc/runs/<workspace>/<run-id>/review-<lens>-<UTC-timestamp>.md` (one file per review lens) and the payload to `review-payload.json` (per [references/run-isolation.md](../references/run-isolation.md)), never a bare `review.json`/`review-<date>.md`, never inside the repo, never under the repo's `.claude/`, and never leave the review as only a commit message. This write happens on **every** run, BLOCK or APPROVE, before any consent prompt; posting stays gated, persisting does not -> 6. print the report -> 7. before asking, write the checkpoint file (`type: post-review`) per [references/checkpoints.md](../references/checkpoints.md), then **STOP and ask the operator for an explicit yes** -> **`pr-review-publisher`** posts **per-repo PR reviews** (one per touched repo's PR), dedup'd (embed `<!-- adlc-run: <run-id> -->`, update-or-skip if a review with this run-id exists on that PR), tagged with the run-id, and only on an explicit yes. When the post also creates or updates a tracker item (a review-gate item or a re-opened finding), route that write through the tracker adapter's `create_issue` / `set_status` / `assign` actions and **assign the operator** on create, per [references/tracker-adapters.md](../references/tracker-adapters.md); do not hardcode GitHub-only semantics.
- **Outbound:** only the post (the PR review and any tracker-item write it drives), and only after the operator's explicit yes. Persisting the `review-*.md` is local and is NOT gated; it always happens. Reviewing is not approving anything to leave the machine.

## Report format
```
<target>  (<author>, <head> -> <base> if a PR)
Reviews run: <code, security, ...>
Findings: <count>   [none -> "No issues found. Checked for bugs and <project> conventions."]
  [HIGH] <file>:<line>  <one-line problem>
         <why; a fix if it is short>
Verdict: BLOCK | APPROVE (with nits)
Outbound if approved: <N> comments + verdict on <target>
```

## Run end
When `/ai-review` runs **standalone** and carries the run to its terminal state (`index.md` status `done` or `abandoned`), the run is complete. When `/ai-review` runs **embedded in `/ai-implement`**, the run ends at the implement terminal state, not here.

## Guardrails
Read and analyze locally; the only outbound step is posting, and it waits for the operator's explicit yes. Never run `gh pr comment`, `gh pr review`, or API writes before the operator says yes. Cite every finding `path:line`; mark anything unverified `unknown`, never invent.
**Verify-real-run applies to review evidence too.** A visual or behavioral acceptance criterion is "met" only after a REAL run with PERSISTED evidence: web = dev-server smoke + a saved screenshot; native = build + install + LAUNCH on sim/emulator + a saved screenshot. A green build or a SwiftUI/preview/snapshot render is NOT sufficient. A "looks right" claim with no saved artifact is a finding, not an approval: if the implement step's acceptance evidence is missing or is only a build/preview, the verdict is BLOCK. (Cautionary example: the iOS home build passed verify with screenshots but the shipped, unsigned binary did not actually launch.)
**Route tracker actions through the adapter.** Any tracker write the verdict drives (create a review-gate item, set its status, assign it) goes through the tracker-adapter actions `create_issue` / `link_child` / `set_status` / `assign`, with per-tracker mappings (GitHub issues, Jira issues), per [references/tracker-adapters.md](../references/tracker-adapters.md). Assign the operator on create. Never hardcode GitHub-only semantics in prose.
**Token compression**: when `compression.enabled` (openadlc.yaml, on by default), communicate tersely for AI-internal and inter-agent output per [references/token-compression.md](../references/token-compression.md); never compress the human-facing artifacts (the review report and verdict, the consent prompt).
