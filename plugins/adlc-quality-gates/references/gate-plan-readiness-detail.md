<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
Consumed by the `gate-plan-readiness` skill. Load on demand; do not load independently.

## Verdict report: example

A filled-in gate report illustrating a NOT READY verdict with two blocking items.

```
## Plan Readiness Gate: spec.md (add reset-link expiry)

Verdict: NOT READY ❌

Checklist:
- Context ............... pass
- Approach .............. pass
- Acceptance criteria ... pass
- Validation ............ fail
- Scope & constraints ... pass
- Dependencies .......... pass
- Size .................. pass
- No unresolved unknowns. pass
- Locations read ........ pass
- Contracts known ....... pass
- No invented facts ..... pass
- Approved .............. fail

Blocking items:
- Validation: plan says "run tests": name the module command, e.g.
  `./gradlew :auth-impl:testDebugUnitTest`, plus the end-to-end check.
- Approved: operator has not confirmed this plan.

Next step: Return to create-plan to fix Validation, then present for approval.
```
