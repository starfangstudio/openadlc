---
name: agentic-implement
description: "Use when the user types /agentic-implement, or asks to build a plan, implement a sub-issue, or take a slice to green. Builds an approved plan in slices, verifies each, runs an acceptance-criteria check, runs an embedded review, and STOPS at a push gate before anything goes to a remote."
version: 0.1.0
---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# Agentic Implement

Build an approved plan end to end: slices, verification, an acceptance-criteria check, an embedded review, and a final push gate. Nothing reaches a remote without the user's explicit yes.

## Steps

1. Read the plan sub-issue, reassembling its OKF bundle first (on GitHub parse the markers across the body and comments; on Jira/ADO download and untar `<slug>.okf.tgz`), and honor the development dependencies it carries. Ask the user to pick SDD or TDD at the start.
2. Build in slices, each ending in a check that passes or fails. Verify each slice. Local edits, commits, and builds run freely and never stop the user.
3. Run an automatic acceptance-criteria check (your own "is the job done?" against the plan) before any review.
4. Run the review embedded (never skipped): invoke the agentic-review skill, stopping first to ask which reviews to run (code, security, compliance, adversarial lenses, or none for tiny work) with a recommendation, then run the ones picked. The user takes a final look.
5. CHECKPOINT, consent, the push gate: present exactly what would be pushed and STOP for an explicit yes before any `git push` or anything outbound (a deploy, a publish, an API write). There is no "ship" command; this push gate is the only path to a remote, and it never fires without that yes. After the user approves, push. The pipeline ends.

## Verify
Every outbound action stops for an explicit yes at the push gate; local work never blocks. Each slice ends in a check that passes or fails.
