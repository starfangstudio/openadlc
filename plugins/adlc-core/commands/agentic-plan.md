---
description: "This command should be used when the user types \"/agentic-plan\", or asks to \"plan this story\", \"scope this work\", \"turn this issue into a dev plan\". Takes a plannable unit of intake fuel (a story, bug, or tech-debt, as free text, a file, or a tracker issue; not an epic or a bare intent), detects or asks for the domain, and authors a thorough development plan; a gate to approve or edit it; on approval it posts a remote sub-issue with the plan attached, ready for /agentic-implement. Authoring is delegated to the create-plan skill."
argument-hint: "[story text | path to a file | tracker issue URL or #number]"

---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# /agentic-plan

Turns intake fuel into a buildable plan. This command authors nothing itself; the plan is written by the **`create-plan`** skill. It resolves the input, detects or asks for the domain, runs read-only exploration, drafts the plan (carrying the development dependencies surfaced at intake), gates on your approval, and on a yes posts the plan as a remote sub-issue.

Input: $ARGUMENTS (a plannable unit of intake fuel: a story, bug, or tech-debt)

## Pipeline
1. Resolve the intake fuel + select the run by run-id (this command, per [references/run-isolation.md](references/run-isolation.md)) -> 2. **detect or ask for the domain(s)** and load each domain's pack -> 3. **`codebase-researcher`** (read-only exploration) -> 4. **`create-plan`** authors ONE plan per domain into the out-of-repo `~/.openadlc/runs/<workspace>/<run-id>/plan/` (slices, tests, compliance notes, the .md/.json artifacts, design refs; each domain plan naming the repos it touches and their cross-repo dependency order; `run_id` + `branch` in spec.md frontmatter; restating the acceptance criteria and carrying the development dependencies from intake) -> 5. **plan checkpoint: approve, edit, or refine** (the refine loop states its cap, ceiling, exit, and per-round cost up front, per [references/loop-control.md](references/loop-control.md)) -> 6. on yes, **dedup then post one NATIVE sub-issue per domain, linked under the parent story and assigned to the operator**, via the tracker adapter (per [references/tracker-adapters.md](references/tracker-adapters.md)): the body carries **both faces inline** (the human plan as the body, the full AI plan in a collapsible block), plus a one-line pointer to the run workspace. The post is outbound: STOP and ask the operator for an explicit yes first.
- **Outbound:** none until the post. Reading the issue and code is local; posting the sub-issue (create + link-as-sub-issue + assign, all through the tracker adapter per [references/tracker-adapters.md](references/tracker-adapters.md)) needs the operator's explicit yes.

## 1. Resolve the intake fuel
Detect what `$ARGUMENTS` is: free text, a file/path (PRD, story, spec), or a tracker issue (GitHub/Jira/ADO URL or #number, fetched read-only). This is intake fuel, already classified at intake. **Select the run by run-id, never by globbing `.claude/plans/*` or matching the feature name** (per [references/run-isolation.md](references/run-isolation.md)): if intake produced a run, read its workspace-level run-id and reuse the existing `~/.openadlc/runs/<workspace>/<run-id>/`; if planning is the first writing step (no upstream run), detect the workspace shape (single / monorepo / declared poly-repo product / undeclared parent, per run-isolation; ask which repo, or offer to declare, when it is an undeclared parent) and mint the workspace-level run-id ONCE here, then create `~/.openadlc/runs/<workspace>/<run-id>/`. **Plan only a plannable unit: a story, a bug, or tech-debt.** An **epic** is too high-level to hold all the specs, stop and point the operator at its child stories (intake already split them out) and plan those. A bare **intent** is not ready either, it needs a discovery pass at intake to become a story first. Pull in the unit's acceptance criteria, the development dependencies surfaced in deep discovery, any layout/UI intent, and the discussion. If empty or ambiguous, ask.

**Concurrency check (per run-isolation):** detect an in-progress run (`git worktree list`, a live `adlc/*` branch, or an active `~/.openadlc/runs/<workspace>/*` with no terminal state). If one is found, do NOT share the checkout: auto-create an isolated worktree and have the operator reopen there. A single run with no collision works on `adlc/<run-id>` in place.

## 2. Detect or ask for the domain
A story from a product owner usually does not name a technical domain. Resolve it before planning:
1. **Detect from the repo** the plan runs in: the manifest and layout (a web framework in `package.json` -> web; `build.gradle` + Kotlin -> android; `Package.swift` / Xcode -> ios; a Tauri or Electron config -> desktop; a server framework -> backend; and so on). One clear signal -> use it and state it.
2. **Ask when it is unclear.** If the repo gives no clear signal, is empty or new, or the story spans platforms or layers (front end AND back end, android AND ios, windows AND macos), STOP and ask the operator which domain(s) to plan and implement for. One parent story fans out into **one plan + one sub-issue per DOMAIN** (web, backend, android, ...), per [references/run-isolation.md](references/run-isolation.md); scope this run to the operator's answer. On a declared poly-repo product a domain may span several member repos, so **each domain's plan names the repos it touches and their cross-repo dependency order** (base/shared repos before their consumers, e.g. shared-components before web-app).

Load the chosen domain pack (and any cross-cutting pack: security, privacy, AI). **Load `adlc-design` only when the story involves Figma or a design/UI surface**, never for non-UI work. State the domain and packs; let the operator correct.

## 3. Explore (read-only)
Delegate heavy investigation to **`codebase-researcher`**, fanning out parallel reads where the threads are independent. Cite `path:line`. Surface ambiguities now, before a plan exists.

## 4. Plan (delegate to create-plan)
Invoke **`create-plan`** once per domain: it owns the plan sections and writes the human-readable plan (`spec.md`), the slice breakdown, and the supporting artifacts the build needs (a test plan, compliance notes where the change is regulated, .json contracts, references to the design). **All plan artifacts land in the out-of-repo run workspace** per [references/run-isolation.md](references/run-isolation.md): `~/.openadlc/runs/<workspace>/<run-id>/plan/spec.md`, `plan/Plans.md`, `plan/*.json`, with design refs under `~/.openadlc/runs/<workspace>/<run-id>/design-baseline/`; never inside the repo, never under the repo's `.claude/` (no `.claude/runs/`, `.claude/plans/<feature>/`). **Record `run_id: <run-id>` and `branch: adlc/<run-id>` in `spec.md` frontmatter** so implement/review/resume select this run by run-id. Each domain's plan **names the repos it touches and their cross-repo dependency order** so the build sequences them correctly. The plan is a complete contract: it **restates the intake fuel's acceptance criteria and maps each slice to the criteria it satisfies**, so the build has a checkable definition of done. It also **carries the development dependencies surfaced at intake** (and any layout/UI intent) into the plan, so the build honors them. Two faces again: the summary a person follows, and the full plan files the implementer consumes.

## 5. Gate: approve, edit, or refine
Present the plan and **stop for the operator.** This checkpoint offers three moves, not just yes/no:
- **Approve** the plan as written.
- **Edit** it: change the scope, the approach, or the rollback before anything is posted.
- **Refine** it with a bounded loop: iterate the plan to tighten it, or generate a few independent approaches and synthesize the best (a judge panel). **State the four loop-control declarations BEFORE the operator says yes** (per [references/loop-control.md](references/loop-control.md)), so they know how many iterations and the spend up front: the **default cap** (one pass), the **hard ceiling** it cannot exceed, the **exit criterion** (a fixed N, or "until two consecutive rounds add nothing new"), and the **per-round cost estimate** (tokens / time, with a running total). Each round ends in a one-screen summary so the operator can stop early.

Do not proceed while a `[NEEDS INPUT]` remains.

## 6. Post the sub-issue (on yes, outbound)
On approval, propose posting **one sub-issue per domain**, each created as a **NATIVE sub-issue of the parent story** on the primary tracker. **Route every tracker action through the tracker adapter** (`create_issue`, `link_child`, `assign`) per [references/tracker-adapters.md](references/tracker-adapters.md); do not hardcode GitHub-only semantics. Per sub-issue:

- **Inline BOTH faces in the body (F5).** The body IS the content, not a pointer. Lead with the **human-readable plan as the body** (what a person opening the ticket reads), then embed the **full AI plan inside a collapsible block** so a teammate, CI, or a fresh agent reads it without filesystem access:
  ```
  <details><summary>Full AI context (for /agentic-plan and implementers)</summary>

  ...the full AI plan: slices, acceptance-criteria mapping, contracts, repos + cross-repo order...

  </details>
  ```
  Keep a **one-line pointer** to the run workspace too (`~/.openadlc/runs/<workspace>/<run-id>/plan/`, never committed), but never post only that path: a teammate / CI / fresh agent cannot read a local file. (Story #14 proved the inline-both-faces body works.)
- **Link it as a native sub-issue (F7), not a text mention.** After creating the child, attach it under the parent via the adapter's `link_child` (GitHub: `gh api -X POST /repos/{owner}/{repo}/issues/{parent}/sub_issues -F sub_issue_id={child_node_id}`, or the GraphQL `addSubIssue` mutation; Jira: a sub-task under the parent; ADO: a parent/child work-item link), per [references/tracker-adapters.md](references/tracker-adapters.md).
- **Assign the operator on create (F6)** via the adapter's `assign` (GitHub: `--assignee @me` on `gh issue create`; if `@me` does not resolve, ask whom once; route per-tracker via the adapter).

**First, dedup per [references/run-isolation.md](references/run-isolation.md):** for each domain check for an existing open sub-issue for the same parent + domain and offer update-vs-new; tag each created sub-issue with the run-id. The plan files (`spec.md`, `Plans.md`, `.json` contracts) stay in the out-of-repo run workspace at the stable `~/.openadlc/runs/<workspace>/<run-id>/plan/` path (never committed) and may additionally be uploaded as **attachments only if the tracker supports it** (GitHub issues take no file attachments via the API, so the inline body carries the content; Jira and ADO accept attachments). **This is the consent CHECKPOINT: STOP and get the operator's explicit yes before posting.** In v0.1 draft the sub-issue(s) and the operator posts them (on GitHub via `gh issue create` + the adapter's link/assign calls); auto-post is a later per-tracker integration. Then `/agentic-implement` runs against a sub-issue, selecting this run by run-id, and opens one PR per touched repo linked to that domain's sub-issue.

## Guardrails
Write no production code here. Reading is local; posting the sub-issue is the only outbound step and it needs the operator's explicit yes.
**Token compression**: when `compression.enabled` (openadlc.yaml, on by default), communicate tersely for AI-internal and inter-agent output per [references/token-compression.md](references/token-compression.md); never compress the human-facing artifacts (the plan summary, the review verdict, the consent prompt).
