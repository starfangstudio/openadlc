<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
# Changelog

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Versioning follows [SemVer](https://semver.org/).

## [1.0.0] - 2026-07-06

Initial public release, version 1.0. This 1.0 is the stable baseline; the version does not bump again until the production release.

### Renamed
- Commands renamed: `agentic-intake` -> `ai-discovery`, `agentic-plan` -> `ai-plan`, `agentic-implement` -> `ai-implement`, `agentic-review` -> `ai-review`.

### The lifecycle
- Four commands, one per human decision point: `/ai-discovery`, `/ai-plan`, `/ai-implement`, `/ai-review`.
- A human checkpoint at every outbound boundary: the agent presents what would leave the machine (post, push, publish) and waits for an explicit yes. Reading and local work are never stopped.
- Every intake and plan artifact is an [OKF](https://github.com/GoogleCloudPlatform/knowledge-catalog/tree/main/okf) bundle: a human briefing plus the full AI context as typed markdown, carried between stages and trackers (inline on GitHub, attached elsewhere).

### Packs
- The always-on `adlc-core` spine plus domain packs: web, iOS, Android, backend, backend-cloud, database, AI, design, security, testing, ops, privacy, monetization, desktop, Unity, planning, and quality-gates.
- Packs ship as Agent Skills that install and run as plain files, with or without a package manager.

### The standard
- The ADLC standard (the `standard/` tree): the spec, principles, manifesto, conformance criteria, and pack format, under CC-BY-4.0.

### Install
- Runs across APM-supported harnesses: `apm install starfangstudio/openadlc`.

### Licensing and governance
- Dual license: the standard under CC-BY-4.0; the implementation under the OpenADLC Source-Available License (free for individuals, a commercial seat for organizations).
- Contributions are covered by a Contributor License Agreement, checked on every pull request.
- Conformance tooling and CI; community docs (contributing, security, code of conduct, support); brand and trademark policy; privacy notice; the brand mark.
