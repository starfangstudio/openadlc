<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
---
id: candidate-tightening-narrows-discretionary
scenario: RED-PROVE 3 (B-172 S-A3)
proves: a stage-0 candidate-set tightening narrows a discretionary pack while the floor stands
---
# A candidate-set tightening narrows a discretionary pack (the floor stands)

## Starting condition

A repo matches two technical domains (`fx-multi`: `package.json` with react +
`Dockerfile` -> `{web, backend-cloud}`). The org policy's candidate set has been
tightened to DROP a discretionary pack: `adlc-backend-cloud` is not approved (an
org that does not run cloud infra).

## Expected observable behavior

The activation funnel activates `adlc-web` (matched AND in the candidate set) and
the mandatory floor (`adlc-core`, `adlc-security`), but NOT `adlc-backend-cloud`
(matched by repo facts, yet tightened out of the candidate set). Stage-0
narrowing genuinely works on discretionary packs.

## Assertion (bite radius: the ACTIVATED pack set, not that a function ran)

- `activate(fx-multi, candidate_set = ALL - {adlc-backend-cloud})` yields a set
  WITHOUT `adlc-backend-cloud`, and WITH `adlc-web`, `adlc-core`, `adlc-security`.
- Complements `pinned-floor-survives-repo-injection`: that proves the floor is
  IMMUNE to a tightening attempt; this proves a legitimate tightening still WORKS
  on a discretionary pack. Together they lock the stage-0 precedence rule (the
  floor stands, the discretionary set narrows).

## TEETH

A broken funnel that ignores `candidate_set` entirely (activates every matched
pack) keeps `adlc-backend-cloud` and FAILS this assertion; the correct funnel
(`candidate_set INTERSECT matched`) narrows it out and PASSES. Proven mechanically
by `tools/check-activation-redproves.py` red-prove 3.
