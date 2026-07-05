---
name: pr-review-publisher
description: "This skill should be used when the user asks to \"post the review\", \"publish review comments to the PR\", \"send my review findings to GitHub\", \"leave inline comments on the pull request\", \"approve/request changes on the PR\", or otherwise wants a completed local code review pushed to a GitHub pull request as a review (summary + inline line comments). It assembles the review payload locally and STOPS to ask the operator for an explicit yes before any outbound write."
version: 0.1.0
---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# PR Review Publisher

Publish a finished code review to a GitHub PR as a single review object: a summary body plus inline comments anchored to specific lines, with one event (`COMMENT`, `REQUEST_CHANGES`, or `APPROVE`).

## CRITICAL: outbound consent (the law)

Posting a review SENDS data to GitHub (the internet). This is an outbound write and needs the operator's explicit yes.

- Do ALL assembly locally. Build the payload file, render the report, and STOP.
- NEVER run `gh api ... -X POST`, `gh pr review`, or any MCP write until the operator replies with an explicit "yes" to THIS review.
- No standing approval. Each publish needs its own fresh "yes".
- If anything in the payload is uncertain (wrong commit, wrong line, unresolved finding), do NOT publish, surface it and ask.

## Workflow

### 1. Gather inputs (read-only) and dedup
Confirm the PR and the exact commit the review targets:
```
gh pr view <pr> --json number,headRefName,headRefOid,baseRefName,url,title
```
Use `headRefOid` as the `commit_id` so comments anchor to the reviewed commit. If the review was done against an older commit, use that SHA instead, never let it default silently.

**Dedup before posting (per [references/run-isolation.md](references/run-isolation.md)).** Check for an existing review from this run, search prior reviews for the run-id marker `<!-- adlc-run: <run-id> -->`:
```
gh pr view <pr> --json reviews --jq '.reviews[] | select(.body | contains("adlc-run: <run-id>"))'
```
If one exists, offer update-vs-new (update the existing review or skip) rather than posting a duplicate. The PR itself should be the run's PR (`adlc/<run-id>`). In a poly-repo product a run has **one PR per touched repo**: publish a review per repo, each against that repo's PR, each carrying the same run-id marker, and dedup per repo.

### 2. Choose the event
Map the review outcome to exactly one event:

| Outcome | event |
|---|---|
| Blocking issues found | `REQUEST_CHANGES` |
| Non-blocking notes only | `COMMENT` |
| Looks good, sign-off | `APPROVE` |

`body` is REQUIRED for `REQUEST_CHANGES` and `COMMENT`. Default to `COMMENT` unless the operator stated the intent.

### 3. Persist the verdict locally (always), then assemble the payload
**PERSIST first, on every run, gated or not.** Write the human-readable verdict to this run's `~/.openadlc/runs/<workspace>/<run-id>/review-<lens>-<UTC-timestamp>.md` (the out-of-repo workspace per [references/run-isolation.md](references/run-isolation.md); never committed, never a bare `review.json`/`review-<date>.md`, never inside the repo). This happens BLOCK or APPROVE, before the consent prompt, whether or not the operator ever says yes; **never leave the review as only a commit message**. Posting is gated; persisting is not.

Then write the payload to `~/.openadlc/runs/<workspace>/<run-id>/review-payload.json`; do NOT post it. When the run spans several repos, qualify both filenames per repo (`review-<repo>-<UTC-timestamp>.md`, `review-payload-<repo>.json`) so the per-repo reviews do not overwrite each other. Each inline comment needs `path`, `body`, and `line` (the line number in the file's new version; use `side: "LEFT"` for deleted lines, `RIGHT` is default). For multi-line comments add `start_line` + `start_side`. Embed the run-id marker `<!-- adlc-run: <run-id> -->` in the `body` so the review is tagged and dedup can find it.

**Verify-real-run applies to review evidence too.** If the verdict claims a visual or behavioral criterion is met, the persisted `review-*.md` must cite REAL-run evidence: web = dev-server smoke + a saved screenshot; native = build + install + LAUNCH on sim/emulator + a saved screenshot. A green build or a SwiftUI/preview/snapshot render is NOT sufficient, and a "looks right" claim with no saved artifact does not earn an `APPROVE`. (Cautionary example: the iOS home build passed verify with screenshots but the shipped, unsigned binary did not actually launch.)

```jsonc
// ~/.openadlc/runs/<workspace>/<run-id>/review-payload.json, out-of-repo artifact, NOT yet sent
{
  "commit_id": "<headRefOid>",
  "event": "COMMENT",
  "body": "## Review summary\n<2-4 sentence overview>\n<!-- adlc-run: <run-id> -->",
  "comments": [
    { "path": "src/foo.kt", "line": 42, "side": "RIGHT", "body": "Null deref when `x` is empty." },
    { "path": "src/bar.kt", "start_line": 10, "line": 14, "side": "RIGHT", "body": "Extract this into a helper." }
  ]
}
```

Rules:
- One comment per distinct finding. Anchor to the line the reader needs to see.
- Keep `body` actionable: state the problem and the fix, not just "this is wrong".
- A line that is not part of the diff will 422 on publish, only anchor to changed lines (or use the summary `body` for file-wide notes).

### 4. Render the consent report and STOP
Print a clear, sectioned report the operator can scan in seconds, then STOP and wait for an explicit "yes". Lead with the verdict, impact, and risk, not a wall of comments:

```
🚦 READY TO PUBLISH, review for <repo> PR #<n> "<title>"
   <url>   ·   target commit <headRefOid short>

VERDICT      ✅ Approve | 🟠 Comment | ⛔ Request changes
IMPACT       <what this PR changes, 1 line: e.g. "adds offline cache to feed; touches 4 files, 1 module">
RISK         <Low | Medium | High>, <why: e.g. "touches auth token storage; no migration; behind a flag">

SUMMARY
  <2–4 sentence overview that will be the review body>

BLOCKING (<n>)            ← these drive REQUEST_CHANGES
  • src/foo.kt:42, null deref when `x` is empty → guard / Result
SUGGESTIONS (<n>)
  • src/bar.kt:10-14, extract helper; duplicated with Baz
POSITIVE
  • clean separation of the cache behind an interface

Sends 1 review (event=<…>) + <n> inline comments to GitHub. Reply "yes" to publish, or edit first.
```
Keep IMPACT and RISK honest and specific, they are what the operator decides on. If RISK is High, say what would break and whether it's reversible.

### 5. Publish, ONLY after "yes"
Post the whole review in one call (atomic, summary + all comments together):
```
gh api repos/{owner}/{repo}/pulls/<pr>/reviews \
  --method POST --input ~/.openadlc/runs/<workspace>/<run-id>/review-payload.json
```
`{owner}/{repo}` resolve from the current repo; pass `-R <owner>/<repo>` if ambiguous.

For a summary-only review with no inline comments, the high-level command is simpler:
```
gh pr review <pr> --comment --body-file summary.md   # or --request-changes / --approve
```

**Route the verdict through the tracker adapter.** The PR-review post is one part of the verdict's outbound. When the verdict ALSO creates or updates a tracker item (a review-gate item, a re-opened finding, or a status change on the change's tracker item), do NOT hardcode GitHub-only calls in prose: route those writes through the tracker-adapter actions `create_issue` / `link_child` / `set_status` / `assign`, with per-tracker mappings (GitHub issues, Jira issues+sub-tasks), per [references/tracker-adapters.md](references/tracker-adapters.md). **Assign the operator on create**: GitHub adds `--assignee @me` to `gh issue create` (ask whom once if `@me` does not resolve); Jira maps to its assignee field via the adapter. Each adapter write is outbound and stays behind the same explicit "yes" as the PR-review post.

### 6. Verify
Confirm it landed and report the URL:
```
gh pr view <pr> --json reviews --jq '.reviews[-1] | {state, author: .author.login, url: .url}'
```
If publish returned `422 Unprocessable Entity`, the usual cause is a comment anchored to a line outside the diff or a stale `commit_id`: fix the payload, re-render the consent report, and get the operator's explicit yes again before retrying.

## Validator → fix loop
Before rendering the report, sanity-check the artifacts locally:
- The persisted `~/.openadlc/runs/<workspace>/<run-id>/review-<lens>-<UTC-timestamp>.md` exists (the verdict was written, not left as a commit message).
- `jq empty ~/.openadlc/runs/<workspace>/<run-id>/review-payload.json`: valid JSON.
- Every comment has `path` + `body` + (`line` or `position`).
- `event` is one of `APPROVE` / `REQUEST_CHANGES` / `COMMENT`, and `body` is non-empty for the latter two.
- `commit_id` equals the SHA the review was actually done against.
- If the verdict is `APPROVE` on a visual or behavioral criterion, the persisted `review-*.md` cites a saved real-run artifact (screenshot path), not a build/preview.

Any failure → fix the file, re-validate, then proceed. Never publish an unvalidated payload.

## References
- Run isolation (per-run payload path, run-id tagging, PR-review dedup): [references/run-isolation.md](references/run-isolation.md)
- Tracker adapters (create_issue / link_child / set_status / assign; GitHub, Jira mappings): [references/tracker-adapters.md](references/tracker-adapters.md)
- GitHub REST API: Create a pull request review: https://docs.github.com/en/rest/pulls/reviews#create-a-review-for-a-pull-request
- `gh pr review` manual: https://cli.github.com/manual/gh_pr_review
