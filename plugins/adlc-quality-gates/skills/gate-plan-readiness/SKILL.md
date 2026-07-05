---
name: gate-plan-readiness
description: "This skill should be used when the user asks to \"check the plan is ready\", \"is this plan good enough to start\", \"gate before implementation\", \"definition of ready\", \"DoR check\", \"can we start coding\", \"did the plan get approved\", or before any agent transitions from planning to implementation. Runs a pass/fail readiness gate that confirms the plan is complete AND explicitly approved before any code is written."
version: 0.1.0
---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# Gate: Plan Readiness (Definition of Ready)

A pass/fail gate that sits between Plan and Implement in the workflow loop. It answers
one question: **is this plan complete enough, and approved, that an implementer can
execute it without re-asking?** Until the gate passes, no implementation starts.

This is a Definition of Ready (DoR) applied to a single plan, a pre-flight checklist,
not a bureaucratic stage. It complements `create-plan` (which produces the plan) and
`validation-contracts` (which produces the acceptance criteria it checks for).

## When to use

- A plan/spec exists and the next step is writing code.
- An orchestrator needs a machine-checkable signal before spawning an implementer.
- A vague "let's just start": run the gate first to surface what is actually missing.

Skip only for trivial, reversible changes (a typo, a one-line copy fix) where the cost
of being wrong is near zero. When in doubt, run the gate.

## Procedure

1. **Locate the plan.** Read the plan artifact (e.g. `spec.md`) and any linked task or
   contract. If no written plan exists, the gate FAILS immediately, there is nothing to
   implement against.
2. **Run the readiness checklist** (below) against the plan. Each item is yes/no, judged
   from the plan text, not from optimism.
3. **Decide the verdict** using the rule below, READY or NOT READY. No "mostly ready".
4. **Confirm approval.** A complete plan that the operator has not explicitly approved is
   still NOT READY. This is a stop-and-ask gate, see Approval gate below.
5. **Emit the verdict report** in the exact format below.

## Readiness checklist

Judge each strictly from the plan. Mark `pass`, `fail`, or `unknown` (treat `unknown` as
`fail`: an unverifiable item is not ready).

- [ ] **Context**: why the work is needed is stated (not "clean up code"); the problem
      is clear.
- [ ] **Approach**: specific enough to start: names the files/interfaces touched and the
      ordering of changes. An implementer would not need to re-ask "where".
- [ ] **Acceptance criteria**: observable, testable conditions for "done" exist (ideally
      Given-When-Then). Fuzzy adjectives ("fast", "robust") are quantified.
- [ ] **Validation**: the exact command(s) that prove correctness are named (module-
      scoped, plus an end-to-end check), not a generic "run the tests".
- [ ] **Scope & constraints**: what is in scope and what must NOT be touched are stated
      (constraints required even if "none", it shows they were considered).
- [ ] **Dependencies**: external blockers (APIs, other teams, migrations, flags) are
      identified, and none would block completion.
- [ ] **Size**: the change is small enough to implement and verify in one focused unit;
      if larger, it is justified and broken into ordered steps.
- [ ] **No unresolved unknowns**: every `[NEEDS INPUT: …]` / `unknown` is either answered
      or explicitly accepted by the operator as out of scope.
- [ ] **Locations read**: the exact files/symbols the plan touches were actually opened
      and read, identified by path, not guessed. Entry points and call sites named.
- [ ] **Contracts known**: the signatures, data shapes, and module boundaries the change
      depends on come from the real code/API (cross-module deps through the right `-api` /
      interface), not inferred from memory.
- [ ] **No invented facts**: every claim stated as fact in the plan is backed by something
      actually read; anything unverified is marked `unknown`, not asserted (item-8
      invented-facts scan).
- [ ] **Approved**: the operator has explicitly said yes to *this* plan (see below).

## Verdict rule

- **READY**: every checklist item is `pass`, including Approved.
- **NOT READY**: any item is `fail` or `unknown`. List every failing item; do not start
  implementation.

There is no partial pass. One missing item blocks the gate. Do not lower the bar to make
a plan pass, fix the plan instead, then re-run the gate.

## Approval gate (stop-and-ask)

Completeness is necessary but not sufficient. Before declaring READY:

- Confirm the operator explicitly approved the current plan (not a stale earlier version).
- If the plan changed after approval, approval is void, re-confirm.
- Approval is never implied, standing, or inferred from silence. If unconfirmed, the
  verdict is **NOT READY, awaiting approval**; present the plan and wait for "yes".

This gate is read-only and local, it never pushes, posts, or sends anything. It triggers no
outbound step itself, but it must never wave a plan through to implementation on
assumed approval.

## Verdict report (exact format)

```
## Plan Readiness Gate: <plan name / spec.md>

Verdict: READY ✅  |  NOT READY ❌

Checklist:
- Context ............... pass / fail / unknown
- Approach .............. pass / fail / unknown
- Acceptance criteria ... pass / fail / unknown
- Validation ............ pass / fail / unknown
- Scope & constraints ... pass / fail / unknown
- Dependencies .......... pass / fail / unknown
- Size .................. pass / fail / unknown
- No unresolved unknowns. pass / fail / unknown
- Locations read ........ pass / fail / unknown
- Contracts known ....... pass / fail / unknown
- No invented facts ..... pass / fail / unknown
- Approved .............. pass / fail / unknown

Blocking items (only if NOT READY):
- <item>: <what is missing and the one concrete change that fixes it>

Next step: <"Proceed to implementation." | "Return to create-plan: <fix>." | "Awaiting operator approval.">
```

For a filled-in example report, see [references/gate-plan-readiness-detail.md](../../references/gate-plan-readiness-detail.md).

## References

- Atlassian, "Definition of Ready (DoR) Explained & Key Components", canonical DoR
  checklist (business value, dependencies, estimable, testable acceptance criteria):
  https://www.atlassian.com/agile/project-management/definition-of-ready
- Mike Cohn / Mountain Goat Software, "Definition of Ready", treat criteria as
  guidelines, not a rigid 100%-compliance gate:
  https://www.mountaingoatsoftware.com/blog/the-dangers-of-a-definition-of-ready
- gate-plan-readiness-detail.md (this plugin): filled-in verdict example:
  [references/gate-plan-readiness-detail.md](../../references/gate-plan-readiness-detail.md)
