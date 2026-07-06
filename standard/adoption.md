<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# Adopting ADLC

> Status: version 1.0.
> One line: what declaring "we follow ADLC" commits you to, by level, and the smallest first step to get there.

The [spec](spec.md) defines the standard. This is how you adopt it: what you are promising, the three levels you can promise it at, and the literal text you put in your repo to say so.

## What "we follow ADLC" commits you to

Declaring ADLC is a commitment, not a label. At minimum (Core) it means your team makes three promises, each tied to a spec requirement:

| You promise | Which means | Spec |
|---|---|---|
| **A human stays in control.** | A person decides at the lifecycle's checkpoints (plan approval, code review, the consent checkpoint), and every decision is logged. The plan and review checkpoints are yours to tune; the consent checkpoint always applies to the release decision, since that decision is always a human's. | [Human in the loop, section 4](spec.md) |
| **You run the lifecycle.** | Non-trivial changes move through explore, plan, implement, verify, review, consent, release, not straight from prompt to production. | [Lifecycle, section 2](spec.md) |
| **Done means proven.** | A change is finished when a check that can fail has passed, not when the agent says it works. | [Law L5](spec.md) |

If you do those three, you are Core-conformant. Everything else is building on top.

## The three levels

Adoption is a ladder, not a switch. Each level adds to the one below.

| Level | Who it is for | Adds on top |
|---|---|---|
| **Core** | A solo dev or any team | The lifecycle + the human-in-the-loop checkpoints you tune, *honored*, with a local audit trail. The consent checkpoint always applies to the release decision. The three promises above. |
| **Governed** | An organization | The org sets which checkpoints are mandatory and *enforces* them centrally across every seat, with a central audit trail that proves it happened. |
| **Certified** _(planned)_ | An organization buying trust | Everything in Governed, plus the packs you run are ADLC-certified and you carry the certification mark. Not yet operational. |

Why three and not one: a solo developer can be Core today with a habit and a local log; the checkpoints are theirs to tune, the consent checkpoint stays on the release decision, and for an individual it is free. An organization cannot trust 200 people to each keep the right checkpoints on, so the value it adds is to *enforce* the chosen checkpoints centrally across every seat and *prove* it to a security lead. **That is what Governed adds: enforcing, org-wide, the checkpoints an individual could otherwise switch off, and producing the audit that proves it.** That central-enforcement layer is operational work any sufficiently-equipped team could build, not a power unique to one vendor; it is for the orgs that would rather buy it than build and run it. Certification is a further trust signal on top, where the packs themselves are vouched for.

Note the level and the price are separate axes. Levels (Core / Governed / Certified) say *how much of the discipline you enforce and prove*; the seat says *who is running the OpenADLC implementation*. The standard and the Core practice are open and free to anyone. The OpenADLC implementation is free for individuals and the public, but use by or on behalf of an organization needs a commercial seat at any level, including Core. See the [license notice](README.md#license).

- **Core** is the developer's promise to themselves (the practice is free and self-configured; an org running the OpenADLC implementation still needs seats).
- **Governed** is the organization enforcing and proving the promise across everyone.
- **Certified** (planned) is a third party's promise to a buyer.

## The conformance statement

To declare adoption, put this in your repo (a `ADLC.md` or a README section). Keep the line for your level; delete the rest.

```
We follow ADLC (the Agentic Development Lifecycle). https://openadlc.com

Level: Core
- A human stays in control at the lifecycle's checkpoints; every decision is logged.
- Changes move through the ADLC lifecycle.
- "Done" requires a passing, failable check.
- The consent checkpoint always applies: the agent stops and asks before any outward action.
```

For Governed, add the matching lines:

```
Level: Governed
- The checkpoints (including the consent checkpoint) are enforced centrally, not just honored.
- Checkpoint, pack, and rule policy is set centrally across all seats.
- The audit trail is centrally kept and provable.
```

What each badge asserts:
- **ADLC Core** asserts a practice: this team runs the loop with a human in it and logs the decisions.
- **ADLC Governed** asserts a control: the checkpoints are mechanically enforced org-wide and the trail is provable.

A badge you cannot back is a false claim. Only state the level you actually meet. Until the certification program ships, the highest level you can truthfully claim is Governed.

**Certified is planned, not yet operational.** It will assert a vouched supply chain: that the packs you run have themselves passed ADLC certification, carrying a published mark. What gets tested and who issues the mark are being defined in the certification program. It is named here so the ladder is complete, not because you can reach it today.

## What ADLC does NOT require

ADLC is a discipline, not lock-in. It does not ask you to:

- **Use a specific agent or vendor.** Claude Code, Codex, Copilot, or anything else: all fine. ADLC sits above the tool.
- **Use a specific language, framework, or cloud.** It is written against capabilities, not a stack.
- **Adopt a project-management method.** It is not Scrum, Kanban, or any of them. It sits *underneath* whatever you already use.
- **Adopt any particular tooling for the checkpoints.** The consent checkpoint is a step the agent performs, not a product you install: before any outward action it stops, shows what would leave, and waits for your yes. How you keep that human in the loop is yours to choose; what is required is that the human stays in control and the decisions are logged.
- **Buy anything to follow the standard.** The ADLC standard is open (CC-BY-4.0) and free for anyone to read and implement; the checkpoints are part of it. Adopting Core as a practice costs nothing. What is paid is the OpenADLC *implementation* when an organization uses it: the source stays publicly viewable and free for individuals and the public, always, but use by or on behalf of an organization needs a commercial seat. Governed and Certified build on that for org-wide enforcement and proof. You can be Core-conformant with any tooling, including your own, and owe nothing.
- **Boil the ocean.** Core is two things: a loop and a human in it. You can adopt it this afternoon.

If a rule felt like lock-in, it would violate Principle 7 (vendor neutrality) and would not be in the standard.

## The smallest first step

Do one thing today: **keep yourself in the loop.** The simplest, strongest way is the consent checkpoint: have your agent stop before it pushes, deploys, comments, or sends anything outward, show you exactly what would leave, and proceed only on your explicit yes. That is the release checkpoint and the whole point of ADLC in one move: a human stays in control of what leaves the machine.

Then run the lifecycle loop for your next real change, decide at its checkpoints, log those decisions, and add a failable check before you call it done. That is Core. You are following ADLC.

When you are ready to make it an organizational control rather than a personal habit, move to Governed: the org enforces the chosen checkpoints across every seat and keeps a central audit trail that proves it. Certification comes after, when you want the packs themselves vouched for.

Start at [the spec](spec.md). Read the [principles](principles.md). Then declare your level and begin.
