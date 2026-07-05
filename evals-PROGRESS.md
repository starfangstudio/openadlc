<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
# Behavioral evals: coverage tracker

Tracks which of the 18 packs ship a real behavioral eval (P3b), the kind defined in
[docs/eval-format.md](docs/eval-format.md). A pack is **done** only when its `evals/`
suite passes the authoring self-test in that doc and its manifest reads
`evals: conformance+gate`. Until then it stays `conformance` (structural only).

> LOOP HALTED by operator after firing 4 (2026-07-02). 10 of 18 packs covered. The remaining 8 packs stay `evals: conformance` and are pending for a future session. Do NOT auto-resume: a scheduled wakeup that re-enters the loop should read this marker and stop.

## Status (10 of 18 done)

| Pack | Cases | Manifest `evals` | State |
|---|---|---|---|
| adlc-core | 3 (outbound-consent, plan-before-code, verify-before-done) | conformance+gate | done |
| adlc-planning | 4 (iterate-plan-spec-first, plan-resume-verify-code, architect-contract-before-impl, issue-analyzer-readonly-trace) | conformance+gate | done |
| adlc-security | 4 (bola-object-authz, secret-scan-before-push, negative-abuse-tests, reachability-no-disclosure) | conformance+gate | done |
| adlc-testing | 4 (contract-before-code, critic-reads-not-writes, pyramid-not-icecream, systematic-edge-enumeration) | conformance+gate | done |
| adlc-ai | 4 (on-device-consent-before-cloud, evals-before-ship, rag-injection-quarantine, agent-vs-simpler-tier) | conformance+gate | done |
| adlc-privacy | 3 (consent-before-sdk, lootbox-odds-and-geogate, privacy-review-readonly-verdict) | conformance+gate | done |
| adlc-quality-gates | 4 (deployment-readiness-evidence-and-consent, plan-readiness-explicit-approval, traceability-untested-is-fail, skill-efficacy-requires-measured-baseline) | conformance+gate | done |
| adlc-web | 3 (server-data-not-app-state, ssr-secret-boundary, web-reviewer-readonly-no-disclosure) | conformance+gate | done |
| adlc-backend | 3 (trust-client-result, destructive-migration-consent, modular-monolith-default) | conformance+gate | done |
| adlc-database | 4 (expand-contract-migration, parameterized-search-query, measure-before-index-and-paginate, exact-money-and-time-types) | conformance+gate | done |
| adlc-android | | conformance | pending |
| adlc-ios | | conformance | pending |
| adlc-desktop | | conformance | pending |
| adlc-design | | conformance | pending |
| adlc-ops | | conformance | pending |
| adlc-monetization | | conformance | pending |
| adlc-backend-cloud | | conformance | pending |
| adlc-unity | | conformance | pending |

## Batch plan (3 packs per firing)

- Firing 1 (done): design the format + `tools/run-evals.py` + adlc-core exemplar suite.
- Firing 2 (done): adlc-planning, adlc-security, adlc-testing (4 cases each, workflow-designed + adversarially verified).
- Firing 3 (done): adlc-ai, adlc-privacy, adlc-quality-gates (workflow-designed + adversarially verified).
- Firing 4 (done): adlc-web, adlc-backend, adlc-database (workflow-designed + adversarially verified).
- Firing 5 (pending): adlc-android, adlc-ios, adlc-desktop.
- Firing 6 (pending): adlc-design, adlc-ops, adlc-monetization.
- Firing 7 (pending): adlc-backend-cloud, adlc-unity.

To resume in a future session: repoint `PACKS` in the workflow script (or author inline) to the next pending trio, run the design + adversarial-verify pass, render into each pack's `evals/`, validate with `run-evals.py`, then flip the manifest.

## The bar for marking a pack done

Per firing, for each pack: read the pack's units, author 2 to 4 eval cases whose
assertions trace to real guidance in those units, run the authoring self-test in
[docs/eval-format.md](docs/eval-format.md), validate the shape, and only then flip the
manifest to `conformance+gate`. A pack whose behavioral delta cannot be made honest
stays `conformance` with a one-line reason recorded here rather than a fake gate.

## Commands

```
python3 tools/run-evals.py <pack>                 # validate + print the run plan
python3 tools/run-evals.py <pack> --score s.json  # score a filled scores.json
python3 tools/run-evals.py all                    # validate every pack's suite shape
```
