---
name: issue-change-analyzer
description: >-
  This skill should be used when the user asks to "analyze this ticket", "scope
  this issue", "do an impact analysis", "what does this change touch", "break
  this issue into changes", "what's the blast radius of X", or hands over a
  bug/feature ticket and wants it turned into scoped, traceable, reviewable
  units of work before any code is written. Produces a forward/backward
  traceability map (requirement -> code -> tests) and a blast-radius report.
version: 0.1.0
---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# Issue Change Analyzer

Turn one ticket/issue into a set of small, scoped, traceable changes plus an
impact (blast-radius) report. Read-only investigation only, write no code here.
The output feeds planning (`create-plan`) and implementation (`implement-change`).

## When to run
- A bug or feature ticket exists and the work hasn't been scoped yet.
- Someone asks "what does this touch?" / "how big is this?" / "what could break?"

## Procedure

### 1. Extract intent (from the ticket) + detect the workspace shape
- Restate the ask in one sentence. List explicit acceptance criteria.
- Mark anything not stated in the ticket as `unknown`: never invent
  requirements, IDs, or behavior. Ask the operator to fill `unknown`s if they
  block scoping.
- Detect the workspace shape (single repo / monorepo / poly-repo product
  declared in `openadlc.yaml` / undeclared parent of repos), per
  the `references/run-isolation.md` reference in the **adlc-core** pack. For a poly-repo product the
  parent story posts to the `primary` repo's tracker. For an undeclared parent of
  repos, STOP and ask which repo (or offer to declare the workspace); never
  silently scope against the parent.

### 2. Locate the anchors (backward trace: requirement -> code)
For each requirement/criterion, find the code that implements it today.
```
# entry points, symbols, and call sites, adapt the pattern to the repo
grep -rn "<feature-symbol>" --include='*.<ext>' .
git log --oneline -n 20 -- <suspected-path>     # who touched this area, why
git grep -l "<api-or-string>"                    # config, resources, strings
```
Record each anchor as `requirement -> file:line`. A requirement with no anchor
is either new code or a missing `unknown`: flag it.

### 3. Trace the blast radius (forward trace: code -> dependents)
From each anchor, walk outward to everything a change would ripple into:
- **Callers / references**: who calls this symbol, reads this field, imports
  this module (`grep`/`git grep` for the symbol and its public surface).
- **Cross-module boundaries**: does the change cross an `-api`/interface line?
  Touching a public/exported surface is higher-risk than a private internal.
- **Cross-repo boundaries** (poly-repo product): does a change in one member
  repo ripple into a consumer repo (e.g. a `shared-components` export consumed by
  `web-app`)? Name the touched repos and the merge order they imply (base/shared
  before consumers), per the `references/run-isolation.md` reference in the **adlc-core** pack.
- **Tests**: existing tests covering the anchors (these must stay green).
- **Non-code artifacts**: config, DB schema/migrations, feature flags,
  serialized formats, public/over-the-wire contracts, docs, i18n strings.

### 4. Decompose into scoped changes
Split the work into the smallest independently-reviewable units. Each change:
- has one clear purpose and its own verification (a pass/fail check);
- prefers deleting/simplifying over adding lines;
- names its files, its risk (low/med/high), and what it depends on.
Order them so each step keeps the build/tests green (refactor-before-feature).

### 5. Emit the report (exact format below)
Use this Markdown skeleton verbatim:
```
## Change analysis: <ticket id / title>

**Intent:** <one sentence>
**Acceptance criteria:** <bulleted, from ticket>
**Workspace:** <single | monorepo | poly-repo product | undeclared parent> ; primary tracker: <repo>
**Unknowns (blocking):** <list, or "none">

### Traceability map
| Requirement | Anchor (file:line) | Forward impact (dependents) | Tests |
|---|---|---|---|
| <req> | <path:line> | <callers / config / contracts> | <test files> |

### Scoped changes (in order)
1. **<title>**: purpose; files: <list>; risk: <low/med/high>; depends on: <#/none>; verify: <check>
2. ...

### Blast radius
- **Touches public/contract surface:** <yes+what / no>
- **Repos touched + merge order:** <repo -> repo (base/shared before consumers) / single repo>
- **Migrations / flags / serialized formats:** <list / none>
- **Highest-risk area:** <where + why>
- **Out of scope (flagged, not done):** <list>
```

## Dedup before creating a tracker issue
If this analysis turns into a tracker issue, the **parent story posts to the primary tracker** (the `primary` repo for a poly-repo product, else the single repo), with **one sub-issue per domain** (web/backend/android/...); the per-domain repos and merge order are recorded for planning. First check for an existing open one and offer update-vs-new, per the dedup section of the `references/run-isolation.md` reference in the **adlc-core** pack:
`gh issue list --search "<slug>" --state open` (and scan active `~/.openadlc/runs/<workspace>/*` for the same slug) before any `gh issue create`. Tag the created issue with the run-id so duplicates stay detectable. Creating/updating the issue is outbound and needs the operator's explicit yes first, never from this skill.

## Quality gates
- Every requirement maps to at least one anchor OR is flagged new/`unknown`.
- Every scoped change has its own pass/fail verification.
- Cross-`-api` / public-contract changes are called out explicitly in the blast
  radius, these are the expensive ones.
- No outbound action here (read-only). Pushing/posting needs the operator's
  explicit yes first, later, never from this skill.

## References
- Run isolation (run-id, dedup before any outbound create): the `references/run-isolation.md` reference in the **adlc-core** pack.
- Jama Software: What Is Traceability (bidirectional / forward+backward, impact
  analysis, scope control): https://www.jamasoftware.com/requirements-management-guide/requirements-traceability/what-is-traceability/
- Jama Software: Four Best Practices for Requirements Traceability:
  https://www.jamasoftware.com/requirements-management-guide/requirements-traceability/four-best-practices-for-requirements-traceability/
