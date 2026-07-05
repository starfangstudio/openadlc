---
name: ai-review
description: "Use when the user types /ai-review, or asks to review a change, do a code review, review a PR or branch, or get an adversarial pass on a diff. Runs an independent, fresh-eyes review across concurrent lenses and returns a BLOCK or APPROVE verdict; posting the verdict is gated on the user's yes."
version: 0.1.0
---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# AI Review

An independent, fresh-eyes review of a change. Runs embedded inside ai-implement and also stands alone on any diff, branch, PR, or code the user did not write. Posting a review is gated on the user's yes.

When a `references/<name>.md` link does not resolve relative to this file, locate it under the deployed adlc-core pack (search for the file name, e.g. under `apm_modules/*/adlc-core/references/`) and READ the referenced file before acting on its rule.

## Steps

1. Resolve the target: the current change, a branch, a PR, or pasted code.
2. Review across concurrent lenses: correctness, safety, whether the tests actually assert anything, UI fidelity as a compliance concern (does the build match the design), and fit. Run the lenses in parallel.
3. Return a single BLOCK or APPROVE verdict with file-and-line evidence. Persist the verdict locally.
4. CHECKPOINT, consent: if the verdict is to be posted to a PR or tracker, before asking, write the checkpoint file (`type: post-review`, `checkpoints.md`); the user may also resolve it from the cockpit while you wait. Present it and STOP for an explicit yes before posting. Persisting locally is free; posting is gated.

## Verify
Returns a BLOCK or APPROVE verdict with file-and-line evidence; posting stops for an explicit yes.
