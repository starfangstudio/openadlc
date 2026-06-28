<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# ADLC Principles

> Status: draft proposal, pre-ratification.
> One line: the seven non-negotiables every ADLC rule traces back to. If a rule does not serve one of these, it does not belong in the standard.

The [manifesto](manifesto.md) says why ADLC exists. These are the values underneath it. The [spec](spec.md) turns each one into a checkable rule. Read these seven and you know what ADLC stands for, before any procedure.

Each principle is one assertion, one reason, and one consequence. Nothing here depends on which agent you run.

---

## 1. Human in the loop

**A human stays in control of the agentic lifecycle, through its checkpoints, the loop, and an audit trail of every decision.**

Why: an agent acts. It writes, runs, and ships. Hand it the whole lifecycle with no human decision points and you have handed over control of your software. The discipline is not to slow the agent down everywhere; it is to keep a human deciding at the moments that matter, and to record those decisions.

Requires: the lifecycle has human checkpoints, at plan approval, at code review, and at the outward boundary (the consent checkpoint), and every human decision is logged. The plan-approval and code-review checkpoints are strong defaults a project tunes to its risk; the consent checkpoint always applies, since the release decision is always a human's. What is not optional is that a human stays in control and that the decisions are recorded.

The release checkpoint is the **consent checkpoint**: no outward or irreversible action without an explicit human yes. It is a step the agent performs, not a hook or a setting: before each outward action the agent stops, presents exactly what would leave the machine, and proceeds only on an explicit yes. It is intrinsic to the lifecycle and free to a solo dev. Enforcing it, and the other checkpoints, centrally across a team is what an organization adds on top (see [adoption](adoption.md)). This is the load-bearing principle: everything else can bend; a human staying in control does not.

## 2. Simplicity

**Every artifact must be understandable by a human at a glance.**

Why: agents generate volume cheaply. Volume nobody can read is a liability, not an asset. The harder the topic, the more the artifact has to do the work of making it clear.

Requires: lead with the summary, use plain names, keep files short, cut what does not earn its place. If a person cannot look at it and get it, simplify until they can. "It is technically correct" is not the bar; "a human gets it" is.

## 3. Currency

**A golden path is only trustworthy if it is kept current.**

Why: models, tools, and SDKs change monthly. Guidance that was right last quarter quietly becomes wrong. Stale guidance followed with confidence is more dangerous than no guidance at all.

Requires: every reusable pack or rule has an owner and a freshness date. Out-of-date guidance is flagged and fixed or retired, not left to rot. Keeping it current is ongoing work, not a one-time setup: the moment you stop, the guidance starts lying.

## 4. Local first

**Work happens on the developer's machine by default; going outward is a deliberate, gated act.**

Why: if the default posture is local, the only thing left to control is the boundary, and the boundary is where the outward checkpoint sits (the consent checkpoint, the release checkpoint). An agent that needs the network to do ordinary work is an agent you cannot fully govern.

Requires: investigate, plan, build, and verify locally first. Reaching the network or a third party is opt-in and visible, never the silent default. This is what makes the outward checkpoint meaningful instead of theoretical.

## 5. Evidence over assertion

**Nothing is "done" on a claim; it is done when a check passes.**

Why: agents are fluent and confident even when wrong. Fluency is not correctness. The only thing that settles whether a change works is a check that can fail.

Requires: every change is verified by something that passes or fails (a test, a build, an observed result), and the agent shows the proof. "It should work" is not done. "Here is the passing check" is.

## 6. Ask, do not improvise

**At any fork, missing input, or ambiguity, the agent stops and asks, with options and a recommendation.**

Why: a confident guess at a fork compounds into wasted work and silent scope creep. The human steers; the agent executes. Inventing requirements is how agentic speed turns into agentic mess.

Requires: when the path is unclear, surface the choice instead of picking one quietly. Offer the options, recommend one, and wait. Never expand scope on the agent's own initiative.

## 7. Vendor neutrality

**The lifecycle is the contract; any agent is just an implementation.**

Why: the tools move fast and the market has several. A discipline tied to one vendor's features dies when that vendor changes them. ADLC has to outlive whatever agent you run today.

Requires: the standard is written against capabilities, not products. Claude Code, Codex, and Copilot are implementations of ADLC, not the definition of it. If a rule only makes sense for one tool, it belongs in that tool's adapter, not in the standard.

---

## How the seven hold together

One sentence: **the human stays in control (1, 6), the work stays local and provable (4, 5), the artifacts stay clear and current (2, 3), and none of it is chained to a single vendor (7).** Take any rule in the [spec](spec.md) and it traces back to one of these. If it does not, it is not part of ADLC.
