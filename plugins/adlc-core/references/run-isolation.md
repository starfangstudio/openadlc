<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
# Run isolation (ADLC)

Every ADLC run is isolated so multiple sessions can run in parallel in one repo without colliding, on any agentic coding tool. Three mechanisms: a unique run-id, an out-of-repo run workspace, and a per-run branch (with a worktree when sessions are concurrent). Loaded by intake, plan, implement, review, and the planning skills; they cite this file rather than restating it.

## The split: artifacts out of git, code in git
- **ADLC working artifacts** (the intake/living doc, the plan, context, scratch, baselines, logs, review reports) are NOT the repo's content. They live OUTSIDE the repo and are NEVER committed or tracked by the repo's git. They never trigger a "commit to main?" question and never pollute `git status`.
- **The code change** IS the repo's content. It is the only thing that goes into git, on the run branch `adlc/<run-id>`, and ships as a PR.

## Run-id
At the first lifecycle step that writes anything, mint a run-id ONCE and reuse it for the whole run:
`run-id = <slug>-<UTC-timestamp>`, e.g. `add-login-20260628T141233Z` (slug = kebab of the task; timestamp = `date -u +%Y%m%dT%H%M%SZ`).
The timestamp guarantees two same-slug runs never collide. Carry it forward (intake -> plan -> implement -> review): record it in `spec.md` frontmatter (`run_id:`) and in the run branch name, so downstream steps select by run-id, never by feature-name glob.

## Run workspace (OUT of the repo): `~/.openadlc/runs/<workspace>/<run-id>/`
ALL artifacts a run writes live here, keyed by repo name + run-id, never inside the repo and never under `.claude/` of the repo:
- `index.md` + `briefing.md` (living doc + human face) + `story.md` + AI-context concepts (`discovery.md`, `dependencies.md`) , the run workspace IS the OKF bundle (see [okf.md](okf.md)); `index.md` frontmatter carries `status: active|done|abandoned`, the run's terminal-state marker (see [checkpoints.md](checkpoints.md))
- `context.md` (load-context brief)
- `activation.md` (repo-facts detection: the deterministic domain sniff per [domains.md](../../../standard/domains.md), plus the policy candidate-set and activated set from later slices)
- `plan/spec.md`, `plan/Plans.md`, `plan/*.json` (contracts)
- `design-baseline/<node>.png`, `verify/` (rendered screens, fidelity diffs)
- `review-<lens>-<UTC-timestamp>.md` (one file per review lens) and `review-payload.json`
- `checkpoints/<seq>-<type>.md` + `<seq>-<type>.heartbeat` (every consent checkpoint's record, see [checkpoints.md](checkpoints.md))
- `decision/` (ADR staging until merged into the repo on the run branch)

`<workspace>` = the product name for a poly-repo workspace, else the single repo's name (`basename` of `git rev-parse --show-toplevel`). The run-id is WORKSPACE-level: one id for a change that may span several repos. The implementer (in any worktree) reads the plan from this stable absolute path; it does not need to be committed to "travel." NEVER write run artifacts to `.claude/sessions/`, `.claude/plans/<feature>/`, `.claude/runs/`, or bare `context.md` / `review.json` / `design-baseline/` inside the repo. Those are the collision (and git-pollution) sources.

## Run branch: `adlc/<run-id>` (code only)
- Branch from the repo's DEFAULT branch at its latest tip: `git fetch`, then base on `origin/<default>` (resolve via `git symbolic-ref refs/remotes/origin/HEAD`; fall back to `main`). A run never branches off another run's state.
- ALL of a run's CODE commits go on `adlc/<run-id>`. NEVER commit to `main` or a shared branch, and never commit the run workspace (it is out of the repo). One PR per run, from `adlc/<run-id>`, at the end. `implementation-lead` integrates slice work into `adlc/<run-id>` (never main); slice worktrees nest as `adlc/<run-id>/<slice-id>`.

## Concurrent sessions: worktree isolation
A git worktree gives TRUE isolation within one repo: its own working directory + its own branch, sharing only the `.git` object store (git forbids two worktrees on the same branch). Edits and commits in one never touch another. (node_modules / build are gitignored, so each worktree needs its own `npm install`, or symlink the deps in.)

- **Single run, no other run active:** create `adlc/<run-id>` in place and work on it. Branch isolation is enough; artifacts are out of the repo regardless.
- **A run starts while another is active in this checkout** (detected via `git worktree list`, a live `adlc/*` branch, or an active `~/.openadlc/runs/<workspace>/*` with no terminal state): do NOT share the checkout. Auto-create an isolated worktree, then have the operator reopen there (a running session cannot relocate itself):
  `git worktree add <wt> -b adlc/<run-id> origin/<default>`, then `cd <wt> && claude` (or the agentic coding tool's launch command).
  The fuel-machine COORDINATOR does this end to end: a worktree per task, a session launched in each.
- **Worktree location:** outside the indexed workspace, to avoid clutter and editor-scan freezes: `~/.openadlc/worktrees/<repo>/<run-id>/`.

## Workspace shapes + multi-repo
A run is scoped to a WORKSPACE, one of four shapes:
1. **Single repo** , the cwd is one git repo. The run operates on it.
2. **Monorepo** , one git repo holding many packages. Still one branch + one PR; package structure is internal (the domain/package fan-out handles it).
3. **Poly-repo product** , several git repos that form ONE product (e.g. `shared-components` + `web-app` + `backend`). A run SPANS the member repos it touches. Declared in `openadlc.yaml` at the workspace root.
4. **Unrelated repos under a parent** (no `workspace:` declaration) , not a product. The repo-anchor step asks which repo, or offers to declare them a workspace; ADLC never silently operates on the parent.

The declaration is how ADLC tells a poly-repo product (#3) from unrelated repos (#4):
```yaml
# openadlc.yaml at the workspace root
workspace:
  repos: [shared-components, web-app, backend]   # member repo paths
  primary: web-app                                # where the parent story posts
```
Undeclared parent of repos -> ask, and offer to write the declaration.

### A run spans the repos it touches
- The **run-id is workspace-level** (one id for the whole cross-repo change); the run workspace is `~/.openadlc/runs/<workspace>/<run-id>/` and records, per domain, which repos are touched and the **cross-repo dependency order** (e.g. `shared-components` before `web-app`).
- Each touched repo gets the **`adlc/<run-id>` branch** (and a worktree when concurrent). Code commits go there, never main.

### Tracker + PR hierarchy
```
Parent story            -> primary tracker (the `primary` repo, or the single repo)
  |- sub-issue: domain A (e.g. web)        linked to the parent story
  |    |- PR: web-app           on adlc/<run-id>   linked to the web sub-issue
  |    \- PR: shared-components on adlc/<run-id>   linked to the web sub-issue
  \- sub-issue: domain B (e.g. backend)
       \- PR: backend          on adlc/<run-id>   linked to the backend sub-issue
```
- **One sub-issue per DOMAIN** (web, backend, android, ...), the same "one story fans out per domain" rule: /ai-plan produces one plan + one sub-issue per domain.
- **One PR per touched repo**, linked to the **domain sub-issue of the same domain** (the repos a domain touches share that domain, so their PRs hang off that one sub-issue). A domain may span several repos.
- **Cross-repo merge order (full orchestration):** PRs merge in dependency order , base/shared repos before their consumers (`shared-components` PR merges before the `web-app` PR that uses it). The lifecycle sequences this now; the fuel-machine coordinator drives it at scale.

### Tracker actions go through the adapter (never hardcode one tracker)
Every tracker write routes through the four-verb adapter in [references/tracker-adapters.md](tracker-adapters.md) (`create_issue`, `link_child`, `set_status`, `assign`); the adapter holds the per-tracker mapping (GitHub, Jira) so the lifecycle prose stays tracker-neutral. Three rules are mandatory on every run:
- **Native sub-issue, not a text mention:** after `create_issue` makes a child plan issue, `link_child` MUST attach it as a real, native child of the parent so the tracker shows the hierarchy (GitHub sub-issue, Jira sub-task). A "child of #N" line in the body is not a sub-issue and does not count.
- **Auto-assign on create:** `create_issue` assigns the operator at creation so the work has an owner from the start (GitHub `--assignee @me`, Jira `assignee`). If the operator's account does not resolve, ask once who to assign and reuse the answer for the run.
- **In-progress at implement start:** at the start of /ai-implement, after the sub-issue is resolved, `set_status` moves the item to in-progress so the board reflects active work (GitHub "status: in progress" label or the Project status field, Jira status transition). Statuses are declared by the adapter, never invented inline.

These are tracker writes, so they are outbound: each stops at the consent checkpoint for an explicit yes before it fires, per [references/loop-control.md](loop-control.md).

## Portability across agentic coding tools
`~/.openadlc/` is OpenADLC's own namespace, identical across every agentic coding tool (Claude Code, OpenAI Codex, GitHub Copilot, Cursor, Antigravity CLI). The run workspace path, the run-id, the branch convention, and the git/PR flow are all independent of the agentic coding tool. Only the command/skill/hook DEPLOYMENT differs per tool, and APM compiles that to each tool's native format (`.claude/` for Claude, `.github/` for Copilot, AGENTS/prompts for Codex, the Antigravity plugin format, etc.). Never hardcode a single tool's config dir for run artifacts; always use `~/.openadlc/runs/<workspace>/<run-id>/`. (Gemini CLI was retired June 2026; its successor is Antigravity CLI.)

## Dedup before any outbound create
Before creating a tracker issue (intake), a plan sub-issue, a PR, or a PR review, check for an existing open one and offer update-vs-new:
- intake / issue-change-analyzer: `gh issue list --search "<slug>" --state open` (+ scan active `~/.openadlc/runs/<workspace>/*` for the same slug) before `gh issue create`.
- plan sub-issue: search for an open sub-issue for the same parent + domain.
- PR review (`pr-review-publisher`): embed `<!-- adlc-run: <run-id> -->` in the body; update-or-skip if a review with this run-id exists.
- ticket claim (`dev-commit-linker`): one ticket -> one run; stop-and-ask if another open `adlc/*` branch or PR already references it.

Tag created issues / PRs / reviews with the run-id so duplicates are detectable.
