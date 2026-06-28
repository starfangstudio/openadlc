---
name: pr-review-confidence
description: >-
  This skill should be used when the user asks to "score reviewer confidence",
  "filter out low-confidence review comments", "suppress speculative findings",
  "cut the noise from this review", "only show high-confidence issues", "stop
  the reviewer hallucinating nits", "calibrate the review", "reduce false
  positives in the PR review", or wants raw review findings gated before they
  are asserted or posted. Scores each finding by evidence and confidence, drops
  what cannot clear the bar, and permits an explicit "no high-confidence issues"
  outcome. Filters findings only, it writes no code and posts nothing.
version: 0.1.0
---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# PR review: confidence gate

**The one law: no evidence, no comment.** Every finding must point at concrete proof in the diff or retrieved context: a specific `path:line`, a reproducing input, a named failed assertion, or a documented rule it violates. A finding that cannot name its evidence is dropped, not downgraded. "Looks risky", "might be slow", "could break" with nothing to point at is noise.

Take a set of raw review findings and pass each one through an evidence +
confidence gate before it is asserted to the operator or queued for posting. A
reviewer told to find problems will manufacture them; this skill is the
restraint that makes precision the goal, not comment volume.

## When to use
After a reviewer worker (`engineering:code-review`, the security pass, a test
pass, or the orchestrator's merged list) has produced findings, and before those
findings are shown as defects or posted. Run it as the last filter. For a single
trivial diff a reviewer can self-apply the gate inline.

## Step 1: Require evidence per finding
For each raw finding, capture the evidence triple. If any cell is empty, drop it.

| Field | Must contain |
|---|---|
| Location | exact `path:line` in the diff (not "somewhere in this file") |
| Evidence | the code/test/output that proves it, quotable, not paraphrased |
| Consequence | the concrete failure path (input → wrong result / crash / leak) |

## Step 2: Score confidence (low / medium / high)
- **High**: evidence directly shows the defect; the failure path is reproducible from the diff alone. Off-by-one with the boundary visible, unhandled error path with the throwing call in view, secret literal in source.
- **Medium**: evidence is real but the trigger depends on context not in the diff (a caller, runtime config, a value range). State the assumption explicitly.
- **Low**: speculative, style-driven, or "defensive code for a state that cannot occur." No reproducible path.

## Step 3: Apply the gate
- **Drop all `low`.** They do not surface, not even as nits.
- **`medium` surfaces only with its assumption stated** ("if `id` can be negative…") so the author can confirm or dismiss in one read.
- **`high` surfaces as an asserted finding** with location, evidence, consequence, and fix.
- **Demote on doubt:** if you cannot decide high vs medium, it is medium; medium vs low, it is low. Calibration errs toward silence.

## Step 4: Permit silence (the critical path)
If nothing clears the bar, return exactly:

```
No high-confidence issues found.
```

This is a success outcome, never a failure. **Do not invent a comment to avoid
returning empty.** A reviewer that is penalized for silence will hallucinate
findings to fill it, that is the failure mode this whole skill exists to
prevent. An empty gate output means the diff is clean against the evidence
available, and that is a valid, valuable result.

## Output format (exact)
```
# Confidence-gated findings: <branch / PR #>
Gate: <kept>/<raw> findings kept | <dropped-low> low dropped | <medium> medium (assumption-flagged)

## High confidence: asserted
- path:line, <issue> [evidence: <quote/ref>] → <fix>

## Medium: needs author confirmation
- path:line, <issue> (assumes: <the unverified condition>) → <suggested check>

## Dropped (audit trail: optional)
- path:line, <claim>, dropped: no evidence | impossible state | style-only
```
Always print the Gate line so the operator sees how much was filtered. Keep the
Dropped section only when the operator wants the audit trail.

## Discipline
- Precision over coverage. The north-star is **high-confidence finding rate paired with a low false-positive (dismissed-by-author) rate**: not the number of comments produced.
- Do not pad. Do not demand defensive code for impossible states. Do not chase style as if it were correctness.
- Suppression is not deletion of real bugs: a `high` finding is **never** dropped for being inconvenient. The gate cuts speculation, not signal. When unsure whether something is a true positive, keep it as `medium` with the assumption stated rather than silently dropping it.

## Outbound consent

Local work needs no approval. Anything outbound (publish, push, post) needs an explicit per-action "yes"; see the global consent law.

## References
- Luis Mori: *How to Build a Good Agentic Code Reviewer* (evidence-first comments, explicit confidence tiers, the no-comment gate, why penalizing silence causes hallucinated findings, implementation-rate-over-volume metric): https://luismori.dev/article/how-to-build-a-good-agentic-code-reviewer/
- Pairs with `review-change` (the canonical review path) and the built-in `code-review` (correctness pass), run this gate on their merged findings before publishing.
