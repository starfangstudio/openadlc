<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# ADLC on one page

> Status: draft proposal, pre-ratification. The full standard: [manifesto](manifesto.md) · [principles](principles.md) · [spec](spec.md) · [adoption](adoption.md). Home: openadlc.com.

**The Agentic Development Lifecycle (ADLC) is the operating discipline for building software with AI agents: a lifecycle, seven principles, and a human kept in control of it, so you get the speed of agents without giving up control, quality, or accountability.** It is vendor-neutral: your agent (Claude Code, Codex, Copilot, anything) is one implementation of it.

## The problem

The tools arrived. The discipline did not. So every developer improvises, agents take irreversible actions nobody approved, quality swings, and the guidance goes stale. ADLC is the discipline, written down.

## Human in the loop (the centerpiece)

A person stays in control of the lifecycle through its **checkpoints**, and every decision is logged (the audit trail):

- **Plan approval** - a human okays the approach before code is written.
- **Code review** - a human okays the change before it ships.
- **Consent checkpoint** - a human okays what goes outward: before any outward or irreversible action the agent stops, presents exactly what would leave the machine, and proceeds only on an explicit yes. It is a step in the lifecycle the agent performs, intrinsic to it, since the release decision is always a human's.

Which checkpoints you enforce is your call. Enforcing them across a whole team and proving it is what the paid org tier adds, an operational layer, not a power only we have.

## The seven principles

1. **Human in the loop** - a person stays in control at the lifecycle's checkpoints; the release decision is always theirs, taken at the consent checkpoint.
2. **Simplicity** - every artifact is graspable at a glance, or it is not ready.
3. **Currency** - guidance that is not kept current is a liability, not an asset.
4. **Local first** - work is local by default; going outward is a deliberate, visible act, never a silent default.
5. **Evidence over assertion** - done means a failable check passed, not the agent said so.
6. **Ask, do not improvise** - at a fork, stop and ask with options; never invent scope.
7. **Vendor neutrality** - the lifecycle is the contract; the tool is just an implementation.

## The seven phases

**Explore** (read-only) -> **Plan** (approve the approach) -> **Implement** (small steps) -> **Verify** (a check that can fail) -> **Review** (fresh eyes) -> **Consent** (the human approves what goes out) -> **Release** (it ships, and the approval is logged).

Trivial work collapses steps. What it never skips is keeping a human in control.

## The three adoption levels

- **Core** - you run the lifecycle and keep a human at the checkpoints, with a local log. The consent checkpoint always applies to the release decision; the plan and review checkpoints are yours to tune. Free; a solo dev can do this today.
- **Governed** - the org enforces the chosen checkpoints across every seat and keeps a central audit trail that proves it. The paid org tier: enforcing fleet-wide the checkpoints an individual could otherwise skip.
- **Certified** (planned) - the packs you run are ADLC-certified and carry the mark.

## Start today

Keep a human at the checkpoints. Run the lifecycle on your next change and decide at its checkpoints, add a failable check before you call it done, and log the decisions. The consent checkpoint is the one that is always on: before your agent pushes, deploys, comments, or sends anything outward, it stops, shows you exactly what would leave, and waits for your explicit yes. That is Core. You are following ADLC.

Read the [spec](spec.md). [Declare your level](adoption.md). Build with agents on purpose.
