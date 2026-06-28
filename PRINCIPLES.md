<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
# Principles

The rules we hold OpenADLC to. A change that breaks one needs a very good reason, written down.

1. **Human-in-the-loop at every consequential step.** Intake, plan, implement, review. One command per human decision point. No step that ships work skips the human silently. Intake is the universal front door for any role (dev, manager, tech owner, product owner, QA), not a PM-only step.

2. **Outbound is a human decision, not a default.** Reading and local work (edits, local commits, builds, tests) flow freely. Anything that leaves the machine, a push, a PR, a posted comment, a deploy, a publish, is a deliberate choice the operator makes, never an implied or standing approval. The lifecycle carries this: the command at the boundary stops, shows exactly what would leave, and waits for an explicit yes before it goes. Approval happens where the action happens, so the person owning the release sees what they are releasing.

3. **The checkpoint is a decision, not a sandbox.** The human approval at each outbound boundary is a deliberate gate on intent, not a security perimeter. The OS sandbox and the harness's own permissions are the real boundary. We never claim "unbypassable." A false sense of safety is worse than none.

4. **Mechanism over prose.** Anything that must happen every time (logging, checkpoints, doc currency) is wired to a command step, a check, or a test, not an instruction.

5. **Fail closed.** A control that cannot tell whether it is working reports failure, not success. The eval runner is red on a missing check or a skipped case.

6. **Open standards, no lock-in.** Content is Agent Skills, tools are MCP, per-repo context is AGENTS.md. Your discipline runs on the harness you already use.

7. **Tighten across a boundary, never loosen.** A project may relax discipline locally. An org may pin it. A project can never loosen what a managed policy set.

8. **Honest engineering.** No AI-generated timelines, effort, or cost estimates. No claimed track record. Published facts with a source, or nothing.

9. **Docs ship with the code.** A change to a command, skill, hook, or config updates its docs in the same change. Stale docs are a bug.

10. **Small and legible.** Every artifact is simple to read at a glance. Prefer deleting lines over adding them. If a human cannot get it quickly, simplify until they can.

11. **Parallel by default, mindful of cost.** Wherever there is no data dependency, fan the work out (discovery, slices, review lenses, loop attempts) so wall-clock is the slowest path, not the sum. And spend tokens like they are scarce: capped loops, a fast route to every screen, heavy reads in subagents. Fast, high-quality, and cheap is the bar.
