---
name: pr-feature-description
description: "This skill should be used when the user asks to \"write a PR description\", \"generate a pull request description\", \"describe this PR\", \"summarize my changes for a PR\", \"draft a PR body from the diff\", or \"fill in the PR template\". Produces a structured PR description and a Conventional Commits title from a local diff. Generation is local-only; never pushes or posts."
version: 0.1.0
---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# PR feature description

Generate a Conventional Commits title and a templated PR body from a local diff. Generation is read-only and local. **Posting the result to GitHub/GitLab is an outbound action: get the operator's explicit yes first (see Outbound consent).**

## Workflow

1. **Collect the diff** (per repo). The change is on the run branch `adlc/<run-id>`; the base is the repo's default branch at latest (`origin/<default>`), per [references/run-isolation.md](../../references/run-isolation.md). Ask only if the default is ambiguous. In a poly-repo product a run produces **one PR per touched repo**, so generate one description per repo from that repo's diff. Run, in each touched repo's root:
   - `git fetch origin <base> --quiet` (only if network already approved for fetch; otherwise skip)
   - `git diff --stat <base>...HEAD`: file-level overview
   - `git diff <base>...HEAD`: full diff (read; for huge diffs read `--stat` plus per-file diffs of the largest files)
   - `git log --oneline <base>..HEAD`: existing commit messages for intent
2. **Infer intent.** From the diff and commit log, determine: the single primary change, the problem it solves, and any breaking changes, new dependencies, migrations, or config changes.
3. **Pick the type and scope** (table below). One title = one primary type. If the diff genuinely spans unrelated changes, say so and suggest splitting the PR.
4. **Fill the template** (below) verbatim. Leave a section out only if it is truly N/A; never invent test steps, issue numbers, or screenshots. Mark unknowns `unknown` rather than guessing.
5. **Present** the title + body in a single fenced block, ready to copy. Stop here.

## Conventional Commits title

Format (spec 1.0.0):

```
<type>[(scope)][!]: <description>
```

- `description`: imperative mood, lower-case start, no trailing period, aim ≤ 50 chars (hard limit 72).
- `scope`: optional noun for the area touched, e.g. `feat(parser):`. In a feature-modular repo use the feature/module name as scope.
- `!` before the colon marks a breaking change, e.g. `feat(api)!: drop v1 auth`.

| type | use for |
|---|---|
| `feat` | new user-facing capability |
| `fix` | bug fix |
| `docs` | documentation only |
| `refactor` | behavior-preserving restructure |
| `perf` | performance improvement |
| `test` | adding/correcting tests |
| `build` | build system, dependencies |
| `ci` | CI config/scripts |
| `style` | formatting, no code-meaning change |
| `chore` | maintenance, no src/test change |

## PR body template

Fill and emit exactly this structure:

```markdown
## What
<one-sentence summary of the change>

## Why
<the problem or motivation; link the issue if one exists: "Closes #123">

## How
<key implementation decisions a reviewer needs; bullet the notable changes>

## Testing
<exact commands run + result, or manual steps. If not yet verified, write "Not yet verified", do not fabricate>

## Breaking changes / migration
<API/config/schema changes and the upgrade step, or "None">

## Consent and side effects
<per changed artifact, whether it can perform an outbound action (push / post / send / publish / call a write API), or "None">
- `path/to/file.ext`: <outbound capability it adds or touches, e.g. "POSTs to the billing API", "sends email">, gated by <consent point / approval>
- `path/to/other.ext`: no outbound action

## Screenshots
<for UI changes only; otherwise omit this section>
```

Rules: lead with **Why** intent over restating the diff, the reviewer can read the diff. Keep **What** to one sentence. Every claim in **Testing** must be something actually run or a step the author can follow. **Consent and side effects** is the release-time outbound-consent audit trail: list each changed artifact that can reach the network or trigger a write, so the reviewer and the operator can see the blast radius before anything ships. If no changed artifact performs an outbound action, write "None".

## Dedup before opening a PR

One PR per touched repo (per [references/run-isolation.md](../../references/run-isolation.md)): a single-repo run is one PR; a poly-repo product run is one PR per repo, each linked to the **same-domain sub-issue**. Before the operator opens a PR from this body, check that repo for an existing open PR for `adlc/<run-id>` (`gh pr list --head adlc/<run-id> --state open`) and offer update-vs-new. Tag each PR with the run-id so duplicates stay detectable.

## Outbound consent

Local work needs no approval. Anything outbound (publish, push, post) needs an explicit per-action "yes"; see the global consent law.

## Validator → fix loop

Before presenting, self-check and fix any failure:
- Title matches `^(feat|fix|docs|refactor|perf|test|build|ci|style|chore)(\([a-z0-9 _-]+\))?!?: .+` and description is ≤ 72 chars.
- A breaking change in the diff is reflected by `!` and the **Breaking changes** section.
- No fabricated issue numbers, screenshots, or unrun test commands.
- **Why** explains motivation, not just a diff restatement.

## References

- Run isolation (run branch, default base, one-PR-per-run dedup): [references/run-isolation.md](../../references/run-isolation.md)
- Conventional Commits 1.0.0: https://www.conventionalcommits.org/en/v1.0.0/
- GitHub: creating a pull request template: https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/creating-a-pull-request-template-for-your-repository
