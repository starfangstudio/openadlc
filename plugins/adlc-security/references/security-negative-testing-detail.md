<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
Consumed by the `security-negative-testing` skill. Load on demand; do not load independently.

## STRIDE property table

| STRIDE threat | Violates property | Defender's question | Primary control class |
|---|---|---|---|
| **S**poofing | Authentication | "Are you who you claim to be?" | Identity / credentials / MFA / signatures |
| **T**ampering | Integrity | "Has the data/code been altered?" | Hashes, signatures, input validation, access control |
| **R**epudiation | Non-repudiation | "Can the actor deny doing it?" | Audit logs, signed receipts, secure timestamps |
| **I**nformation disclosure | Confidentiality | "Can the wrong party read it?" | Encryption (rest+transit), least-privilege, redaction |
| **D**enial of service | Availability | "Can legitimate users still use it?" | Rate limits, quotas, redundancy, timeouts |
| **E**levation of privilege | Authorization | "Can they do more than allowed?" | AuthZ checks, sandboxing, least-privilege |

If a finding spans two letters, split it: one label per distinct violation, each maps to a different control.

## Abuse-case generators (run every applicable one)

Walk this checklist against the feature; each line is a "no/not" negation:

- **Identity (Spoofing):** call it unauthenticated; replay/forge a token; act as another user by changing an id.
- **Authorization (Elevation):** low-priv user invokes a high-priv action; access another tenant's/user's object (IDOR); bypass the check via a different route (API vs UI), mass-assignment, or hidden field.
- **Integrity (Tampering):** trust a client-supplied price/role/total; skip a required step in a multi-step flow; tamper with a signed/serialized value; inject (SQLi, command, path traversal, template, XSS-shaped) payloads.
- **Confidentiality (Disclosure):** read errors/stack traces for secrets; enumerate ids; over-fetch fields; pull data via verbose responses or logs.
- **Availability (DoS):** oversized/deeply-nested payload; unbounded list/regex/file upload; no rate limit on expensive or auth endpoints.
- **Non-repudiation (Repudiation):** perform a sensitive action and check nothing is logged, or the actor/time can be forged.
- **Application misuse (WSTG 10.7):** hammer the feature like an attacker probing; does an app-layer defense (lockout, throttle, anomaly flag) trigger, and can it itself be abused (e.g. lock out another user, or set the lockout counter negative to bypass it)?

## Abuse-case matrix output format

Emit one table. One row per abuse case. Group by STRIDE letter. Deduplicate.

```
## Abuse cases: <feature>
Actors in scope: <anonymous | low-priv user | other-tenant | admin | external system>

| # | STRIDE | Abuse case ("As an attacker, I...") | Security requirement (defense) | Negative test: action -> asserted outcome | Priority |
|---|--------|--------------------------------------|--------------------------------|-------------------------------------------|----------|
| 1 | E | ...invoke /admin/* as a low-priv user | AuthZ enforced server-side per role | call as low-priv -> 403, no state change, audit logged | P1 |
| 2 | I | ...read another user's invoice by id | object-level authZ on every fetch | request other id -> 404/403, no data leaked | P1 |
| 3 | D | ...upload a 2GB / deeply-nested payload | size + depth limits enforced | oversized body -> 413, server stays responsive | P2 |

## Open questions
- <unknown control the spec must define before the test is writable, e.g. "is there a rate limit, and at what threshold?">
```

Priority definitions: **P1** = auth/authZ bypass, injection, data exposure (high blast radius); **P2** = DoS, misuse-defense, integrity-of-flow; **P3** = lower-likelihood or defense-in-depth. One row per distinct defense, not per payload variant.
