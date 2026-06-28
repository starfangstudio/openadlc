<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# The ADLC Pack Format

> Status: draft proposal, pre-ratification. For spec version 0.1.
> One line: the vendor-neutral wire format and capability vocabulary for an ADLC pack, so a pack written once validates and travels everywhere.

[spec.md](spec.md) section 5 fixes the pack *shape* (manifest + units + evals + capability declaration) and leaves the wire format for later. This is later. It defines the concrete manifest fields, the capability vocabulary, and the bans, backed by a real machine-checkable schema.

- Schema: [schema/pack-manifest.schema.json](schema/pack-manifest.schema.json) (JSON Schema, draft 2020-12)
- Valid example: [schema/example-pack.manifest.json](schema/example-pack.manifest.json)
- Invalid example (proves the schema rejects malformed packs): [schema/example-pack-invalid.manifest.json](schema/example-pack-invalid.manifest.json)

## The manifest

A pack carries one manifest. It MAY be written as JSON or YAML (they map one-to-one); the schema validates the JSON form. Required fields make a pack *conformant* (spec section 5); an experimental pack MAY omit `evals` but is then not conformant.

| Field | Type | Required | Meaning |
|---|---|---|---|
| `name` | string, kebab-case, 1-64 chars | yes | The pack's name. |
| `version` | string, SemVer 2.0.0 | yes | The version. Pattern is the official SemVer regex. |
| `description` | string, 1-200 chars (one line) | yes | What it does and when it applies. |
| `owner` | object {name, contact} | yes | Who maintains it and how to reach them. Currency (Law L3) needs an owner. |
| `adlc` | string (e.g. "0.1") | yes | The spec version the pack targets (spec 5.1). |
| `units` | array, >= 1 | yes | The guidance units: each `{kind, id, path?}`, kind in skill / agent / rule / reference. |
| `evals` | object {path, baseline} | yes (for conformant) | Where the evals live and the no-pack baseline they beat (Law L5). |
| `capabilities` | object | yes | The default-deny capability declaration (below). |
| `harness` | array | no | Informational target harness(es). Omit for a pure-content pack. The standard never requires one (Law L7). |
| `depends` | array | no | Other packs this builds on. |
| `license` | string | yes | A per-pack license identifier (an SPDX id or an SPDX `LicenseRef-`), so each pack states its own terms (a CC-BY pack and a source-available commercial pack travel side by side). Required and validated by the checker. The official OpenADLC packs use `LicenseRef-OpenADLC-Source-Available-1.0` (source-available + commercial, see the `LICENSE` file); standard content uses `CC-BY-4.0`. See the [license notice](README.md#license). |

## The capability vocabulary

What a pack may declare it can touch. It is **default-deny**: an omitted key means the pack does not take that capability. A declared capability MUST match actual behavior (spec 5.4); proving that match is the certification scan's job (below), not the manifest's.

| Key | Value | Declares | Default |
|---|---|---|---|
| `exec` | list of named commands | Scoped commands it runs (`npm run lint`, `./gradlew test`). | none |
| `exec-installer` | boolean | Runs dependency installers that execute arbitrary upstream code (`npm install`, `pip install`). | false |
| `exec-broad` | boolean | Runs a general shell or arbitrary commands (`bash`, `python -c`). Expressible, but high-risk and tier-gated (below). | false |
| `network` | list of hosts | Scoped allowlist of named hosts (no wildcards). | none |
| `network-broad` | boolean | Reaches arbitrary or wildcard hosts. Expressible, but high-risk and tier-gated. | false |
| `fs-read` | list of path scopes | Where it reads. | workspace |
| `fs-write` | list of path scopes | Where it writes. | none |
| `env` | list of names | Environment variables or secrets it reads. | none |
| `subprocess` | boolean | Spawns long-running processes or daemons. | false |

## Two integrity bans, and how breadth is handled

The format has exactly two hard, all-context MUST-NOTs. They protect the integrity of the standard itself, and they are banned in every trust tier (so the certification program agrees, never disagrees):

- **No subverting the checkpoints.** A pack MUST NOT read or modify the configuration of any human-in-the-loop checkpoint, including the consent checkpoint. There is no capability key for this; it is forbidden, full stop. The whole standard rests on keeping a human in control.
- **No opaque executables.** A pack MUST NOT ship a bundled binary without source. You cannot review what you cannot read.

Both are behavioral, not declarational: a manifest cannot "declare" checkpoint-subverting or a hidden binary into legitimacy. Catching them needs a scan of the pack's content, which is the certification program's job (below).

**Breadth is expressible, not banned.** A general shell (`exec-broad`) or a wildcard host (`network-broad`) is a real need for some packs, so the format lets you declare it. What the format does is make breadth **visible and explicit**: a pack that can run anything MUST set `exec-broad: true` rather than hiding `bash` in the scoped `exec` list, and the scoped `exec`/`network` lists stay narrow by construction (the schema rejects a wildcard in the scoped `network` list). Whether a given tier *admits* a broad capability is policy, owned by the certification program, not the format. This is the fix for an earlier contradiction: the format used to forbid breadth outright, which clashed with the program allowing it (with justification) in the Certified tier. The format defines and surfaces; the program decides.

## The same manifest in YAML

The valid example, rendered as YAML for human eyes (identical content to the JSON):

```yaml
name: web-e2e-testing
version: 1.2.0
description: >-
  End-to-end web testing golden path: Playwright setup, page-object
  structure, and flake-resistant assertions.
owner: { name: Jane Dev, contact: jane@example.com }
adlc: "0.1"
units:
  - { kind: skill, id: write-e2e-test, path: skills/write-e2e-test.md }
  - { kind: reference, id: playwright-patterns, path: references/playwright-patterns.md }
  - { kind: rule, id: no-hardcoded-waits, path: rules/no-hardcoded-waits.md }
evals:
  path: evals/e2e.json
  baseline: "no-pack agent on the same 12 tasks: 5/12 stable vs 11/12 with the pack"
capabilities:
  exec: [npx playwright test, npm run lint]   # e.g.; any ecosystem: ./gradlew test, cargo build, go test
  exec-installer: false
  fs-read: [./, ./src, ./tests]
  fs-write: [./test-results, ./playwright-report]
  subprocess: true
harness: [claude-code, codex]   # any harness id; examples only, not a closed set
depends: [web-core]
```

## Reconciliation with the certification program

There is a clean split, and stating it keeps the two from contradicting:

- **The standard owns the format contract.** This file and the schema define what a pack manifest *is*: the fields, the capability vocabulary, the two integrity bans. Every ADLC pack uses it.
- **The certification program owns the operations.** the certification program's capability model decides, per capability, what is allowed automatically, what escalates to human review, and what is banned for a given trust tier, plus the scan that checks declaration-against-behavior (the certification program's enforcement spec). That is policy and process, not format.

A certification submission is **this manifest plus the program's extra fields** (`tier-requested`, `domain`, `fills-gap`). The standard defines the base; the program extends it. The full crosswalk against 16's capability classes:

| 16 capability class | This format | Owner / agreement |
|---|---|---|
| `markdown-only` | all `capabilities` empty (the default) | standard (shape) |
| `fs-read` / `fs-write` | `fs-read` / `fs-write` | standard defines; 16 gates the scope |
| `exec-task-runner` | `exec` (named commands) | standard defines; 16 gates |
| `exec-installer` | `exec-installer: true` | standard defines; 16 gates |
| `network` (allowlist) | `network` (scoped hosts) | standard defines; 16 gates |
| `subprocess` | `subprocess: true` | standard defines; 16 gates |
| `env`/secrets | `env` | standard defines the key; **16 bans it at Community, REVIEW at Certified** |
| broad `exec` | `exec-broad: true` | **expressible in format; tier-gated by 16** (banned open, review+justification certified) |
| wildcard `network` | `network-broad: true` | **expressible in format; tier-gated by 16** (banned open, review+justification certified) |
| checkpoint config touch | no key; integrity ban | **banned by format AND program; the two MUST agree (banned in all tiers)** |
| opaque binary | no key; integrity ban | **banned by format AND program; the two MUST agree (banned in all tiers)** |
| network exfil-shaped (POST to unknown host) | not declarable; caught by behavior scan | program (scan); banned in all tiers by 16 |
| tier gating (auto / review / ban per class) | n/a | program (operations) |
| declaration-vs-behavior scan | n/a | program (operations) |

Authority rule: if the format and 16 disagree on the *vocabulary*, this file wins (it is the standard). If they disagree on *what a tier admits*, 16 wins (it is the program). The two integrity bans are the one place both must say the same thing: banned everywhere.

## How it is validated, and the honest limit

The manifest is machine-checkable: any JSON Schema validator runs the schema against a manifest and returns pass/fail. The repo ships a local check that validates both examples (the valid one passes; the invalid one fails on every seeded violation: empty `version`, missing `owner.contact`, empty `units`, missing `evals`, an unknown capability key, and a wildcard in the scoped `network` list). The same check runs in [CI](../.github/workflows/ci.yml).

The honest limit is the same one every capability system has: **the schema checks the declaration, not the behavior.** It proves a manifest is well-formed and free of banned declarations. It cannot prove the pack only does what it declared. Closing that gap (scan the code, compare to the declaration, enforce at runtime) is the certification program's job, specified in the certification program's enforcement spec. The format makes the honest declaration possible and checkable; it does not make it true.
