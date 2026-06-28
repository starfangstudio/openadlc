---
name: validation-contracts
description: "This skill should be used when the user asks to \"define acceptance criteria\", \"write a validation contract\", \"turn this story into given-when-then\", \"write Gherkin scenarios\", \"do ATDD for this feature\", \"what does done look like for this feature\", or otherwise needs executable, testable acceptance conditions before implementation begins. Produces atomic Given-When-Then scenarios that double as the feature's verification gate."
version: 0.1.0
---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# Validation Contracts (ATDD / Given-When-Then)

Define the acceptance contract for a feature **before** implementation, as concrete
Given-When-Then scenarios. The contract is the agreed answer to "what does done look
like" and becomes the pass/fail gate at the Verify step of the workflow loop.

Write the contract during Explore/Plan, get it approved, then implement against it.

## When to use

- A new feature, story, or bug fix needs agreed, testable acceptance conditions.
- A vague request ("make search better") needs to be pinned to observable behavior.
- The Verify step needs a concrete checklist to run pass/fail against.

If the request is purely a refactor with no behavior change, skip, there is no new
contract to write; reuse existing tests as the gate.

## Procedure

1. **Restate the goal in one line.** Capture the user-facing outcome, not the
   implementation. If the goal is ambiguous, STOP and ask, never invent acceptance
   criteria the operator did not agree to.
2. **List the scenarios.** Enumerate the happy path first, then each error/edge case,
   then boundary conditions. One scenario per distinct behavior. For systematic edge
   enumeration (equivalence partitions, boundary values, error paths), run the
   `test-scenario-expander` skill and fold its matrix back in here.
3. **Write each as Given-When-Then** (format below). Keep each scenario atomic and
   independently runnable.
4. **Run the validator loop** (below). Fix every flagged scenario before presenting.
5. **Present the contract for approval.** Do not start implementing until the operator
   confirms the contract is correct and complete. This is a stop-and-ask gate.
6. **Persist the contract.** Write the approved scenarios where they outlive the chat:
   an "Acceptance criteria" section in the run's `spec.md`, or
   `~/.openadlc/runs/<workspace>/<run-id>/plan/contract.md` (the out-of-repo run
   workspace from `run-isolation.md`, never inside the repo). The contract is the
   verification gate, it must not be ephemeral.
7. **Hand off to Verify.** Each scenario maps to one automated test or one manual check
   that returns pass/fail. To run a single scenario against the live app, hand it to
   `/validate-scenario`, which drives the running app through one Given-When-Then and
   reports observed vs. expected.

## Format

One scenario per behavior. Use `And` to chain steps within a clause.

```gherkin
Feature: <feature name, the capability under test>

  Scenario: <happy path, named by behavior not by step>
    Given <the state of the world before the behavior>
      And <additional precondition>
    When <the single action being specified>
    Then <the observable, verifiable outcome>
      And <additional expected outcome>

  Scenario: <error case, named by what goes wrong>
    Given <precondition that triggers the error>
    When <the action>
    Then <the specific, observable failure response>
```

- **Given** = preconditions / state before the behavior (setup; commands).
- **When** = the one action being specified (keep it single, two `When`s means two
  scenarios).
- **Then** = observable outcomes only, side-effect-free (queries/assertions). Never
  assert on internal state a user cannot observe.

## Rules (hold strictly)

- **Behavior, not implementation.** "Then the user sees their order confirmation", not
  "Then `orderService.save()` is called". The contract must survive a refactor.
- **Quantify everything fuzzy.** Replace "fast", "user-friendly", "handles load" with a
  measurable threshold: "Then results return within 200 ms", "Then the list shows at
  most 50 items".
- **Atomic + independent.** Each scenario sets up its own Given and tests one outcome.
  No scenario depends on another having run first.
- **One When per scenario.** A second action is a second scenario.
- **Cover the unhappy paths.** A contract with only the happy path is incomplete, enumerate error responses, empty/null inputs, and boundaries.
- **Shared language.** Wording a PO, tester, and developer all read the same way. No
  internal jargon, no class names.

## Validator → fix loop

Before presenting, check every scenario against this list. Rewrite any that fail, then
re-check:

- [ ] Goal restated as a user-facing outcome, approved-or-asked (not invented).
- [ ] Happy path present, plus at least one error case and one boundary case.
- [ ] Every scenario has exactly one `When`.
- [ ] No `Then` references implementation detail (method names, tables, internal state).
- [ ] No fuzzy adjectives, each is replaced by a measurable threshold.
- [ ] Each scenario is self-contained (its own `Given`, no cross-scenario ordering).
- [ ] Each scenario maps to a runnable check for the Verify step.

If any box is unchecked, fix and re-run the loop. Only a fully-checked contract goes to
the approval gate.

## Example

```gherkin
Feature: Password reset

  Scenario: Registered user requests a reset link
    Given a registered account exists for "ada@example.com"
    When a reset is requested for "ada@example.com"
    Then a reset email is sent to "ada@example.com" within 60 seconds
      And the email contains a link valid for 24 hours

  Scenario: Reset requested for an unknown address
    Given no account exists for "nobody@example.com"
    When a reset is requested for "nobody@example.com"
    Then no email is sent
      And the response is the same generic confirmation shown to known users

  Scenario: Expired reset link is used
    Given a reset link issued more than 24 hours ago
    When the link is opened
    Then the user sees an "expired link" message
      And no password change is permitted
```

## References

- Martin Fowler, "GivenWhenThen": origin (Dan North / Chris Matts, BDD) and structure:
  https://martinfowler.com/bliki/GivenWhenThen.html
- Cucumber, "Gherkin Reference": official keyword/scenario syntax:
  https://cucumber.io/docs/gherkin/reference/
