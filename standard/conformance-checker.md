<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# The ADLC Conformance Checker

> Status: draft proposal, pre-ratification. For spec version 0.1.
> One line: the buildable spec for the owned reference checker, the tool that runs the automatic checks in [conformance.md](conformance.md) and reports a verdict.

[conformance.md](conformance.md) says a standard that does not ship its own checker loses control of what "conformant" means (the OpenAPI / SemVer / Conventional Commits lesson). This is the spec an implementer follows to build that checker. It is deliberately small: it runs the **auto** checks, records the **audit/attest** ones, and never pretends to decide what it cannot.

This file bundles everything the checker needs (the check IDs, their tags, the level map, the report shape). It refers to [conformance.md](conformance.md) for the prose rationale and to `schema/pack-manifest.schema.json` for the pack schema, but the tables below are the authority the checker is built from.

## What it does

The checker takes a target and a subject, runs the decidable checks for that subject, records the rest, and prints a verdict. It does not judge evidence quality or run behavioral scans; those belong to a human auditor and to the certification program.

```
adlc-check <subject> <path>
  subject: pack | team | harness
  path:    pack    -> a pack manifest (JSON or YAML), or the pack directory (enables the optional content scan)
           team    -> a directory containing .adlc/conformance.yaml
           harness -> a harness adapter endpoint or fixture (see Harness mode)
```

## The two bundled tables (the authority)

**Level to required-check IDs.** A subject claiming a level must satisfy that level's checks and all levels below it.

| Subject | Core / base | Governed adds | Certified adds |
|---|---|---|---|
| team | T-C1, T-C2, T-C3, T-C4, T-C5 | T-G1, T-G2, T-G3 | T-X1 (planned) |
| pack | P1, P2, P3a, P4, P5 (P3b when a runner exists; P6 advisory) | (same) | (same) |
| harness | H1, H2, H3, H4, H5 | (same) | (same) |

**Check to verification tag (provenance).** The checker decides **auto** checks; for **audit/attest** it only confirms the declaration exists, its declared status, and that its evidence resolves. It never upgrades an audit/attest check to "machine-proven."

| auto | audit | attest |
|---|---|---|
| T-G1, P1, P2, P3a, P3b, P4, P5, P6, H2, H3-intool, H4, H5 | T-C2, T-C3, T-C4, T-C5, T-G2, T-G3, H3-external | T-C1 |

## Status and provenance (one vocabulary)

Two separate fields, never mixed:
- **status** (per check): `pass | fail | warn | n/a | not-run`. This is the manifest vocabulary from [conformance.md](conformance.md) (`warn` is advisory, e.g. P6; `n/a` needs a reason; `not-run` = an auto check that could not execute, e.g. P3b with no runner).
- **provenance** (per check): `auto | audit | attest`, from the table above. `attest`/`audit` results are reported with their provenance so a reader never mistakes an attested `pass` for a machine-proven one.

There is no `attest-only` status; "attested" is the provenance flag on a `pass`.

## Pack mode: the per-check algorithm

P1 enforces the manifest required fields: **name, version, description, license, owner, the targeted spec version (`adlc`), units, evals, capabilities** (spec 5.1-5.4).

A per-pack `license` field is required so each pack declares its own terms (see [pack-format.md](pack-format.md): the ADLC standard stays CC-BY-4.0, the OpenADLC packs are source-available + commercial under the OpenADLC source-available license, see the `LICENSE` file). P1 requires `license` and validates it: the value must be present, and the checker warns on a value outside the known vocabulary (`LicenseRef-OpenADLC-Source-Available-1.0`, `CC-BY-4.0`).

| Check | Decision procedure | status |
|---|---|---|
| **P1** | Validate the manifest against `pack-manifest.schema.json` (covers the required fields above and the capability vocabulary). | pass / fail |
| **P2** | `units` present, length >= 1 (covered by schema). | pass / fail |
| **P3a** | `evals.path` resolves on disk. | pass / fail |
| **P3b** | If `evals` declares a runner, invoke it and read the delta vs `evals.baseline`; pass iff delta > 0. No runner -> `not-run` (does not gate). | pass / fail / not-run |
| **P4** | `capabilities` is schema-valid with no banned declaration (auto). The declared-vs-actual behavior match is **not decided here**; emit a pointer to the certification program's enforcement spec scan. | pass / fail |
| **P5** | Manifest-decidable half (auto): no checkpoint-subverting capability key (e.g. touching a human-in-the-loop checkpoint's config; none exists in the vocabulary, so structurally absent). The opaque-binary half is **not decided here** unless the pack directory was given and a content scan is wired; otherwise emit a pointer to 16's scan, like P4. | pass / fail |
| **P6** | `version` matches the SemVer pattern (advisory). A miss is `warn`, never `fail`. | pass / warn |

**Pack verdict:** conformant iff P1, P2, P3a, P4, P5 are `pass`, and P3b is `pass` or `not-run`. P6 is advisory and never gates.

## Team mode: the per-check algorithm

The checker does not watch the team work. It verifies the team's `.adlc/conformance.yaml` is **complete, internally valid, and backed by resolvable evidence**. For an **attest** or **audit** check it cannot decide the truth, only that the claim and its evidence are present.

1. Parse `.adlc/conformance.yaml`. Exit `2` if unparseable.
2. Read `level`. Look up its required check IDs from the bundled level table above.
3. For each required check: it MUST be present; its `status` MUST be `pass` (or `warn`/`n/a` with a `reason` for advisory/exempt checks); its `evidence` MUST resolve (a local path that exists, or a syntactically valid URL).
4. The verdict reports the highest level whose required checks all hold. Because Core's checks are all `attest`/`audit`, a Core (or Governed) team verdict is labeled **"attested, not machine-proven"**: the checker confirms the declaration and evidence exist, it does not certify the practice happened.

## Harness mode: the probe contract

Harness checks need a running adapter. The checker defines the probes; the harness answers them through a fixture or test endpoint.

- **H2 (honor):** drive a scripted outward action. PASS iff the harness pauses for approval AND surfaces the payload/destination before approval is possible.
- **H3-intool (enforce):** drive an outward action in unattended mode. PASS iff hard-denied without pre-approval.
- **H3-external:** if H3-intool is `n/a`, the operator supplies a denial log from the external control; recorded as `audit` evidence (the checker cannot self-test an out-of-band control).
- **H4 (load):** point the adapter at the example pack. PASS iff it loads without error.
- **H5 (exempt not gated):** drive a local read, a local edit, a local test. PASS iff none prompts for approval.
- **H1 (derived):** PASS iff H2, H3 (intool or external), H4, and H5 PASS.

## Exit codes

The terminal state maps to an exit code, the same way across subjects:

| Terminal state | Exit |
|---|---|
| All required checks `pass` (auto), or `pass`/`warn`/`not-run` where allowed | `0` conformant at the claimed/detected level |
| Any required non-advisory check `fail`, or required evidence does not resolve | `1` not conformant |
| A team/Core verdict that rests on `attest`/`audit` checks | `0`, but the report is flagged **attested, not machine-proven** (the exit is success because the declaration + evidence hold; the flag tells a reader it was not machine-decided) |
| Bad path, unparseable manifest, unknown subject | `2` usage/input error |

## The report

One JSON shape across all three subjects, so CI can gate on it:

```json
{
  "spec": "0.1",
  "checker": "0.1",
  "subject": "pack",
  "target": "web-e2e-testing@1.2.0",
  "checks": [
    { "id": "P1", "status": "pass", "provenance": "auto", "note": "schema-valid" },
    { "id": "P3b", "status": "not-run", "provenance": "auto", "note": "no eval runner declared" },
    { "id": "P6", "status": "warn", "provenance": "auto", "note": "version not SemVer" }
  ],
  "verdict": "conformant",
  "level": "core",
  "attested": false,
  "exitCode": 0
}
```

Value domains: `status` in `pass | fail | warn | n/a | not-run`; `provenance` in `auto | audit | attest`; `verdict` in `conformant | not-conformant | error`; `attested` is true when the verdict rests on any attest/audit check.

The human form is the same content, one line per check.

## CI usage

The checker is the gate, the way CommonMark's runner and the JSON Schema suite gate implementations.

- Pack repos: `adlc-check pack ./PACK.json` on every PR; block merge on exit `1`.
- Team repos: `adlc-check team .` on a schedule or pre-release; surface the achieved level and the attested flag.
- Harness projects: run the harness probes in the adapter's test suite.

## Honest limits

- **It runs the auto checks; it records the rest.** Audit and attest checks are surfaced with their evidence pointers and provenance, not decided. A `pass` that is attest/audit carries the `attested` flag.
- **It checks declarations, not behavior.** P4's behavior-match and P5's opaque-binary half need the certification program's enforcement spec scan; the checker emits a pointer unless a content scan is wired in.
- **It is versioned with the spec.** Checker 0.1 checks against spec 0.1; the bundled tables and schema move together, so a stale checker cannot silently pass a newer pack.
- **This is the contract, not yet the code.** A reference implementation is the build that follows this spec; keeping it owned and current is the commitment that keeps "conformant" meaningful.
