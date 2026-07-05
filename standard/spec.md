<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# The ADLC Specification

> Status: draft proposal, pre-ratification. Version: 0.1 (draft).
> One line: the normative, vendor-neutral definition of the Agentic Development Lifecycle. The [manifesto](manifesto.md) is the why; this is the what.

This document defines what it means to follow ADLC. It is written against capabilities, not products: any agent or tool that implements the rules below is an ADLC implementation. The [principles](principles.md) are the values; every rule here traces to one of them.

**Normative keywords.** The key words MUST, MUST NOT, REQUIRED, SHALL, SHALL NOT, SHOULD, SHOULD NOT, RECOMMENDED, NOT RECOMMENDED, MAY, and OPTIONAL in this document are to be interpreted as described in BCP 14 ([RFC 2119], [RFC 8174]) when, and only when, they appear in all capitals, as shown here. In plain terms: MUST is a hard requirement for conformance; SHOULD is a strong default you may override with a stated reason; MAY is optional. Lowercase uses of these words carry their ordinary English meaning. (Of the full keyword list, only MUST, SHOULD, and MAY are exercised in this spec.)

**How to read this spec.** Sections 2 to 4 are the core: the lifecycle, the laws, and human-in-the-loop (the checkpoints, the consent checkpoint, the audit trail). That is what a developer does day to day, and it is all you need to be Core-conformant. Sections 5 to 7 are the portability layer: how guidance is packaged (packs), kept honest (artifacts), and carried across tools (adapters). They matter when you share guidance or govern a team, not on your first change. Section 8 is conformance. If you only read three sections, read 2, 3, and 4.

---

## 1. Definitions

| Term | Meaning |
|---|---|
| **Agent** | An AI system that can take actions (run commands, edit files, call tools), not just emit text. |
| **Harness** | The tool that runs an agent: its loop, its permissions, its plugin and hook system. Claude Code, Codex, and Copilot are harnesses. |
| **Operator** | The human responsible for the work. The operator gives intent and holds approval authority. |
| **The boundary** | The line between the local machine and everything outside it (the network, third parties, other people). |
| **Outward action** | Any action that crosses the boundary or cannot be undone: push, pull request, comment, message, email, API write, deploy, publish, release. |
| **Checkpoint** | A point in the lifecycle where a human decides whether the agent proceeds. ADLC defines three: plan approval, code review, and the consent checkpoint. See section 4. |
| **Human in the loop** | The human stays in control of the lifecycle through its checkpoints, the loop, and the audit trail. The non-negotiable principle (Law L1). |
| **The consent checkpoint** | The release checkpoint: a stop before each outward action where the agent presents what would leave the machine and waits for an explicit human yes. Intrinsic to the lifecycle, free to a solo dev. See section 4. |
| **Audit trail** | The record of every human decision at a checkpoint (what, when, who, approve or reject). See section 6. |
| **Pack** | A versioned, portable bundle of agentic guidance (skills, agents, rules, references) plus its evals and capability declaration. See section 5. |
| **Artifact** | A named written output of a lifecycle phase (a plan, a review report, a consent record). See section 6. |
| **Adapter** | The thin mapping that implements this standard on a specific harness. See section 7. |
| **Conformant** | Meets the MUST requirements of this spec for its kind (team, pack, or harness). See section 8. |

---

## 2. The lifecycle

ADLC defines seven phases. An ADLC team's work MUST move through them in order for any change that produces an outward action. Trivial or read-only work MAY collapse phases, but a human MUST own the decision to go outward (the Consent phase).

Each phase has an input and produces an artifact (section 6). Three of the phases are the **human checkpoints** where a person stays in control (section 4): **Plan** (plan approval), **Review** (code review), and **Consent** (the consent checkpoint).

| # | Phase | Purpose | Input | Produces |
|---|---|---|---|---|
| 1 | **Explore** | Understand before changing. The universal front door for any role. Read-only. | An intent or task | Typed intake fuel (story / bug / epic / tech-debt / intent) |
| 2 | **Plan** | Decide the approach before building. | Typed intake fuel | Approved plan |
| 3 | **Implement** | Make the change in small, reviewable steps. | Approved plan | The change + its tests |
| 4 | **Verify** | Prove it works with a check that can fail. | The change | Verification evidence |
| 5 | **Review** | Inspect the change with fresh, independent judgment. | Verified change | Review report |
| 6 | **Consent** | A human decides whether to release. The consent checkpoint is where the agent presents what would leave and waits for that decision. | Reviewed change + a report of what would leave | Consent record |
| 7 | **Release** | The approved change crosses the boundary. | A consent record | Released artifact + logged decision |

Rules:
- Explore MUST be read-only. It MUST NOT change files or take outward actions. It is the universal front door open to any role (developer, manager, tech owner, product owner, QA), not a product-only surface. Its output SHOULD be typed intake fuel, classified as a story, bug, epic, tech-debt, or intent rather than left untyped, and SHOULD surface the development dependencies it finds so a later phase can carry them.
- Plan output SHOULD be written and approved before Implement begins.
- Verify MUST produce evidence that can fail (see Law L5). A change with no failable check is not verified.
- Review SHOULD be performed by a different context than the one that wrote the change (a fresh agent, a different agent, or a human).
- A human MUST own the release decision (the Consent phase). The consent checkpoint is how that decision is taken: before each outward action the agent presents what would leave and the operator gives an explicit yes (section 4).

### The lifecycle in one example

A one-line bug fix, run through all seven phases:

1. **Explore:** the agent reads the failing code and the test, and reports what it found.
2. **Plan:** it proposes a one-line fix and how it will prove the fix works.
3. **Implement:** it makes the change.
4. **Verify:** it runs the test, the test passes, and it shows you the output.
5. **Review:** a fresh agent (or you) checks the diff for anything the first pass missed.
6. **Consent:** it shows you the diff and asks before pushing. You say yes.
7. **Release:** it pushes, and records that you approved it.

Trivial work collapses steps. The one step it never skips is 6.

---

## 3. The laws

The laws are the always-on rules that hold across every phase. They are the [principles](principles.md) stated normatively. Law N is Principle N, written as a rule.

- **L1. Human in the loop.** A human MUST stay in control of the lifecycle through its checkpoints (plan approval, code review, the consent checkpoint), and every human decision MUST be recorded in the audit trail. The release decision is always a human's; the consent checkpoint is the step where the agent stops and asks for it. (Specified in section 4.)
- **L2. Simplicity.** Every artifact MUST be understandable by a human at a glance; when it is not, it MUST be simplified before it is used or shipped.
- **L3. Currency.** Every pack and rule MUST declare an owner and a freshness expectation, and out-of-date guidance MUST be flagged and fixed or retired.
- **L4. Locality.** Work MUST default to the local machine; reaching the network or a third party MUST be a deliberate, visible act, never a silent default.
- **L5. Evidence.** A change MUST NOT be called done until a check that can fail has passed, and the evidence MUST be shown.
- **L6. Ask.** At a fork, missing input, or ambiguity, an agent MUST stop and ask with options rather than invent scope.
- **L7. Neutrality.** This standard MUST NOT require any specific vendor, model, language, or framework. Tool-specific rules belong in an adapter, not here.

---

## 4. Human in the loop

Keeping a human in control of the lifecycle is the central MUST of ADLC (Law L1). It is realized through three things: the **checkpoints**, the **audit trail**, and, as the release checkpoint, the **consent checkpoint**.

### The three checkpoints

A checkpoint is a point in the lifecycle where a human decides whether the agent proceeds. They map to three phases:

| Checkpoint | Phase | The human decides |
|---|---|---|
| **Plan approval** | Plan | whether the approach is right before any code is written |
| **Code review** | Review | whether the change is safe and correct before it ships |
| **Consent checkpoint** | Consent | whether what would go outward is allowed to leave |

A conformant team MUST keep a human in the loop through these checkpoints and MUST record each decision (the audit trail). The plan-approval and code-review checkpoints are strong defaults a project MAY adjust to its risk. The consent checkpoint is different: the release decision is always a human's, so the agent always stops and asks before an outward action. That is intrinsic to the lifecycle, free to a solo dev, not a setting to turn off.

### The consent checkpoint (the release checkpoint)

The consent checkpoint is a step the agent performs, and it behaves precisely, so it is checkable:

**The rule:** an agent MUST obtain explicit operator approval immediately before each outward action, and MUST present, before asking, exactly what will go out.

**What counts as an outward action** (non-exhaustive; an implementation MUST stop and ask for at least these):
- Pushing commits; opening or updating a pull request; merging.
- Any comment, review, message, or email to another person or system.
- Any network write: API POST / PUT / DELETE, MCP or tool write actions.
- Any release, deploy, publish, or package upload.

**What "explicit approval" means:**
- It MUST be per-action. Approval of one outward action MUST NOT imply approval of the next.
- It MUST follow a clear presentation of what would leave (the diff, the recipient, the destination, the payload).
- It MUST NOT be standing or implied.

**What is never stopped (so the checkpoint stays meaningful):**
- Reading: local files, the web, read-only queries.
- Editing local files; local commits with no push.
- Local builds and tests.
- Talking to the operator.

### Honoring, enforcing, and who does which

A checkpoint is *honored* when the agent is instructed to stop for the human, and *enforced* when a mechanism makes the stop unskippable regardless of the agent's choice.

- A **solo dev** honors their own checkpoints, locally and for free. They tune the plan and review checkpoints to their risk; the consent checkpoint is always present, since the release decision is always theirs.
- An **organization** sets a checkpoint policy and **enforces it centrally across every seat**, with a central audit trail that proves it happened. Enforcing the checkpoints an individual could otherwise skip, across many seats, and proving it to a third party, is the work an org takes on (see [adoption](adoption.md) levels). This is an operational layer on top of the free standard, not a special power: any sufficiently-equipped team could build it.
- For an **unattended or autonomous run**, a checkpoint MUST be enforced, not merely honored, because no human is present in the moment to decide.

See [conformance.md](conformance.md) for the checkable test that tells honored from enforced.

---

## 5. The pack format

A **pack** is the portable unit of agentic knowledge: a versioned bundle that teaches an agent to do a class of work to the ADLC bar. Packs are how the lifecycle and the golden paths travel between teams and tools.

A conformant pack MUST contain:

1. **(5.1) A manifest.** At minimum: name, version, a one-line description, an owner, the targeted ADLC spec version, and a declared capability set (see below). Version SHOULD follow Semantic Versioning.
2. **(5.2) At least one guidance unit**, of these kinds:
   - **Skill** - how to do a task: a trigger (when it applies) and a procedure.
   - **Agent** - a scoped role with a defined job and its own tool access.
   - **Rule** - a constraint, always-on or loaded on demand.
   - **Reference** - the deep detail a skill points to, kept out of the skill body (progressive disclosure: the common case runs from the skill; the detail is one hop away). **Citation form:** name a reference by its pack-relative `references/<file>.md`; the markdown link keeps that readable name as its text but points at a file-relative target that resolves from the citing file, e.g. from a skill `[references/<file>.md](../../references/<file>.md)`. The `../` depth adjusts to the citing file's place under the pack: `../../references/` from a skill, `../references/` from a command or agent, a bare `<file>.md` from a sibling reference. A reference owned by another pack is named in prose, e.g. the `references/<file>.md` reference in the **adlc-core** pack. A reference MUST NOT be cited with a harness-specific path variable such as `${CLAUDE_PLUGIN_ROOT}`: that resolves on only one of the deploy targets, so the agent names the file and locates it at runtime.

   In the manifest, units travel as per-kind integer counts (`skills`, `agents`, `commands`, `references`; see [pack-format.md](pack-format.md)): a command is a harness-invocable entry point into the lifecycle, and a rule is carried under `references`.
3. **(5.3) Evals.** Evidence the pack measurably beats a no-pack baseline (Law L5 applied to the pack itself). In the manifest, `evals` declares the bar the pack clears: `conformance` (the structural eval) or `conformance+gate` (also ships a behavioral eval). A pack with no evals MAY be shared as experimental but MUST NOT be called conformant.
4. **(5.4) A capability declaration.** What the pack can touch: shell execution, network, file writes outside the workspace. This declares the pack's blast radius so the checkpoints and reviewers know what it can do. Declared capabilities MUST match actual behavior. The concrete vocabulary is in [pack-format.md](pack-format.md).

A conformant pack MUST NOT weaken or bypass the human-in-the-loop checkpoints (including the consent checkpoint), and MUST NOT take undeclared capabilities.

The standard defines the **shape** (manifest + units + evals + capability declaration). It does not mandate a file layout or a vendor's plugin schema; the adapter (section 7) maps this shape onto a specific harness.

---

## 6. The artifacts

ADLC names the written outputs of the lifecycle so that work is traceable and resumable. Each is a phase's product (section 2).

| Artifact | From phase | What it is |
|---|---|---|
| **Intake fuel** | Explore | What the agent learned, typed as a story, bug, epic, tech-debt, or intent: a human-readable briefing plus classified-unit, discovery, and dependencies concepts, with acceptance criteria. |
| **Plan** | Plan | The approved approach: scope, steps, and what "done" means. |
| **Verification evidence** | Verify | The failable check and its passing result. |
| **Review report** | Review | An independent verdict: what is wrong, what is missing, what is safe. |
| **Consent record** | Consent | What was approved to go out, when, and by whom. |
| **Audit trail** | Cross-cutting | The running record of every human checkpoint decision (plan approval, review, consent): what, when, who, approve or reject. |
| **Decision record** | Cross-cutting | A durable record of a significant decision: the context, the choice, the alternatives, the consequences. |

Rules:
- An ADLC team MUST keep an audit trail: a record of each human decision at a checkpoint (plan approval, code review, consent). This is what makes human-in-the-loop provable to a third party; the consent record is the consent checkpoint's entry in it.
- A significant or hard-to-reverse decision SHOULD be captured in a Decision record.
- Other artifacts SHOULD be written for any non-trivial change so the work can be reviewed and resumed cold.
- Artifacts SHOULD be written as [OKF](https://github.com/GoogleCloudPlatform/knowledge-catalog/tree/main/okf) bundles: typed-markdown directories carrying a human-readable briefing plus typed machine-context concepts. OKF is itself an open format, so the SHOULD keeps Law L7 intact.

---

## 7. The harness adapter seam

This is the proof of vendor neutrality.

- The **standard** is the contract: the lifecycle (2), the laws (3), human-in-the-loop (4), the pack shape (5), the artifacts (6).
- A **harness** is any tool that runs an agent.
- An **adapter** is the thin layer that maps this standard onto one harness's primitives: its permission and hook system, its plugin loader, its config files.

A harness is ADLC-conformant when its adapter implements the MUST clauses of this spec. The load-bearing requirement is supporting the human-in-the-loop checkpoints: the adapter MUST be able to honor them (the consent checkpoint among them), and MUST be able to enforce a checkpoint for unattended or central use.

Harnesses differ in how well they can enforce. The standard does not paper over that. Where a harness cannot enforce a checkpoint in-tool, conformance MAY be achieved by an external control below the harness (for example an egress check or a server-side approval step). Either way, conformance is judged against this standard, never against a vendor's feature list.

This is what lets ADLC sit *above* Claude Code, Codex, and Copilot: each is one adapter away from the same standard, and none of them is the standard.

---

## 8. Conformance

"ADLC-conformant" is a checkable claim, and [conformance.md](conformance.md) is the test that checks it. Three kinds of thing can claim it.

**A team is conformant (Core) when it:**
- moves changes through the lifecycle (section 2), and
- keeps a human in the loop through the lifecycle's checkpoints and records each decision in the audit trail (section 4; the consent checkpoint always applies to the release decision, while the plan and review checkpoints are the team's to tune), and
- verifies changes with failable checks (Law L5).

"Core" here is the same Core that [adoption.md](adoption.md) defines as the first adoption level: team conformance and the Core level are one thing.

**A pack is conformant when it:**
- has a manifest, at least one guidance unit, evals, and a truthful capability declaration (section 5), and
- does not weaken the human-in-the-loop checkpoints.

**A harness is conformant when:**
- its adapter implements the MUST clauses of this spec (section 7), and
- it can honor the checkpoints (the consent checkpoint among them) and enforce a checkpoint for unattended runs (section 4).

Conformance is a floor, not a grade. [adoption.md](adoption.md) defines the levels above the floor (Core, Governed, Certified) and how a team declares which one it meets.

---

## Companion specifications

This is version 0.1. The rules above are the core and stand on their own. A set of companion specs makes them buildable without changing a single rule here:

- **[conformance.md](conformance.md)** turns section 8 into a machine-checkable test (per-subject, per-level checks) plus a `.adlc/conformance.yaml` manifest a project drops in to declare and prove its level.
- **[pack-format.md](pack-format.md)** fixes the pack wire format (section 5) and the capability vocabulary, backed by a real JSON Schema in [schema/](schema/pack-manifest.schema.json) with passing and failing examples.
- **[provenance.md](provenance.md)** defines the git-trailer provenance format and the view-time verifier: which lifecycle phases ran, on what, in what order, hash-linked and checkable with no server and no gate.
- **The reference conformance checker** ([tools/adlc-check.py](../tools/adlc-check.py)) runs the automatic checks and reports a verdict; it ships in the repo.

Read the companions when you implement or certify; read the rules above to understand the standard.

[RFC 2119]: https://www.rfc-editor.org/rfc/rfc2119
[RFC 8174]: https://www.rfc-editor.org/rfc/rfc8174
