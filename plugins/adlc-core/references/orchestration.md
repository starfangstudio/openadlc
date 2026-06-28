<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
# Parallelism Doctrine

Consumed by the ADLC lifecycle skills (load-context, create-plan, review-change, implement-change) and the planning agents.

**One-line rule: parallelize independent work; stay sequential only for a real data dependency.**

---

## Primitives

| Primitive | What it does |
|---|---|
| Workflow tool | Deterministic fan-out / pipeline of subagents; each step is declared, not improvised. |
| Background agents | `run_in_background`; caller is notified on completion; use when a long task must not block the main thread. |
| Batched tool calls | Issue all independent tool calls in one message turn; the runtime executes them concurrently. |
| Git worktree isolation | `git worktree add`; each parallel file-editing agent owns a separate working tree; no checkout conflicts. |
| `/loop` | Self-paced iteration inside a single agent; useful for unknown-size discovery where the agent decides when to stop. |

---

## Patterns

### Fan-out
Spawn N agents concurrently on N independent tasks. Reach for this when tasks share no mutable state and no output feeds another's input.

### Pipeline
Multi-stage work where stage K+1 starts as soon as its slice from stage K is ready, with no global barrier. Reach for this when throughput matters more than latency-to-first-result.

### Parallel-barrier
Fan out, then collect ALL results before proceeding (e.g., dedup across agents, merge summaries). Reach for this when the downstream step requires the full corpus.

### Loop-until-dry
One agent (or the `/loop` primitive) keeps searching or processing until K consecutive rounds return nothing new. Reach for this for open-ended discovery where the total size is unknown up front.

### Adversarial-verify panel
N skeptic agents each try to REFUTE a specific finding independently; kill the finding if a majority refute it. Reach for this before committing to any conclusion that would be expensive to reverse.

### Judge-panel
N agents each produce an independent solution; a judge agent scores and synthesizes the winner. Reach for this when there is no single obviously correct approach and the cost of a wrong pick is high.

### Multi-modal sweep
Each agent searches a different corpus or uses a different tool (code search, docs, web, logs). Reach for this when a single search method leaves blind spots.

### Completeness-critic
A final dedicated agent asks "what is missing?" against the accumulated output. Reach for this at the end of any fan-out whose results will be presented directly to the operator.

---

## Decision rule

```
shared mutable state OR output-feeds-input?  ->  sequential
parallel file edits on overlapping paths?    ->  git worktree per agent
otherwise                                    ->  parallelize
```

When in doubt: can agent B start before agent A finishes without reading A's output? If yes, run them together.

---

## Quality guard (load-bearing)

Always adversarially verify fanned-out output before trusting it. A fast-but-wrong fan-out is not faster; it creates rework that costs more than the parallelism saved.

Dedup before expensive downstream stages. Running a judge-panel on 40 near-duplicate candidates wastes budget; collapse first.

Prefer adversarial-verify panel over a single self-review. Self-review misses what the author's mental model already assumed away.

---

## Consent invariant

Every fanned-out agent still stops and asks the operator for an explicit yes before any outbound action. Fan-out NEVER bypasses that. Parallelism is a scheduling choice, not a permission escalation.

---

## Measure habit

Record wall-clock as: **waves x slowest-slice-per-wave** vs the sequential sum. The speedup is a number, not "faster". Log it so the next plan can calibrate.

Example row in a plan or session note:

```
Parallelism: 3 waves; slowest slice 12 s; sequential estimate 47 s; actual 38 s; speedup 1.2x
```

If the speedup is under 1.1x, the fan-out overhead was not worth it; note why for future planning.

---

## Model and effort routing

**Default: Opus + high effort** for any task that reasons, plans, implements, summarizes, or judges. This covers orchestration planning, solution design, code generation, review, synthesis, and any judge-panel role.

A model or effort downshift is allowed ONLY when BOTH conditions hold:
1. The work is provably mechanical and deterministic (pure format conversion, scaffold generation, string replacement, line counting, trivial renaming).
2. Quality is proven identical via an A/B comparison on representative inputs before the downshift is adopted.

**Effort right-sizing on the same model** (low effort for mechanical stages, high effort for reasoning stages) is the safe speed knob. Never lower effort on a reasoning task.

Never Haiku for engineering work, including any subagent that reasons, implements, or summarizes. Haiku is permitted only for a true zero-judgment reference-card readout (a fixed lookup, a line-count or lint gate, scaffolding from a frozen template) where a wrong answer is structurally impossible, not merely unlikely.

A downgrade that costs quality is a regression, not a gain. Speed wins only when quality is held constant.

### Reference models by family alias, never a pinned version

Always select a model by FAMILY ALIAS: `opus`, `sonnet`, `haiku`, `fable`. Never write a pinned version id (e.g. `claude-opus-4-8`) in agent frontmatter, a Workflow `agent({model})` call, or this doctrine. Aliases auto-resolve to the latest version of their family, so a model upgrade (Opus 4.8 to 4.9, Sonnet 4.6 to 4.7) is adopted with zero edits; a pinned id silently rots.

### Concrete routing (today's corpus)

| Role | Model + effort |
|---|---|
| Plan / implement / architect / review-judgment / security / summarize-for-a-human | Opus, high (the spine stays here) |
| Code reviewers + test-critic | Opus, high (review is judgment; Sonnet drops blocking-finding recall) |
| Visual + creative design (design-critic, visual-craft, UX) | **Fable** when available (the design-native model); Fable is currently unavailable, so fall back to **Opus** until it returns |
| Standard structured authoring with a clear contract | Sonnet, medium |
| Provably-mechanical readouts (build-command refs, commit-linker, PR plumbing, vault-maintenance, swiftui-preview, taxonomy lookups) | Sonnet, low |
