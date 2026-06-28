---
name: gate-skill-efficacy
description: "This skill should be used when the user asks to \"measure a skill\", \"test my skill\", \"is this skill any better than no skill\", \"eval a skill\", \"write evals for a skill\", \"does this skill actually work\", \"benchmark a skill\", \"skill efficacy\", \"skill regression check\", or before shipping/merging a new or edited SKILL.md. Runs a pass/fail efficacy gate over a skill's own evals using three layers, static checks, LLM-as-judge on outputs, and reliability (variance vs a no-skill baseline)."
version: 0.1.0
---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# Gate: Skill Efficacy

A pass/fail gate that answers one question about a skill: **does it reliably produce
better outputs than not using it, across varied prompts, including edge cases?** Until
this gate passes, a new or edited skill is not ready to ship.

Three layers, each cheaper-to-falsify than the last:

| Layer | What it checks | How |
|---|---|---|
| **1. Static** | Skill is well-formed and won't silently no-op | Lint frontmatter, body, structure |
| **2. LLM-judge** | Outputs are correct and better than baseline | Assertion grading + blind comparison |
| **3. Reliability** | The win holds across reruns, not by luck | Variance (stddev) over repeated runs |

## When to use

- A new `SKILL.md` exists and the next step is merging/shipping it.
- An existing skill was edited and you need a regression check vs the prior version.
- A skill is suspected of adding cost (tokens/time) without adding value.

Skip only for a trivial copy/typo edit that cannot change behavior. When in doubt, run the gate.

## Inputs (stop and ask if missing)

- **Skill path**: the directory containing `SKILL.md`.
- **Evals**: look at `.claude/evals/<skill>.json` and `<skill-dir>/evals/evals.json`; use
  whichever exists. If neither is present, the gate **cannot pass**: STOP and offer to scaffold evals.
- **Baseline**: for a new skill, the baseline is no skill. For an edit, snapshot the prior
  version first: `cp -r <skill-path> <workspace>/skill-snapshot/`

## Procedure

### Layer 1: Static

Judge each item `pass` / `fail` from the files on disk (treat `unknown` as `fail`).
Any FAIL blocks the gate; fix before measuring outputs.

- [ ] **Frontmatter**: `name` + `description` present; `description` is third-person with concrete trigger phrases.
- [ ] **Body discipline**: imperative voice, under ~500 lines; detail beyond ~150 lines lives in a linked `references/` file.
- [ ] **Structure**: every referenced `scripts/`, `references/`, and asset path resolves.
- [ ] **Evals present**: >= 3 cases, varied phrasing, >= 1 edge/boundary case; each has a prompt + expected output.
- [ ] **No outbound side effects**: the body never pushes/posts/sends/publishes without the operator's explicit yes first.

### Layer 2: LLM-judge

Run from **clean context** (fresh subagent or separate session) so the agent follows only the skill.
For each eval case:

1. Run **with-skill** and save output + `timing.json` (`{total_tokens, duration_ms}`).
2. Run **baseline** (no skill, same prompt) and save output + timing.
3. Grade assertions: each must have quoted evidence; a heading without substance is a FAIL.
4. Run a **blind comparison**: give the judge both outputs without labels; score holistic quality.
   Blinding cuts position bias. See grading schema and bias rules in the detail reference.

### Layer 3: Reliability

Rerun each eval N times (default N=3; edge cases N >= 5). Aggregate into `benchmark.json`:

```json
{ "with_skill":    { "pass_rate": {"mean":0.83,"stddev":0.06}, "tokens": {"mean":3800,"stddev":400} },
  "without_skill": { "pass_rate": {"mean":0.33,"stddev":0.10}, "tokens": {"mean":2100,"stddev":300} },
  "delta": { "pass_rate": 0.50, "tokens": 1700 } }
```

High stddev means flaky: tighten the skill or eval before passing. Single-run results
must be marked reliability `unknown`, which fails the gate.

## Verdict rule

- **EFFECTIVE**: Layer 1 all `pass`; with-skill pass-rate strictly beats baseline (including
  edge case); stddev <= 0.15; token cost is justified by the lift.
- **NOT EFFECTIVE**: any static FAIL, no measured improvement, edge case fails, high variance,
  or cost not worth the lift. List every blocking reason.

No partial pass. Do not drop assertions or the edge case to force a pass; fix the skill.

## Report format

Emit this exactly:

```
## Skill Efficacy Gate: <skill-name>

Verdict: EFFECTIVE   |  NOT EFFECTIVE

Layer 1, Static:
- Frontmatter ......... pass / fail
- Body discipline ..... pass / fail
- Structure ........... pass / fail
- Evals present ....... pass / fail
- No side effects ..... pass / fail

Layer 2, LLM-judge (n=<cases>):
- with-skill pass-rate ... <x>   baseline ... <y>   delta ... <+/->
- Edge case .............. pass / fail
- Blind comparison ....... with-skill / baseline / tie

Layer 3, Reliability (N=<runs>):
- with-skill pass-rate ... mean <m> stddev <s>
- cost delta ............. tokens <+/->  time <+/->s

Blocking reasons (only if NOT EFFECTIVE):
- <reason>: <the one concrete change to the skill or evals that fixes it>

Next step: <"Ship the skill." | "Return to skill-creator: <fix>." | "Add evals/runs and re-measure.">
```

## Outbound checkpoint

Local work needs no approval. Anything outbound (publish, push, post) is a lifecycle checkpoint: present exactly what would go out and get the operator's explicit per-action "yes" first; see the global consent law.

## References

- Anthropic skill-creation docs, "Evaluating skill output quality", canonical eval-driven
  loop: `evals/evals.json`, with-skill vs without-skill baseline, assertion grading with
  evidence, blind LLM-judge comparison, `benchmark.json` mean/stddev, iteration loop.
  https://agentskills.io/skill-creation/evaluating-skills
- Anthropic `skill-creator` Skill: automates running evals, grading, and aggregating:
  https://github.com/anthropics/skills/tree/main/skills/skill-creator
- wshobson/agents `llm-evaluation` Skill, the three-layer framing (static / LLM-as-judge /
  reliability) and bias mitigation for LLM judges:
  https://agentskills.so/skills/wshobson-agents-llm-evaluation
- Detail reference (full grading schema, bias rules, calibration guidance, interpretation rules):
  [references/gate-skill-efficacy-detail.md](references/gate-skill-efficacy-detail.md)
