---
name: security-property-taxonomy-reference
description: >-
  This skill should be used when the user asks to "classify a security threat",
  "map a finding to STRIDE", "which CIA property does this break", "is this
  confidentiality or integrity", "what STRIDE category is this", or
  "categorize a vulnerability", or otherwise needs the canonical
  taxonomy linking STRIDE threat categories to the CIA(+) security properties
  they violate. Reference card only: provides the shared vocabulary for threat
  modeling and security review; does not run scans or touch the network.
version: 0.1.0
---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# Security Property Taxonomy Reference (STRIDE + CIA)

Provide one shared vocabulary so threats, findings, and mitigations are
classified consistently. Two complementary lenses:

- **CIA(+)**: the *defender's* lens: the security *properties* a system must
  preserve.
- **STRIDE**: the *attacker's* lens: the *violation* of each property. Each
  STRIDE category is the negation of exactly one property.

## The taxonomy (memorize this table)

| STRIDE threat | Violates property | Defender's question | Primary control class |
|---|---|---|---|
| **S**poofing | Authentication | "Are you who you claim to be?" | Identity / credentials / MFA / signatures |
| **T**ampering | Integrity | "Has the data/code been altered?" | Hashes, signatures, input validation, access control |
| **R**epudiation | Non-repudiation | "Can the actor deny doing it?" | Audit logs, signed receipts, secure timestamps |
| **I**nformation disclosure | Confidentiality | "Can the wrong party read it?" | Encryption (rest+transit), least-privilege, redaction |
| **D**enial of service | Availability | "Can legitimate users still use it?" | Rate limits, quotas, redundancy, timeouts |
| **E**levation of privilege | Authorization | "Can they do more than allowed?" | AuthZ checks, sandboxing, least-privilege |

CIA triad = **C**onfidentiality, **I**ntegrity, **A**vailability. STRIDE
extends it with Authentication, Non-repudiation, and Authorization, so treat
the working set as **CIA+ (six properties)**, one per STRIDE letter.

## CIA property definitions (NIST)

- **Confidentiality**: preserving authorized restrictions on access and
  disclosure, including protecting privacy and proprietary information.
- **Integrity**: guarding against improper modification or destruction;
  ensuring non-repudiation and authenticity.
- **Availability**: ensuring timely and reliable access to and use of
  information.

## How to classify a finding

1. State the asset and the bad outcome in one sentence ("an attacker can read
   other users' invoices").
2. Pick the **violated property** by asking the defender's question above.
3. Map property → STRIDE letter via the table (read confidentiality = **I**;
   wrong-altered data = **T**; etc.).
4. If a finding spans multiple letters, **split it**: one STRIDE label per
   distinct violation (e.g. a missing authZ check that also leaks data = **E**
   *and* **I**). Do not collapse them; each maps to a different control.
5. Name the control class from the last column so the fix is actionable.

## Worked examples

- Missing auth on an admin endpoint → caller acts as someone they aren't →
  Authentication → **Spoofing (S)**; if it lets a logged-in low-priv user reach
  admin actions, that is Authorization → **Elevation of privilege (E)**.
- Price field trusted from a client request → server-side data altered →
  Integrity → **Tampering (T)**.
- Action runs with no audit trail → actor can deny it → Non-repudiation →
  **Repudiation (R)**.
- Verbose stack trace leaks DB schema → wrong party reads it → Confidentiality
  → **Information disclosure (I)**.
- Unbounded regex / no rate limit → legitimate users locked out →
  Availability → **Denial of service (D)**.

## Scope and boundaries

- **Reference only.** This skill supplies the vocabulary. It performs no scans,
  no network calls, and no outbound actions, nothing here needs operator approval
  because nothing leaves the machine.
- Use it as the labeling layer for `security-review`, code review, and threat
  models; do not invent categories outside the six properties.
- `security-negative-testing` now carries the STRIDE → property table inline and
  no longer depends on this skill to run. Reach for this card when you want the
  fuller definitions, worked examples, and NIST sources behind that table.
- STRIDE classifies *what* is violated, not *how severe*, pair with a separate
  severity/CVSS step; do not infer priority from the letter alone.

## Example

A WebView feature that renders untrusted HTML: a script-injection
bug is **Tampering** (DOM integrity) and **Information disclosure** (reads
session data), two labels, two controls (CSP/sanitization and origin
isolation), not one "XSS" bucket.

## References

- Microsoft Learn: *The STRIDE Threat Model* (canonical source; per-category
  violated property): https://learn.microsoft.com/en-us/previous-versions/commerce-server/ee823878(v=cs.20)
- NIST SP 1800-25 / SP 800-53: authoritative CIA definitions:
  https://www.nccoe.nist.gov/publication/1800-25/VolA/index.html
- OWASP: *Threat Modeling Process* (STRIDE in practice):
  https://owasp.org/www-community/Threat_Modeling_Process
