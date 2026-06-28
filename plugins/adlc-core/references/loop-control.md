<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
# The loop control

Every ADLC checkpoint, the intake discovery, the plan gate, and the implement review, offers the operator an optional, bounded refinement loop. This is how the adversarial-iteration rigor an experienced operator reaches for becomes a first-class, operator-controlled feature of the lifecycle, instead of an internal trick.

## What a checkpoint is

A **checkpoint** is a mandatory step the pipeline always runs; it is not always a question to the operator. Three kinds:
- **Automatic checkpoint:** runs without asking (verify a slice, the acceptance-criteria check).
- **Operator ask:** a mandatory step that asks a question and waits (the SDD / TDD method choice, which reviews to run).
- **Consent checkpoint:** a mandatory step where the agent stops and asks the operator for an explicit yes before something goes outbound (post the story, post the sub-issue, push, post a review).

The consent checkpoint is one kind of operator-facing checkpoint, the outbound one; not every checkpoint is a consent checkpoint, and not every checkpoint asks you anything. The two dials below apply only to the operator-facing checkpoints (asks and consent), never to the automatic ones.

## Two dials at every operator-facing checkpoint

Such a checkpoint asks the operator two things:

1. **Consent**: approve, edit, or reject what the step produced.
2. **Rigor**: run the step once (the default), or as a bounded loop.

Consent decides *whether* to proceed; rigor decides *how hard to push first*. The default is always one pass; depth is opt-in.

## The two loop flavors

- **Iterate (refine):** run the step again, building on the last output, deepen the discovery, tighten the plan, fix-and-re-review. Stop when a round adds nothing new, or at the cap.
- **Fan-out and judge (diversify):** run N independent attempts and synthesize or pick the best, several plan approaches scored by a judge, several adversarial review lenses reaching consensus. Best when the solution space is wide.

Each checkpoint has a sensible default flavor (discovery and review iterate; planning can fan out for a hard design); the operator can override.

## The bound is not optional (it guards the operator's tokens)

A loop costs tokens and time; a runaway loop can light a bonfire with the operator's budget. So before a loop runs it MUST declare four things, and the operator sees them up front:

1. **Exit criteria**, concrete. Either a **fixed cap** (N passes) or **"until converged"** with a hard definition (stop after two consecutive rounds add nothing new). "Converged" is never vague.
2. **A hard ceiling** the loop cannot exceed even if not converged. Keep defaults small (a few passes, not dozens). Managed config sets the system maximum; a project can lower it, never silently raise it.
3. **A per-round cost estimate, a real number** (see "Show the four declarations when you offer the loop" below). Not "a cost view" in the abstract: an actual tokens-and-dollars figure for one round, plus the projected total at the default cap, sourced from this run's cost ledger ([references/cost-ledger.md](references/cost-ledger.md)). Then every round ends in a one-screen summary with what that round actually cost and the running total, so the operator can stop early; the loop also halts itself if a declared budget is hit.
4. **Staged escalation.** Start with the smallest pass that could surface the answer, look at the yield, and add capacity in increments only while each increment still finds real, verified results. Do not open with a large fixed fan-out; a hundred agents confirming what the first ten found is waste, not rigor.

A checkpoint loop is never unbounded, never automatic, and never hides its cost. Default is one pass; depth is a deliberate, visible trade. An unbounded or cost-blind loop is the bonfire this design exists to prevent.

## Show the four declarations when you offer the loop (F10)

The four declarations are not a precondition the loop checks after the operator opts in; they are the OFFER. The instant a command surfaces a refine/loop option at a checkpoint (intake refine, the plan gate, the implement review-depth ask), the same message that offers the loop MUST state, in plain sight, before the operator can say yes:

1. **Default cap** , how many rounds run by default (e.g. "2 rounds").
2. **Hard ceiling** , the max it cannot exceed even un-converged (e.g. "ceiling 4"), and where it came from (default, project, or managed config).
3. **Exit criterion** , concrete (the fixed cap, or the "two consecutive rounds add nothing new" convergence rule). Never vague.
4. **Per-round cost estimate** , a REAL number, not a promise of a cost view. Quote tokens and dollars for one round and the projected total at the default cap, e.g. "~38k tokens / ~$0.74 per round, ~$1.48 for 2 rounds."

The operator decides how many iterations and the spend BEFORE saying yes, not after the first round burns. An offer that hides any of the four, or quotes "a cost view" instead of an actual figure, is non-conformant.

### Where the per-round number comes from

The estimate is grounded in this run's measured spend, never guessed. Read the run's cost ledger ([references/cost-ledger.md](references/cost-ledger.md)) and base the per-round figure on the phase this checkpoint loops over:
- **Intake refine** , the cost of the `intake` phase so far (one refine round repeats discovery work of similar shape).
- **Plan gate** , the cost of the `plan` phase (one iterate or one fan-out arm).
- **Implement review depth** , the cost of one `review` pass.

Take the relevant phase's last-round (or per-pass) tokens-and-dollars from the ledger as the per-round estimate; multiply by the default cap for the projected total. For a **fan-out** flavor, multiply by the arm count (N independent attempts cost ~N times one arm, run concurrently). If the ledger has no entry yet for that phase (the very first round), fall back to a documented baseline estimate for the model+effort routing of that phase and label it "estimated, no measured round yet"; replace it with the real number once the first round writes to the ledger. Each round then appends its actuals to the ledger, so the next offer's estimate is tighter than the last.

A worked example of the full offer:

```
Refine the plan? (optional)
  default cap : 2 rounds
  hard ceiling: 4 (project config)
  exit        : stop when 2 consecutive rounds add nothing new
  cost/round  : ~38k tokens / ~$0.74  (from this run's ledger, plan phase)
  projected   : ~$1.48 at the default cap of 2
  flavor      : iterate (or fan-out N=3 approaches -> ~$2.22, judged)
Reply: 1 = proceed as offered  ·  edit the cap/flavor  ·  skip (one pass, done)
```

## Use parallelism, always

A loop is not a slow sequential grind. Wherever there is no data dependency, fan the work out:
- **Fan-out-and-judge** runs its N attempts concurrently, then a judge picks or synthesizes (the parallel-barrier pattern).
- A checkpoint over many items (N review lenses, the slices in a wave, N scenarios) runs them in parallel, not one at a time.
- Flows nest: a round may itself fan out sub-agents, each in its own clean context, and those may fan out again. Dynamic fan-out (scale the width to the work) is encouraged.
- Always **adversarially verify** a fanned-out result before trusting it; parallel speed never buys a skipped check.

Wall-clock should approach the slowest single path, not the sum of all paths. See [references/orchestration.md](references/orchestration.md) for the fan-out, parallel-barrier, pipeline, and judge-panel patterns.

## Cost and policy

Loops cost tokens and time; depth is a deliberate trade the operator makes, more rigor for more cost. An organization MAY set loop defaults per checkpoint and per domain in managed config (for example, a minimum review depth for regulated changes); a project can tighten, never loosen.

The cost figures the offer quotes and the per-round summaries report are not estimates pulled from the air: they read this run's persisted **cost ledger** ([references/cost-ledger.md](references/cost-ledger.md)), which records tokens and dollars per phase (intake / plan / implement / review). That ledger is what makes the cost view real, and what makes model-and-effort routing measurable rather than asserted (the A/B that justifies any downshift, see the model-and-effort-routing section of [references/orchestration.md](references/orchestration.md), compares ledger numbers, not vibes).
