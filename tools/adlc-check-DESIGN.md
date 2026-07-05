<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# adlc-check: design

> One line: the buildable design for `tools/adlc-check.py`, the owned reference checker that runs the **auto** checks in [conformance.md](../standard/conformance.md), records the **audit/attest** ones, and prints the verdict shape from [conformance-checker.md](../standard/conformance-checker.md). Stdlib-only Python, fail-closed.

This is the design the code follows. The authority it is built from is [conformance-checker.md](../standard/conformance-checker.md) (the two bundled tables, the per-check procedures, the report shape, the exit codes). This file adds nothing normative: it decides the concrete CLI, the file layout, what is decided vs pointed-at, and how the stdlib-only constraints (no PyYAML, no jsonschema) are met.

## 1. Scope and the one hard rule

The checker decides what is **mechanically decidable** and never pretends to decide the rest. Two fields, never mixed, on every check: `status` (`pass | fail | warn | n/a | not-run`) and `provenance` (`auto | audit | attest`). An `attest`/`audit` result is reported with its provenance so a reader never reads an attested `pass` as machine-proven.

Fail-closed everywhere: any input the checker cannot parse, any missing bundled asset (the schema file), any subject it does not recognize is exit `2`, not a silent pass.

## 2. CLI shape

```
python3 tools/adlc-check.py <subject> <path> [--json] [--level L] [--quiet]

  subject   pack | team | harness
  path      pack     -> a manifest file (JSON or YAML), or a pack directory
            team     -> a directory containing .adlc/conformance.yaml
            harness  -> a probe-result fixture (JSON or YAML), or an adapter note

  --json    emit the JSON report (section 6) to stdout instead of the human form
  --level   claim a specific level to check against (default: pack/harness = core;
            team = the level declared in the manifest)
  --quiet   suppress the per-check lines in human mode; print only the verdict line
```

Invocation matches the spec's `adlc-check <subject> <path>`; the reference build is a Python entry point. No third-party dependencies, no network, no git. Wrong arg count or unknown subject prints usage and exits `2`.

## 3. What is auto vs pointer-to-program

The checker is deliberately small. The line between "decided here" and "pointed at the certification program" is fixed by the spec, restated here so the code has no room to drift.

| Check | Decided here (auto) | Pointed at the program |
|---|---|---|
| P1 | Validate manifest against `pack-manifest.schema.json`. | none |
| P2 | `units` has at least one per-kind count >= 1. | none |
| P3a | `evals` is `conformance` or `conformance+gate`. | none |
| P3b | Invoke a declared eval runner and read delta vs baseline; no runner -> `not-run`. | eval *quality* (audit) |
| P4 | `capabilities` is schema-valid, only known keys, correct types. | declared-vs-behavior match (behavior scan) |
| P5 | No checkpoint-subverting capability key (none exists in the vocabulary -> structurally absent = pass). Opaque-binary half: scanned only when a pack **directory** is given; else pointer. | prose that coaxes a bypass; opaque-binary when only a manifest file is given |
| P6 | `version` matches SemVer (advisory; miss = `warn`). | none |

Team mode decides nothing about behavior: it confirms each required check is **present**, its `status` is acceptable, and its `evidence` **resolves** (a local path that exists, or a syntactically valid URL). Harness mode records probe results from a fixture (an adapter's test suite is the real prober) and derives H1.

The pointer is a `note` on the check, e.g. `P4 auto half passed; declaration-vs-behavior match is the certification program's scan`. It never changes a `pass` into more than it is.

## 4. The bundled authority (lives in code as constants)

Straight from [conformance-checker.md](../standard/conformance-checker.md). The checker carries these so a stale checker cannot silently pass a newer pack.

**Level -> required check IDs.**

- **pack**: `P1, P2, P3a, P4, P5` required; `P3b` required-if-a-runner-exists (else `not-run`, does not gate); `P6` advisory. Same set at every level.
- **team**: core `T-C1..T-C5`; governed adds `T-G1, T-G2, T-G3`; certified adds `T-X1` (defined, not runnable -> `not-run`).
- **harness**: `H1, H2, H3, H4, H5`. H1 is derived.

**Check -> provenance.**

- **auto**: `T-G1, P1, P2, P3a, P3b, P4, P5, P6, H2, H3-intool, H4, H5`
- **audit**: `T-C2, T-C3, T-C4, T-C5, T-G2, T-G3, H3-external`
- **attest**: `T-C1`

**Verdict per subject.**

- **pack**: conformant iff `P1, P2, P3a, P4, P5` are `pass` and `P3b` is `pass` or `not-run`. P6 never gates.
- **team**: the highest level whose required checks all hold (`pass`, or `warn`/`n/a` with a `reason` for advisory/exempt). If any required non-advisory check is not satisfied, cap at the level below.
- **harness**: conformant iff `H2, H4, H5` pass and (`H3-intool` passes, or `H3-external` is a resolvable `audit` pass). H1 is then `pass`.

**Attested flag.** `attested = true` when the verdict rests on any `attest`/`audit` check. A team at core/governed is always flagged **"attested, not machine-proven"** (all its checks are attest/audit) with exit `0`, because the declaration and evidence hold even though the practice was not machine-decided.

## 5. Per-subject algorithm

### Pack

1. Resolve `path`. If a directory, find the manifest: `.claude-plugin/plugin.json` (the shipped convention), then `pack.json` / `manifest.json` / `*.manifest.json` / `.adlc/pack.yaml`. A directory also arms the P5 content scan. If a file, use it directly.
2. Load it: `json.loads` first, then the mini-YAML loader (section 7). Unparseable -> exit `2`.
3. Run P1 (schema validate), P2, P3a, P3b, P4, P5, P6 per section 4. Set each check's `status`, `provenance: auto`, and a `note`.
4. Compute the pack verdict. `target = name@version` from the manifest.

### Team

1. `path` must be a directory containing `.adlc/conformance.yaml`. Missing or unparseable -> exit `2`.
2. Read `level` (or `--level` override). Look up its required IDs.
3. For each required check: present? `status` acceptable (`pass`, or `warn`/`n/a` with a `reason`)? `evidence` resolves (local path exists, or valid URL)? A miss = that check `fail` and the level is capped below.
4. Verdict = highest satisfied level. Flag `attested` per section 4.

### Harness

1. `path` is a probe-result fixture (JSON/YAML) declaring `H2, H3-intool | H3-external, H4, H5`, produced by the adapter's test suite (the checker defines the probes; it does not drive a live adapter in the reference build).
2. If no fixture is given, the checks are `not-run` with a pointer note ("run the harness probes in the adapter's test suite"); verdict `not-conformant` with exit `1`, because enforcement was not demonstrated.
3. With a fixture: validate the declared probe statuses, derive H1, compute the verdict.

## 6. The report (one shape, all subjects)

Exactly the shape in [conformance-checker.md](../standard/conformance-checker.md):

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

Domains: `status` in `pass|fail|warn|n/a|not-run`; `provenance` in `auto|audit|attest`; `verdict` in `conformant|not-conformant|error`; `attested` true when the verdict rests on any attest/audit check.

**Human form** is the same content, one line per check, then a verdict line:

```
adlc-check pack  web-e2e-testing@1.2.0

  P1    pass    auto    schema-valid
  P2    pass    auto    3 units declared
  P3a   pass    auto    eval bar: conformance
  P3b   not-run auto    no eval runner declared (does not gate)
  P4    pass    auto    capabilities well-formed; behavior match -> cert program scan
  P5    pass    auto    no checkpoint-subverting key; opaque-binary -> cert program scan
  P6    pass    auto    1.2.0

  VERDICT: conformant at level core   (exit 0)
```

`--quiet` prints only the `VERDICT:` line. `--json` prints only the JSON object. Exit codes are identical across output modes.

## 7. Meeting the stdlib-only constraints

Two things a checker normally reaches for a library to do. Both are bounded here, so both are small owned engines.

- **JSON Schema validation (P1).** No `jsonschema`. The checker loads `standard/schema/pack-manifest.schema.json` at runtime and runs a minimal draft-2020-12 validator covering exactly the keywords that schema uses: `type` (with integer-vs-boolean kept distinct), `required`, `additionalProperties: false`, `properties`, `pattern`, `minLength`, `maxLength`, `minimum`, `enum`, `items`. Loading the schema file (not re-coding the rules) keeps the checker and the schema a single source of truth. Missing schema file -> exit `2` (cannot validate = fail-closed).
- **YAML parsing (manifests + `conformance.yaml`).** No `PyYAML`. A small `mini_yaml` loader handles the constrained subset the ADLC formats use: comments, block mappings by indentation, nested maps, flow mappings `{ ... }`, flow sequences `[ ... ]`, block sequences (`- item`), and scalars (bare, single/double quoted, int, bool, null). Anything it cannot represent -> raise -> exit `2` (never a lenient guess). JSON is parsed by `json.loads` first; the loader is the fallback.

## 8. Exit codes

| Terminal state | Exit |
|---|---|
| All required checks satisfied (`pass`, or `warn`/`not-run`/`n/a` where allowed) | `0` conformant |
| Any required non-advisory check `fail`, or required evidence does not resolve | `1` not conformant |
| Team/Core verdict resting on attest/audit checks | `0`, report flagged **attested, not machine-proven** |
| Bad path, unparseable manifest/YAML, unknown subject, missing schema | `2` usage/input error |

## 9. File layout of the implementation

Single file, `tools/adlc-check.py`, stdlib-only, sectioned:

1. Constants: spec/checker version, level->checks, provenance map, verdict rules, license vocabulary.
2. `mini_yaml_load(text)` and `load_data(text)` (JSON-then-YAML).
3. `validate(instance, schema)` -> list of error strings (the draft-2020-12 subset).
4. `check_pack`, `check_team`, `check_harness` -> a list of check dicts + verdict + level + attested.
5. `render_human` / `render_json`.
6. `main`: parse args, dispatch, print, exit with the code.

The checker does not import from or modify `check-packs.py`; the two are independent. `check-packs.py` stays the per-pack **structural** eval (house conventions, em-dash ban, frontmatter); `adlc-check.py` is the **conformance** checker (P1-P6 against the standard). They overlap only in that both validate the manifest shape, and both must agree the 18 shipped packs are well-formed.

## 10. Test plan (Firing 4 will execute)

- **Must pass**: all 18 shipped packs (`plugins/*/.claude-plugin/plugin.json`) as `adlc-check pack <dir>` and as `adlc-check pack <manifest>`.
- **Must fail (exit 1)**: `standard/schema/example-pack-invalid.manifest.json` (P1 fails: `units` is an array, `evals` is an object, `description` over 600).
- **Must pass**: `standard/schema/example-pack.manifest.json`.
- **Self-test**: a `--selftest` path (or a sibling assertion in the harness) that runs both example manifests and asserts valid->0, invalid->1, plus the content scan does not false-positive on the packs' `.md`/`.json`/dotfiles (`.DS_Store` is a dotfile and is ignored).
- **Team**: a fixture `.adlc/conformance.yaml` (core + governed) -> conformant, flagged attested.
- **Harness**: a fixture with all probes `pass` -> conformant; a missing/failing H3 -> not-conformant.

## 11. Status

Design complete (Firing 1). Implementation of `tools/adlc-check.py` follows in Firings 2-3; hardening, `--json`, full self-test, and the doc updates (this checker's status line in `conformance-checker.md`, `tools/README.md`) in Firing 4.
