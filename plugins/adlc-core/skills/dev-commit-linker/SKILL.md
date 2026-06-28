---
name: dev-commit-linker
description: >-
  This skill should be used when the user asks to "link this commit to a ticket",
  "add the issue number to the commit", "reference the Jira/issue in the commit
  message", "write a conventional commit that closes #N", "add a git trailer", or
  otherwise wants commit messages structured so a tracker auto-links or auto-closes
  the work item. Covers Conventional Commits format, git trailers (Refs/Closes/Fixes),
  and GitHub/Jira closing keywords.
version: 0.1.0
---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# dev-commit-linker

Produce commit messages that link to their tracking ticket using Conventional Commits + git trailers, so the tracker (GitHub, GitLab, Jira) auto-links or auto-closes the work item. Apply locally only, never push or comment without the operator's explicit yes.

## When to use
- A change resolves or relates to a known ticket/issue id and the commit must carry that link.
- The user asks for a conventional commit, a footer reference, or a closing keyword.

## Required input: STOP and ask if missing
- **Ticket id(s)**: e.g. `#142`, `PROJ-88`, `org/repo#7`. Do NOT invent one. If unknown, ask the user or check the branch name (`git rev-parse --abbrev-ref HEAD`, which on an ADLC run is `adlc/<run-id>` and encodes the run slug).
- **Relationship**: does this commit *close* the ticket or merely *reference* it? Picks the trailer.
- **Tracker**: GitHub/GitLab vs Jira/other; decides keyword vs plain ref.

**Commit on the run branch only.** All of a run's commits go on `adlc/<run-id>`, never `main` or a shared branch (per [references/run-isolation.md](references/run-isolation.md)). The run-id is workspace-level: in a poly-repo product each touched repo carries its own `adlc/<run-id>` branch, and commits go on the branch of whichever repo the change lives in.

**Ticket-claim dedup (one ticket -> one run).** Before claiming a ticket for this run, check whether another open `adlc/*` branch or PR already references it; if so, STOP and ask (update the existing run vs start a new one) rather than double-claiming.

## Commit format
```
<type>[optional scope][!]: <description>

[optional body, what & why, wrapped ~72 cols]

[trailers]
```
Rules (per spec): a type (`feat`, `fix`, `docs`, `refactor`, `test`, `chore`, …) then optional `(scope)`, optional `!` for a breaking change, then `: ` and a concise description. Body starts one blank line after the description. Trailers start one blank line after the body.

## Trailer = the link
A trailer is `Token: value` (token uses hyphens for spaces). One blank line before the trailer block. Choose by relationship and tracker:

| Goal | Trailer | Effect |
|---|---|---|
| Reference only (no close) | `Refs: #142` | Links, leaves ticket open |
| Auto-close on default-branch merge (GitHub/GitLab) | `Closes: #142` / `Fixes: #142` | Closes the issue when merged |
| Cross-repo close (GitHub) | `Closes: org/repo#142` | Needs push access to that repo |
| Jira (no native keyword) | `Refs: PROJ-88` + id in description | Jira links by id scan |
| Breaking change | `BREAKING CHANGE: <desc>` | Major-version / migration signal |

Keywords (`Closes`/`Fixes`/`Resolves`) are case-insensitive and the colon is optional, but pick one casing and keep it consistent.

## Procedure
1. Gather the required input above; STOP and ask on any gap.
2. Draft the message. Example:
   ```
   fix(auth): reject expired refresh tokens

   Tokens past their TTL were silently refreshed. Validate exp
   before issuing a new access token.

   Fixes: #142
   ```
3. Append/verify the trailer with the canonical tool rather than hand-editing, run:
   `git commit -m "<subject>" -m "<body>" --trailer "Fixes: #142"`
   (or for an existing file: `git interpret-trailers --in-place --trailer "Fixes: #142" .git/COMMIT_EDITMSG`).
4. Verify: `git log -1 --format=%B` shows the trailer on its own line after a blank line; `git interpret-trailers --parse <<<"$(git log -1 --format=%B)"` echoes it back. If parse drops it, the blank-line/format is wrong, fix and re-run.

## Optional: enforce via hook (suggest, don't auto-install)
A `commit-msg` hook can normalize trailers across the team. Offer this; install only if asked:
```sh
#!/bin/sh
git interpret-trailers --trim-empty --in-place "$1"
```

## Outbound consent

Local work needs no approval. Anything outbound (publish, push, post) needs an explicit per-action "yes"; see the global consent law.

## References
- [Conventional Commits v1.0.0](https://www.conventionalcommits.org/en/v1.0.0/), message structure, footers, BREAKING CHANGE.
- [git-interpret-trailers](https://git-scm.com/docs/git-interpret-trailers), trailer token/separator rules, `--trailer`, `--parse`, hook usage.
- [GitHub: Using keywords in issues and pull requests](https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/using-keywords-in-issues-and-pull-requests), closing keywords, casing, cross-repo syntax, default-branch-only behavior.
