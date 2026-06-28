---
name: gate-deployment-readiness
description: >-
  Runs a fixed go/no-go checklist (verification, rollback, migrations,
  observability, secrets) against a pending release and emits a readiness
  report; supports both server deploys and Android Play staged rollouts. Use
  when the user asks "are we ready to ship", "go/no-go for the release",
  "pre-deploy checklist", "production readiness review", or "is this safe to
  release". Never deploys, pushes, or releases anything itself.
version: 0.1.0
---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# Gate: deployment readiness

Decide **go / no-go** for a release against a fixed checklist, then emit a
report. This is the last gate before the consent step, it answers "can we
safely operate this in production?", not "should we build it?". The release is
**blocked** until every blocking item is green or has a written, accepted
exception.

## What this builds on
This adapts the built-in **`engineering:deploy-checklist`** skill (and its
pre-deploy verification patterns). Invoke that engine for the checklist
mechanics; this skill adds the ADLC delta: a fixed go/no-go verdict format,
evidence-over-assertion discipline, and an explicit-operator-yes checkpoint before the deploy itself.
If `engineering:deploy-checklist` is not installed, fall back to the checklist
below as the source of truth, the gate is self-contained without it.

## Pick the release profile
- **Server / backend deploy** → the server checklist below (rollback artifacts,
  schema migrations, canary, observability). This is the default.
- **Mobile (Android via Google Play)** → route to the **Mobile (Play) release
  profile** section; a store rollout is staged and halted, not reverted, so the
  server rollback/migration items do not map cleanly.

## Workflow
1. **Identify the release.** What ships (diff / tag / build), where it goes, and
   the approved plan or spec it must satisfy. No plan → gate against the stated
   intent and say so in the verdict.
2. **Run the checklist** (below). Each item resolves to **pass / fail / n/a**,
   backed by evidence, not a claim. Missing evidence is a **fail**, not a pass.
3. **Decide the verdict.** Any blocking fail → **NO-GO**. Otherwise **GO**.
4. **Return the readiness report** (format below).
5. **🚦 Consent, then release**: never deploy from this skill.

## The checklist
Six dimensions, adapted from the Google SRE Production Readiness Review. Each
line is one finding with its evidence.

### Blocking: a fail here is an automatic NO-GO
- **Verification**: CI green on the exact commit being shipped; tests/build
  pass; the plan's named acceptance criteria are covered. Attach the run, don't
  assert it.
- **Rollback**: a tested, documented way back (revert, previous artifact, kill
  switch). State the exact command/step and who can run it. No rollback → NO-GO.
- **Data migrations**: schema/data changes are backward-compatible with the
  currently-running version (expand-then-contract); migration is reversible or
  forward-fix is documented; tested against production-like data.
- **Observability**: the change is monitored: logs, metrics, and alerts exist
  for the new/changed paths so a regression is *visible*, not silent.
- **Secrets & config**: required env/secrets/flags exist in the target env; no
  secret committed; config diff reviewed. (Route deeper concerns to the security
  gate, don't re-run it here.)

### Advisory: record, don't necessarily block
- **Ownership & on-call**: a named owner is reachable during/after rollout.
- **Capacity**: expected load is within headroom; no obvious scaling cliff.
- **Rollout strategy**: staged/canary/flagged where the blast radius warrants
  it, with the gradual ramp and abort criteria stated.
- **Dependencies**: downstream/upstream services and their versions are
  compatible; required ones are healthy.
- **Comms**: stakeholders/affected users know the window; status page or
  changelog ready if relevant.

## Mobile (Play) release profile
For an Android app shipped through Google Play, the server items above (rollback
artifact, schema migration, canary) do not map. Gate these instead:

### Blocking: a fail here is an automatic NO-GO
- **Staged rollout %**: the release goes out at a fraction (e.g. 5 → 20 → 50 →
  100), not 100% on day one. Name the starting percentage and the ramp criteria.
- **Halt, not revert**: the "way back" for Play is **halt the rollout** (and ship
  a forward-fix), because you cannot pull a version users already installed. State
  who can halt and the trigger (crash-rate / ANR threshold from the console).
- **targetSdk + Data safety compliance**: `targetSdk` meets Play's current
  requirement and the Data safety form matches what the app actually collects.
  **Delegate these checks to the installed `android-compliance` skill** (do not
  re-derive the deadlines or form rules here); attach its verdict as the evidence.

### Advisory: record, don't necessarily block
- **Observability**: crash/ANR dashboards and the new-path metrics exist in
  Play Console / Crashlytics so a regression is visible during the ramp.
- **Pre-launch report**: Play's automated pre-launch report reviewed; no new
  crashes on the device matrix.

Run the blocking server items that still apply (Verification, Secrets/config) plus
the three mobile items above. Mark the inapplicable server items **n/a** with a
one-line reason in the report.

## Readiness report format
Emit exactly this. Verdict first; every item carries evidence or a reason.

```
# Deployment readiness: <release / tag / PR #> → <target env>
Verdict: GO | NO-GO    (one line why)

## Blocking
- Verification    pass | fail | n/a: <evidence: CI run / link / reason>
- Rollback        pass | fail | n/a: <exact path back + who runs it>
- Migrations      pass | fail | n/a: <backward-compat + reversibility>
- Observability   pass | fail | n/a: <what makes a regression visible>
- Secrets/config  pass | fail | n/a: <present in target env>

## Advisory
- Ownership | Capacity | Rollout | Dependencies | Comms, <state each>

## Accepted exceptions
- <blocking item>, why it's acceptable to ship anyway + who accepted it

## Plan coverage
- <acceptance criterion> → verified | not verified
```

## Discipline
- **Evidence over assertion.** "Tests pass" without the run is a fail. Ask for
  the CI link, build log, or screenshot.
- A NO-GO loops back to implementation/verification; re-gate after fixes. Only a
  GO (or all-fails-accepted) proceeds to consent.
- Don't pad the checklist with items the change can't affect, mark them **n/a**
  with a one-line reason. Over-gating erodes trust in the gate.
- An accepted exception must be **written and attributed**: never a silent pass.

## Outbound checkpoint

Local work needs no approval. Anything outbound (publish, push, post) is a lifecycle checkpoint: present exactly what would go out and get the operator's explicit per-action "yes" first; see the global consent law.

## References
- Built-in skill adapted: `engineering:deploy-checklist`.
- Google SRE Book: *Evolving the SRE Engagement Model* (Production Readiness
  Review; the six dimensions: architecture/dependencies, monitoring, emergency
  response, capacity, change management, performance):
  https://sre.google/sre-book/evolving-sre-engagement-model/
