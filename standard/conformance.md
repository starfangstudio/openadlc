<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# ADLC Conformance Test

> Status: draft proposal, pre-ratification. Tests against spec version 0.1.
> One line: the checkable test behind "ADLC-conformant." [spec.md](spec.md) section 8 says conformance is a checkable claim; this is the actual checklist.

A standard that cannot be checked is a slogan. This document turns the spec's MUST clauses into a numbered test a person or a script can run against a team, a pack, or a harness, plus a manifest a project drops in its repo to declare and prove its level.

## Why this is a test, not just prose (precedent)

We checked how six category-owning standards handle conformance. The split set this document's design:

- **CommonMark** ships 600+ examples that "are intended to double as conformance tests," plus a runner.
- **JSON Schema** ships an official data-driven test suite, decoupled from the prose spec.
- The web platform pairs every requirement with **Web Platform Tests (WPT)**, a shared CI-gated suite, and calls a feature done only when independent implementations pass it.
- **OpenAPI, SemVer, and Conventional Commits** stop at prose MUST-language with no owned checker, so conformance there is vague and outsourced to third-party tools.

The directive we took: **pair every MUST with an executable check, and own the checker.** RFC-2119 language in [spec.md](spec.md) makes the requirements precise; this document and its manifest make them runnable.

## How to read a check

Each check has an **ID**, an **assertion**, the **spec clause** it enforces, and a verification tag:

| Tag | Who decides | Strength |
|---|---|---|
| **auto** | a script | strongest: a deterministic pass/fail (schema validation, a probe that must be blocked, an eval run) |
| **audit** | a human or script samples evidence | medium: reproducible only if the sample rule is defined |
| **attest** | the operator vouches | weakest: a practice that is not mechanically provable, called out as such |

A subject reaches a **level** when every check at that level and every level below it is PASS. The verdict rule and the manifest are at the end.

---

## Team checks

### Core (the floor)
- **T-C1** - Human in the loop: a human decides at the lifecycle's checkpoints (plan approval at Plan, code review at Review, consent at Consent), and the decisions are honored. The consent checkpoint behaves per spec section 4: before any outward action the agent stops, presents exactly what would go out, and proceeds only on an explicit per-action approval (the section 4 exemptions are NOT stopped). The plan and review checkpoints are the team's to tune; the consent checkpoint always applies to the release decision. _(Spec section 4 / Law L1.)_ **attest** at Core, because honoring is a practice, not a mechanism. (Central enforcement is checked at T-G1.)
- **T-C2** - Non-trivial changes move through the lifecycle in order and produce its artifacts: a plan before implementation, verification evidence before review, and a consent record strictly before any release. _(Spec section 2.)_ Verify by sampling recent changes against the phase order. **audit**
- **T-C3** - "Done" requires a passing, failable check, and the evidence is recorded. _(Law L5.)_ **audit**
- **T-C4** - Explore-phase work is read-only: sampled exploration steps show no file writes and no outward actions. _(Spec section 2, "Explore MUST be read-only".)_ **audit**
- **T-C5** - Audit trail: each human checkpoint decision (plan approval, code review, consent) is recorded locally, with what, when, and who. _(Spec section 6 / Law L1.)_ **audit**

### Governed (adds, for an organization)
- **T-G1** - The chosen checkpoints (including the consent checkpoint) are enforced centrally, not just honored: a mechanism makes them unskippable across every seat, including in unattended runs. Verify by running an unattended agent under policy and confirming an outward action is hard-denied without pre-approval. _(Spec section 4, enforcement.)_ **auto**
- **T-G2** - Checkpoint, pack, and rule policy is set centrally and applied to every seat. Pass = the enrolled-seat list reconciles against the active-seat list with no unmanaged seats. _(adoption.md Governed.)_ **audit**
- **T-G3** - The audit trail is centrally kept and provable across the organization: an append-only log of checkpoint decisions, retained per the stated window, covering every active seat (same reconciliation as T-G2). _(Spec section 6 / adoption.md Governed.)_ **audit**

### Certified (planned, not operational)
- **T-X1** - Every pack in use carries a valid ADLC certification mark. _(adoption.md Certified.)_ Verify against the certification registry. Status: the certification program is not yet operational; this check is defined, not runnable.

> Note on the word "Certified": the team adoption level **Certified** (this ladder) is a different axis from a pack's **Certified** trust tier in the certification program. A Certified team runs certified packs; "the team is Certified" and "the pack is Certified" are distinct claims.

---

## Pack checks

These split by what is mechanically decidable. The schema ([pack-format.md](pack-format.md)) covers the **auto** ones; the rest need running code or judgement.

- **P1** - Has a manifest with name, version, description, owner, targeted spec version, and a capability declaration. _(Spec 5.1.)_ **auto** (validate against the schema).
- **P2** - Has at least one guidance unit (skill, agent, rule, or reference). _(Spec 5.2.)_ **auto**
- **P3a** - An eval set is present. _(Spec 5.3.)_ **auto**
- **P3b** - The eval set runs and its result beats the declared no-pack baseline (delta greater than zero). _(Spec 5.3 / Law L5.)_ **auto** (run the evals). If the pack declares no runner, P3b is `not-run` and does not gate (P3a presence is still required). Eval *quality* (is the baseline honest, are the tasks representative) is a separate **audit**.
- **P4** - The capability declaration is well-formed and contains no banned declaration. _(Spec 5.4.)_ **auto**. The harder MUST, that the declaration matches actual behavior, is NOT decidable at this layer; it needs the declaration-vs-behavior scan specified in the certification program's enforcement spec. This document records that scan's result; it does not re-specify it.
- **P5** - The manifest declares no checkpoint-subverting capability (e.g. touching any human-in-the-loop checkpoint's config) and ships no opaque binary. _(Spec section 5, universal bans in [pack-format.md](pack-format.md).)_ **auto** (these are structural). Detecting *prose* that coaxes a human or agent into bypassing a checkpoint is not reliably decidable and is handled as a risk signal by 16's scan, not as a pass/fail here.
- **P6** - Version follows Semantic Versioning. _(Spec 5.1, SHOULD.)_ **auto**, but advisory: a SHOULD may be overridden with a stated reason, so a SemVer-violating pack with a reason is still conformant. P6 reports `warn`, it does not cap the level.

---

## Harness checks

A harness claims conformance by shipping an **adapter** (spec section 7). H1 is derived from the rest.

- **H1** - The adapter implements the spec's MUST clauses. Derived: **H1 passes if and only if H2, H3 (intool or external), H4, and H5 pass.** No separate tag.
- **H2** - The adapter can honor a checkpoint (the consent checkpoint among them): before an outward action the agent stops, and the approval prompt shows what would go out before approval is possible. Verify with a scripted outward action that must pause and must display its payload. _(Spec section 4.)_ **auto**
- **H3-intool** - The adapter can enforce a checkpoint in-tool for unattended runs (the consent checkpoint: outward actions hard-denied without pre-approval). _(Spec sections 4, 7.)_ **auto**
- **H3-external** - If the harness cannot enforce in-tool, an external below-harness control (egress check, server-side gate) does. Verify with a probe that the external control must deny, and capture the denial as evidence. _(Spec section 7.)_ **audit** (the harness cannot self-test an out-of-band control). A harness passes the enforcement requirement via H3-intool OR H3-external.
- **H4** - The adapter can load a conformant pack (map the pack shape onto the harness's primitives). Verify by loading the example pack. _(Spec sections 5, 7.)_ **auto**
- **H5** - Exempt actions are not gated: a local read, a local edit, and a local test each proceed without an approval prompt. This guards the over-gating failure (a gate that blocks everything is as useless as one that blocks nothing). _(Spec section 4 exemptions.)_ **auto**

---

## The conformance manifest

A project declares and proves its level with one file, `.adlc/conformance.yaml`. It names the spec version, the subject, the claimed level, and the evidence for each required check. A checker validates that every required check is present, is `pass`, and that the evidence path exists.

```yaml
adlc-conformance: "0.1"        # the spec version this claims against
subject: team                  # team | pack | harness
level: governed                # core | governed | certified
checks:                        # one entry per required check for the claimed level and below
  T-C1: { status: pass, evidence: "<checkpoint config showing which checkpoints are on> + <a log of a checkpoint decision: plan approval / review / consent>" }
  T-C2: { status: pass, evidence: "<plans + reviews for a sample of recent changes>" }
  T-C3: { status: pass, evidence: "<CI run links for the same sample>" }
  T-C4: { status: pass, evidence: "<explore-phase logs showing no writes>" }
  T-C5: { status: pass, evidence: "<local audit log of checkpoint decisions>" }
  T-G1: { status: pass, evidence: "<unattended-run deny log under central policy>" }
  T-G2: { status: pass, evidence: "<enrolled-vs-active seat reconciliation>" }
  T-G3: { status: pass, evidence: "<central append-only checkpoint audit log, retention stated>" }
attested-by: "Jane Dev <jane@example.com>"
date: "2026-06-26"
```

The paths above are illustrative; any path or link a checker or auditor can open satisfies the rule. There is no mandated directory layout.

Rules for the manifest:
- The claimed `level` MUST list every check for that level and all levels below it; a missing required check fails the claim.
- A check MUST be `pass`, `fail`, `warn` (advisory only, e.g. P6), or `n/a` (with a reason).
- Evidence MUST be a path or link a checker or auditor can open. "Trust me" is not evidence.
- A false claim (a `pass` whose evidence does not hold) breaks the whole signal, so the badge is only as good as the audit behind it.

## The verdict

- A subject's **achieved level** is the highest level for which all required non-advisory checks pass.
- The badge a team displays ([adoption.md](adoption.md)) MUST match the achieved level, never a higher one.
- A failed required check at a level caps the subject at the level below. Advisory checks (P6) report a warning and do not cap.

## Honest limits

- **Honoring is not provable; enforcing is.** Core asks the checkpoints to be *honored* (T-C1, **attest**). Governed makes the chosen checkpoints *enforced* centrally (T-G1, **auto**), which is where conformance becomes a hard, mechanically-checkable control across a fleet. This is why an organization moves past Core: only enforced checkpoints are mechanically trustworthy at scale.
- **Eval efficacy and capability-match need running code.** P3b runs the evals; P4's behavior-match needs the scan in the certification program's enforcement spec. This file records those results; it does not re-specify the scanner.
- **Certified is defined, not operational.** T-X1 and the Certified level are written so the ladder is complete; the program that issues the mark does not exist yet.
- **The owned checker is the next build.** A reference checker that reads `.adlc/conformance.yaml` and runs the **auto** checks is in scope for the standard *project*, not the standard *text*. The precedent (S8, S10, S11) is clear that a standard which does not ship its own checker loses control of what "conformant" means.
