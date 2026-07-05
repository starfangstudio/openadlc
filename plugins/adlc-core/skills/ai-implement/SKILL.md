---
name: ai-implement
description: "Use when the user types /ai-implement, or asks to build a plan, implement a sub-issue, or take a slice to green. Builds an approved plan in slices, verifies each, runs an acceptance-criteria check, runs an embedded review, and STOPS at a push gate before anything goes to a remote."
version: 0.1.0
---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# AI Implement

Build an approved plan end to end: slices, verification, an acceptance-criteria check, an embedded review, and a final push gate. Nothing reaches a remote without the user's explicit yes.

When a `references/<name>.md` link does not resolve relative to this file, locate it under the deployed adlc-core pack (search for the file name, e.g. under `apm_modules/*/adlc-core/references/`) and READ the referenced file before acting on its rule.

## Steps

1. Read the plan sub-issue, reassembling its OKF bundle first (on GitHub parse the markers across the body and comments; on Jira download and untar `<slug>.okf.tgz`), and honor the development dependencies it carries. Ask the user to pick SDD or TDD at the start.
2. Build in slices, each ending in a check that passes or fails. Verify each slice. Local edits, commits, and builds run freely and never stop the user.
3. Run an automatic acceptance-criteria check (your own "is the job done?" against the plan) before any review.
4. Run the review embedded (never skipped): invoke the ai-review skill, stopping first to ask which reviews to run (code, security, compliance, adversarial lenses, or none for tiny work) with a recommendation, then run the ones picked. The user takes a final look.
5. CHECKPOINT, consent, the push gate: before asking, write the checkpoint file (`type: push`, `checkpoints.md`). Present exactly what would be pushed and STOP for an explicit yes before any `git push` or anything outbound (a deploy, a publish, an API write). There is no "ship" command; this push gate is the only path to a remote, and it never fires without that yes. After the user approves, push, and set `index.md`'s `status: done` (or `abandoned`), the run's terminal state (`checkpoints.md`). The pipeline ends.

## Verify
Every outbound action stops for an explicit yes at the push gate; local work never blocks. Each slice ends in a check that passes or fails.
