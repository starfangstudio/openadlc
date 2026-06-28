<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# The Agentic Development Lifecycle

> Status: draft proposal, pre-ratification. Home: openadlc.com.

**The Agentic Development Lifecycle (ADLC) is the operating discipline for building software with AI agents: a repeatable lifecycle with a human kept in control at its checkpoints, a small set of non-negotiable laws, and an audit trail of every decision, so a team gets the speed of agents without giving up control, quality, or accountability.**

## The problem

Your engineers now have agents that write, run, and ship code in minutes. The tools arrived. The discipline did not.

So every developer improvises. One lets the agent push straight to main. One has it email a customer. One ships code nobody read because the agent sounded sure. Quality swings wildly from person to person, the agent takes irreversible actions nobody approved, and the knowledge that makes it all work goes stale and no one notices.

This is not an agent problem. The agents are good. It is the absence of a shared way to run them. A power tool with no operating procedure is how people get hurt.

## What ADLC says

ADLC is that operating procedure, written down and owned in the open. It holds to a few things:

- **The agent proposes; the human decides.** A person stays in control of the lifecycle at its checkpoints, plan approval, code review, and the consent checkpoint, and every decision is logged. The consent checkpoint, no outward action without an explicit yes, is a step the agent performs: before anything leaves the machine it stops, presents exactly what would go out, and proceeds only on a human yes.
- **A lifecycle, not vibes.** Explore, plan, implement, verify, review, consent, release. Each step has an input and a result you can point to.
- **Done means proven, not claimed.** A change is finished when a check passes, not when the agent says it works.
- **Clear or it does not ship.** If a human cannot understand it at a glance, it is not ready, however correct it is.
- **Current or it is a liability.** Guidance that is not kept up to date is worse than none, because people trust it.
- **The lifecycle outlives the tool.** ADLC is the contract. Your agent is just one implementation of it.

## What it is, and is not

ADLC is a standard, not a product. It does not care which agent you run, which language you write, or which project board you use. It sits underneath all of that and asks one thing: that building software with agents stays deliberate, provable, and in human hands.

It is small on purpose. The core is a [lifecycle](spec.md), seven [principles](principles.md), and a human kept in the loop, and that is all you need to start. The [spec](spec.md) adds the parts that let the discipline travel between teams and tools. You can read the whole thing in a sitting and start today.

## The invitation

If you build software with agents, you already have an agentic development lifecycle. The only question is whether it is one you chose, wrote down, and can defend, or one that emerged by accident, one shortcut at a time.

ADLC is the one you choose on purpose. Read the [principles](principles.md), read the [spec](spec.md), and [adopt it](adoption.md).
