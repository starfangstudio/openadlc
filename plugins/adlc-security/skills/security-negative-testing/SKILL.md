---
name: security-negative-testing
description: >-
  Derive attacker-driven (negative) test cases from a feature or threat. Triggers:
  "write abuse cases", "negative security tests", "what could an attacker do here",
  "turn this threat into a test", "test the auth/access-control defenses". Generates
  abuse cases the "as an attacker, I…" way, turns each into a security requirement and a
  failing-by-default negative test. Analysis/authoring only: runs nothing and sends nothing.
version: 0.1.0
---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# Security negative testing (abuse cases)

Derive what an attacker *would* do to a feature, then turn each abuse into a
**negative test**: one that asserts the system *rejects* the misuse. This is
the adversarial complement to `test-scenario-expander` (which enumerates
functional edge cases): here every scenario is an attack the code must defend
against. Authoring only, this produces abuse cases and test designs; it writes
no production code and runs nothing.

## Inputs

Work from a feature, user story, endpoint, spec, or UI flow. Restate in one line
before starting: the **feature**, its **actors** (legit user, anonymous,
low-priv user, admin, external system), its **assets/effects** (what it reads,
writes, or triggers), and any **stated security rules**. Mark anything not given
as `unknown`: never invent a limit, role boundary, or control that the spec
does not state. If a critical control is unknown (e.g. "is there rate
limiting?"), that is itself an abuse case to test, not an assumption.

## Workflow

1. **List the legitimate use.** One plain sentence per intended action ("a
   signed-in user updates their own profile").
2. **Negate it to generate abuse cases.** Insert "no" / "not" / "someone
   else's" / "more than allowed" around each noun and verb. Phrase every abuse
   case as **"As an attacker, I <do the misuse>"**: concrete and testable.
3. **Classify each abuse case** by the property it attacks using STRIDE (see
   the STRIDE section below); the label maps to a control class. Drop abuse
   cases that don't apply to this feature; don't pad.
4. **Promote each kept abuse case to a security requirement**: the acceptance
   criterion the feature must satisfy ("the server rejects updates to a profile
   the caller does not own with 403, and logs it").
5. **Design the negative test** for each requirement. A negative test performs
   the misuse and **asserts the defensive outcome** (reject / 4xx / no state
   change / audit entry); it must fail if the defense is missing.
6. **Emit the abuse-case matrix**, then open questions.

## STRIDE → property → control (classify each abuse case)

Each STRIDE letter violates one security property; the control class is where the defensive requirement comes from. If a finding spans two letters, split it: one label per distinct violation, each maps to a different control.

For the full STRIDE property table and abuse-case generators checklist, see [references/security-negative-testing-detail.md](references/security-negative-testing-detail.md).

STRIDE labels for inline use: **S**poofing (Authentication), **T**ampering (Integrity), **R**epudiation (Non-repudiation), **I**nformation disclosure (Confidentiality), **D**enial of service (Availability), **E**levation of privilege (Authorization).

## Output: abuse-case matrix

Emit one table: columns `# | STRIDE | Abuse case ("As an attacker, I...") | Security requirement (defense) | Negative test: action -> asserted outcome | Priority`. One row per abuse case, grouped by STRIDE letter, deduplicated. Follow with an `## Open questions` block for any unknown controls.

Priority: **P1** = auth/authZ bypass, injection, data exposure; **P2** = DoS, misuse-defense, integrity-of-flow; **P3** = lower-likelihood or defense-in-depth. One row per distinct defense, not per payload variant.

For the exact format with example rows, see [references/security-negative-testing-detail.md](references/security-negative-testing-detail.md).

## Validator → fix loop

Before presenting, self-check and fix any gap:
- Every legitimate action has at least one abuse case (or a note why none applies).
- Each of the seven abuse-case generators (in the detail reference) was considered; skipped ones are noted as N/A, not silently dropped.
- Every abuse case has a **defensive** requirement and a test that **asserts
  rejection**: not a test that merely confirms the happy path still works.
- Each abuse case carries a STRIDE label (see detail reference) mapped to a control class.
- An auth-bypass case **and** an authorization/IDOR case exist for any feature
  that touches user-owned or role-gated data (or a note why N/A).
- No invented controls or thresholds: every concrete number traces to the spec
  or sits in Open questions.

## Scope and boundaries

- **Authoring only.** Designs abuse cases and negative tests; it writes no
  production code, picks no framework, and **runs nothing**: no scans, no
  payloads fired, no network. Hand the matrix to the test-writing workflow
  (`test-scenario-expander` / the project's test conventions).
- **Nothing here needs operator approval** because nothing leaves the machine. Running
  an actual abuse payload against a *live/remote* system would be an outbound
  action, out of scope for this skill and would need the operator's explicit yes under the consent law if ever done.
- The STRIDE labels and generators are in [references/security-negative-testing-detail.md](references/security-negative-testing-detail.md); that file is loaded on demand and does not block this skill from running. Pairs with the built-in `security-review` for finding real instances in code. `security-property-taxonomy-reference` remains an optional deeper reference card.

## Android note

Express negative tests as fast JVM unit tests on the ViewModel/interactor where
possible (assert the rejected state transition or sealed `Result` error), per
`android-testing.md`. Cover platform abuse surfaces too: exported
Activities/Services/Receivers invoked by a malicious app, untrusted deep-link /
intent extras, and WebView features rendering untrusted content (see
`webview-engineering`). Don't write defensive tests for impossible states.

## References

- [references/security-negative-testing-detail.md](references/security-negative-testing-detail.md): STRIDE property table, abuse-case generators checklist, and matrix output format with example rows.
- OWASP: *Abuse Case Cheat Sheet* (workshop method; the "no/not" generation trick; abuse case -> security requirement -> security test): https://cheatsheetseries.owasp.org/cheatsheets/Abuse_Case_Cheat_Sheet.html
- OWASP Web Security Testing Guide (WSTG), §10.7 *Test Defenses Against Application Misuse*: https://owasp.org/www-project-web-security-testing-guide/v42/4-Web_Application_Security_Testing/10-Business_Logic_Testing/07-Test_Defenses_Against_Application_Misuse.html
- OWASP SAMM: *Requirements-Driven Testing: Misuse/Abuse Testing*: https://owaspsamm.org/model/verification/requirements-driven-testing/stream-b/
