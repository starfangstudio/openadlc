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

## The bound is not optional (it guards against a runaway loop)

A loop takes time and passes; a runaway loop grinds on well past the point where it stops finding anything new. So before a loop runs it MUST declare three things, and the operator sees them up front:

1. **Exit criteria**, concrete. Either a **fixed cap** (N passes) or **"until converged"** with a hard definition (stop after two consecutive rounds add nothing new). "Converged" is never vague.
2. **A hard ceiling** the loop cannot exceed even if not converged. Keep defaults small (a few passes, not dozens). Managed config sets the system maximum; a project can lower it, never silently raise it.
3. **Staged escalation.** Start with the smallest pass that could surface the answer, look at the yield, and add capacity in increments only while each increment still finds real, verified results. Do not open with a large fixed fan-out; a hundred agents confirming what the first ten found is waste, not rigor.

A checkpoint loop is never unbounded and never automatic. Default is one pass; depth is a deliberate, visible trade.

## Show the three declarations when you offer the loop

The three declarations are not a precondition the loop checks after the operator opts in; they are the OFFER. The instant a command surfaces a refine/loop option at a checkpoint (intake refine, the plan gate, the implement review-depth ask), the same message that offers the loop MUST state, in plain sight, before the operator can say yes:

1. **Default cap** , how many rounds run by default (e.g. "2 rounds").
2. **Hard ceiling** , the max it cannot exceed even un-converged (e.g. "ceiling 4"), and where it came from (default, project, or managed config).
3. **Exit criterion** , concrete (the fixed cap, or the "two consecutive rounds add nothing new" convergence rule). Never vague.

The operator decides how many iterations BEFORE saying yes, not after the first round runs. An offer that hides any of the three is non-conformant.

A worked example of the full offer:

```
Refine the plan? (optional)
  default cap : 2 rounds
  hard ceiling: 4 (project config)
  exit        : stop when 2 consecutive rounds add nothing new
  flavor      : iterate (or fan-out N=3 approaches, judged)
Reply: 1 = proceed as offered  ·  edit the cap/flavor  ·  skip (one pass, done)
```

## Use parallelism, always

A loop is not a slow sequential grind. Wherever there is no data dependency, fan the work out:
- **Fan-out-and-judge** runs its N attempts concurrently, then a judge picks or synthesizes (the parallel-barrier pattern).
- A checkpoint over many items (N review lenses, the slices in a wave, N scenarios) runs them in parallel, not one at a time.
- Flows nest: a round may itself fan out sub-agents, each in its own clean context, and those may fan out again. Dynamic fan-out (scale the width to the work) is encouraged.
- Always **adversarially verify** a fanned-out result before trusting it; parallel speed never buys a skipped check.

Wall-clock should approach the slowest single path, not the sum of all paths. See [references/orchestration.md](references/orchestration.md) for the fan-out, parallel-barrier, pipeline, and judge-panel patterns.

## Policy

Loops take time; depth is a deliberate trade the operator makes, more rigor for more rounds. An organization MAY set loop defaults per checkpoint and per domain in managed config (for example, a minimum review depth for regulated changes); a project can tighten, never loosen.
