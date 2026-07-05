<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
# Run isolation

Every run is isolated, so several sessions can run in parallel in one repo without colliding, on any harness. Three mechanisms: a unique **run-id**, an out-of-repo **run workspace**, and a per-run **branch** (with a worktree when sessions are concurrent).

## The split: artifacts out of git, code in git

- **ADLC working artifacts** (the living doc, the plan, context, baselines, logs, review reports) are not the repo's content. They live outside the repo and are never committed. They never pollute `git status` or trigger a "commit to main?" question.
- **The code change** is the repo's content. It is the only thing that goes into git, on the run branch, and ships as a PR.

## Run-id

At the first step that writes anything, a run-id is minted once and reused for the whole run:

```
run-id = <slug>-<UTC-timestamp>       e.g. add-login-20260628T141233Z
```

The timestamp guarantees two same-slug runs never collide. It is carried forward (intake to plan to implement to review), recorded in `spec.md` frontmatter and the branch name, so downstream steps select a run **by run-id**, never by matching a feature name.

## Run workspace (out of the repo)

```
~/.openadlc/runs/<workspace>/<run-id>/
```

Everything a run writes lives here: the OKF bundle (see [OKF bundles](okf-bundles.md)), the context brief, the plan, design baselines, verify evidence, review reports, and ADR staging. `<workspace>` is the product name for a poly-repo workspace, else the single repo's name. The run-id is **workspace-level**: one id for a change that may span several repos. The implementer reads the plan from this stable absolute path; it does not need to be committed to travel. Nothing is ever written to the repo's `.claude/` directory.

## Run branch (code only)

```
adlc/<run-id>
```

Branched from the repo's default branch at its latest tip, never off another run's state. All of a run's code commits go here, never to `main` or a shared branch. One PR per touched repo, at the end.

## Concurrent sessions: worktrees

A git worktree gives true isolation within one repo: its own working directory and branch, sharing only the `.git` object store.

- **Single run, nothing else active:** create `adlc/<run-id>` in place. Branch isolation is enough.
- **A run starts while another is active in this checkout:** the run does not share the checkout. It auto-creates an isolated worktree (at `~/.openadlc/worktrees/<repo>/<run-id>/`) and the operator reopens there.

## Workspace shapes

A run is scoped to a workspace, one of four shapes:

1. **Single repo:** the cwd is one git repo.
2. **Monorepo:** one git repo, many packages. Still one branch and one PR.
3. **Poly-repo product:** several repos that form one product. A run spans the member repos it touches. Declared in [`openadlc.yaml`](../config/) at the workspace root (`workspace.repos` + `primary`).
4. **Unrelated repos under a parent:** not a product. The command asks which repo, or offers to declare a workspace. It never silently operates on the parent.

## Tracker and PR hierarchy

```
Parent story            -> primary tracker (the primary repo, or the single repo)
  |- sub-issue: domain A (web)         linked to the parent story
  |    |- PR: web-app            on adlc/<run-id>   linked to the web sub-issue
  |    \- PR: shared-components  on adlc/<run-id>   linked to the web sub-issue
  \- sub-issue: domain B (backend)
       \- PR: backend           on adlc/<run-id>   linked to the backend sub-issue
```

- **One sub-issue per domain** (web, backend, android, and so on).
- **One PR per touched repo**, linked to the sub-issue of its domain.
- **Cross-repo merge order:** base and shared repos merge before their consumers (for example `shared-components` before `web-app`).

## Harness portability

`~/.openadlc/` is OpenADLC's own namespace, identical across every harness. The run workspace path, the run-id, the branch convention, and the git and PR flow are all harness-independent. Only the command, skill, and hook deployment differs per harness, and APM compiles that to each harness's native format.

## Dedup before any outbound create

Before creating a tracker issue, a plan sub-issue, a PR, or a PR review, the command checks for an existing open one and offers update-vs-new, tagging what it creates with the run-id so duplicates stay detectable. Every such create is outbound and stops at the [consent checkpoint](checkpoints.md).

## Source

- Reference: [plugins/adlc-core/references/run-isolation.md](../../plugins/adlc-core/references/run-isolation.md)
