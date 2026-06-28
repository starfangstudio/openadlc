<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
# OSS license scan: reference tables

Companion to `skills/oss-license-scan/SKILL.md`. Contains the category tables
and scanner quick-ref that keep the skill body under 150 lines.

---

## License category table

| Category | Representative SPDX IDs | Closed-app risk |
|---|---|---|
| Permissive | MIT, BSD-2-Clause, BSD-3-Clause, Apache-2.0, ISC, Zlib | Low. Attribution notice required in the binary/docs. |
| Weak copyleft (file/library scope) | LGPL-2.1-only, LGPL-2.1-or-later, LGPL-3.0-only, MPL-2.0 | Medium. LGPL: dynamic-linking is generally safe; static-linking or modifying the library triggers source-disclosure. MPL: file-scope copyleft only. Confirm with counsel. |
| Strong copyleft (work scope) | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0-only, GPL-3.0-or-later | High. Linking a GPL library into a closed app is a compliance breach. Source of the whole combined work must be offered. |
| Network copyleft | AGPL-3.0-only, AGPL-3.0-or-later | Very high for SaaS/backend; same as GPL for app binaries. Network use triggers source-disclosure. |
| Source-available / non-commercial | BUSL-1.1, CC-BY-NC-*, SSPL-1.0 | Varies. BUSL has a time-limited change date; commercial production use may be restricted until then. |
| No license / unlicensed | (none declared) | Stop. No license = all-rights-reserved by default. Do not ship. Flag for legal review. |
| Dual-licensed | e.g. GPL-2.0-or-later OR commercial | Check which grant applies. Commercial license must be in place before shipping a closed product. |

---

## Attribution notice requirements

Permissive licenses (MIT, BSD, Apache-2.0, ISC) require the copyright notice to
be reproduced in the distributed product. Typical delivery mechanisms:

- Mobile app: an "Open Source Licenses" screen reachable from Settings/About.
- Desktop/CLI: a `NOTICES` or `THIRD_PARTY_NOTICES.txt` file shipped with the binary.
- Web/backend: served at a well-known path (e.g. `/oss-licenses`) or included in
  the distributed package.

Apache-2.0 additionally requires including the `NOTICE` file from each dependency
that ships one. Automate this with the scanner's notice-generation flag rather
than maintaining it by hand.

---

## Scanner quick-reference

| Ecosystem | Scanner | Command / flag | Notes |
|---|---|---|---|
| npm / Node | `license-checker-rseidelsohn` | `npx license-checker-rseidelsohn --production --onlyAllow "MIT;BSD-2-Clause;BSD-3-Clause;Apache-2.0;ISC"` | `--production` skips dev deps; use `--excludePrivatePackages` for monorepos. |
| Gradle (Android) | `jk1/Gradle-License-Report` plugin | `./gradlew generateLicenseReport` (output: `build/reports/licenses/`) | Add `allowedLicenses.json` to fail CI on copyleft; see plugin README. |
| SPM (iOS) | ORT (OSS Review Toolkit) | `ort analyze -i . -o ort-result/`; then `ort report` | ORT parses `Package.resolved`; set `--package-managers SPM`. |
| Unity (UPM) | `pivotal/LicenseFinder` | `license_finder --decisions_file decisions.yml` | Supports npm (UPM registry), Gradle (Android export), and SPM (iOS export) in one pass. |
| Multi-ecosystem | ORT | `ort analyze + ort scan + ort report` | Best SBOM output (CycloneDX / SPDX JSON); preferred for M&A-grade audits. |

---

## SBOM formats

- **SPDX JSON / tag-value** (ISO/IEC 5962:2021): preferred for EU supply-chain and
  EU Cyber Resilience Act (CRA) readiness. ORT outputs this natively.
- **CycloneDX** (ECMA-424): preferred by many SBOM toolchains and vulnerability
  correlators. ORT and `license_finder` both support it.

Generate the SBOM from the scanner's output rather than hand-authoring. Store it
under version control alongside the release artifact.

---

## LGPL dynamic vs. static linking: the key distinction

LGPL-2.1 and LGPL-3.0 permit use in a proprietary application when the library is
**dynamically linked** (loaded at runtime as a separate .so / .dylib / .dll) AND
the user can replace the library with a compatible version. Static linking or
in-process modification of the library source typically triggers the LGPL's
requirement to publish at least the object files of the proprietary portions.

- Android: bundling a `.so` via `jniLibs` is effectively dynamic; statically
  linking via `ndk-build` or CMake `add_library(STATIC)` is not.
- iOS: the App Store forbids dynamic frameworks from third parties for non-system
  dylibs; almost all LGPL iOS integrations are static. This creates a potential
  compliance issue. Confirm with counsel before shipping LGPL on iOS.
- This is a legal call, not a pure engineering call. Flag it; do not assert compliance.

---

## Loot-box / F2P out-of-scope note

License obligations are distinct from loot-box law or COPPA obligations. Those
are covered by the privacy and F2P-compliance skills, not by this skill.

---

## Jurisdiction note

OSS license compliance is governed by copyright law, which varies by jurisdiction.
The EU, US, and other regions have different enforcement histories. This reference
is engineering guidance, not legal advice. Confirm material copyleft findings with
counsel before shipping.
