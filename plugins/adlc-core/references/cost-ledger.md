<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
# The cost ledger

Every ADLC run records what it actually spent, per phase, to a small ledger in the run workspace. This is what makes the loop-control cost view a real number instead of a hand-wave, and what makes model-and-effort routing measurable instead of asserted. No ledger, no honest "this round costs ~$X" offer; no honest A/B that proves a downshift held quality at lower cost.

## What it measures

Tokens and dollars, broken down by **phase**: `intake`, `plan`, `implement`, `review`. A phase can be entered more than once (a refine loop reruns `plan`; a review loop reruns `review`); each entry is one round / one pass, so the per-round figures loop-control needs fall straight out of the data.

Tokens are the ground truth the harness reports (input + output, and cache-read / cache-write when the harness exposes them). Dollars are derived from tokens times the per-model rate, so a price change re-derives cleanly and the token record never rots.

## Where it lives

In the run workspace from [references/run-isolation.md](references/run-isolation.md), never in the repo, never under `.claude/`:

```
~/.openadlc/runs/<workspace>/<run-id>/cost-ledger.jsonl
```

One JSON object per line (append-only JSONL): a round never rewrites an earlier round, it appends. The file is a run artifact like the plan or the review report, so it is keyed by `<workspace>` + `<run-id>` and travels with the run across worktrees and harnesses. It is never committed and never posted (a cost summary may be shown to the operator at a checkpoint; the raw ledger is internal).

## Schema (one line per round)

```json
{
  "run_id":   "add-login-20260628T141233Z",
  "phase":    "plan",
  "round":    1,
  "flavor":   "iterate",
  "model":    "opus",
  "effort":   "high",
  "tokens":   { "input": 31200, "output": 6800, "cache_read": 18000, "cache_write": 4200 },
  "usd":      0.74,
  "rate_id":  "opus-2026-06",
  "started":  "2026-06-28T14:18:02Z",
  "ended":    "2026-06-28T14:20:41Z",
  "note":     "fan-out arm 2 of 3"
}
```

Field rules:
- `phase` is one of `intake | plan | implement | review`. `round` counts entries into that phase for this run (1-based); the first time a phase runs is `round: 1`.
- `flavor` is `single | iterate | fan-out` so loop-control can tell a one-pass cost from a per-arm cost.
- `model` / `effort` are FAMILY ALIAS + effort tier (`opus`/`sonnet`/`haiku`/`fable` plus `high`/`medium`/`low`), never a pinned version id, matching the routing doctrine in [references/orchestration.md](references/orchestration.md). This is the field the A/B compares across.
- `tokens` records whatever the harness reports; `input` and `output` are required, cache fields are optional (omit when the harness does not expose them).
- `usd` = sum over token kinds of `tokens.<kind>` times the per-kind rate for `rate_id`. `rate_id` pins WHICH price table produced `usd`, so a later rate change is auditable and re-derivable from `tokens`.
- `note` is free text for context (which fan-out arm, which slice, which review lens). Optional.

Fan-out writes one line per arm (N arms = N lines, same `phase` + `round`); the round's cost is their sum. A nested sub-agent's spend rolls up into the phase it serves, it does not get its own phase.

## How a phase writes it

At the END of each phase (and each round of a looped phase), the command/skill appends one line (or N lines for a fan-out) with the round's measured tokens and the derived dollars. Append, never rewrite. A round that is abandoned mid-flight still records what it burned, the ledger reflects real spend, not intended spend.

A tiny per-run total is cheap to recompute on read (sum `usd` over all lines), so the ledger stores only rounds; running totals are derived, never duplicated and never allowed to drift.

## How loop-control reads it (the cost view)

[references/loop-control.md](references/loop-control.md) requires a real per-round cost number when it OFFERS a loop (F10). It gets that number here:

- **Per-round estimate** = the most recent ledger line(s) for the phase this checkpoint loops over (`intake` for an intake refine, `plan` for the plan gate, `review` for an implement review-depth loop). One iterate round costs about one prior round; one fan-out of N costs about N arms.
- **Projected total** = per-round times the default cap (times the arm count for a fan-out).
- **Cold start** (no ledger line for that phase yet, the very first round): fall back to a documented baseline for that phase's model+effort routing, label it "estimated, no measured round yet," and replace it with the real figure the moment the first round appends. Each subsequent offer is tighter than the last because it reads real history.

Per-round summaries during the loop read the same way: the line just appended IS that round's "what it cost," and the sum of lines so far IS the running total the operator watches to stop early. The loop's self-halt-on-budget compares that running sum against the declared budget.

## How model-routing A/Bs use it

The routing doctrine in [references/orchestration.md](references/orchestration.md) allows a model or effort downshift ONLY when an A/B proves quality is identical at the lower cost. The ledger is the cost side of that A/B:

- Run the same representative phase twice, once at the default routing, once at the candidate downshift, into two runs (or two clearly-`note`d entries). The `model` + `effort` + `tokens` + `usd` fields make the delta concrete: candidate vs default, in tokens and dollars, on the same work.
- A downshift is adopted only if quality held (judged separately) AND the ledger shows a real saving. A downshift that the ledger shows did not actually save, or that cost quality, is a regression, not a gain, exactly as the doctrine states.
- Because dollars derive from `tokens` and a pinned `rate_id`, the comparison stays valid even if prices move later: re-derive both sides at the same `rate_id` and the quality-held verdict still holds.

This closes the loop the global routing rule asks for: speed and cost decisions are made against measured numbers from this very pipeline, not against vibes.
