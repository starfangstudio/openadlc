---
name: oss-license-scan
description: >-
  This skill should be used when the user asks to "audit OSS licenses", "scan
  dependency licenses", "check for copyleft in our dependencies", "do we have
  any GPL libraries?", "check LGPL linking rules", "generate an SBOM",
  "produce a software bill of materials", "check attribution notices",
  "are our open-source attributions correct?", "do we need to ship a NOTICES
  file?", "scan for license compliance before release", "flag any copyleft
  traps", "check if we can ship this library commercially", "check our
  transitive deps for license issues", or "run a license report". Covers
  detecting dependency manifests (SPM/Gradle/npm/UPM), scanning transitive
  deps for SPDX-identified licenses, flagging copyleft traps (GPL/AGPL in a
  closed app, LGPL static-linking constraints), attribution notice delivery,
  and SBOM generation. Produces a pass/fail license report with no unresolved
  copyleft. Legal calls are flagged; never asserts a definitive legal conclusion.
version: 0.1.0
---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# OSS license scan

Audit every shipped dependency's license, flag copyleft traps before they
reach production, and produce an SBOM. This is engineering for compliance,
not legal advice: flag material findings for counsel rather than resolving
them unilaterally.

## Detect first

Identify which package ecosystems are present before running any scanner:

```bash
# Android / Gradle
find . -name "build.gradle" -o -name "build.gradle.kts" \
       -o -name "libs.versions.toml" | head -20

# iOS / SPM
find . -name "Package.swift" -o -name "Package.resolved" | head -10

# npm / Node / UPM (Unity uses npm registry)
find . -name "package.json" -not -path "*/node_modules/*" | head -10

# Unity (UPM manifest)
find . -name "manifest.json" -path "*/Packages/*" | head -5
```

Mark any ecosystem where the lockfile is missing as `unknown`; a lockfile
is required to enumerate transitive deps accurately. Never guess license
coverage from direct deps alone.

## Step 1: scan transitive dependencies

Run the scanner appropriate to each detected ecosystem. For exact commands
(Gradle, npm/UPM, SPM via ORT, LicenseFinder multi-ecosystem), see
[references/oss-license-scan-detail.md](references/oss-license-scan-detail.md) (Step 1 section).
The scanner quick-reference table is in
[references/oss-license-scan.md](references/oss-license-scan.md).

## Step 2: triage by category

Classify each detected license using the category table in
[references/oss-license-scan.md](references/oss-license-scan.md). Flag:

- **BLOCK -- strong copyleft in a closed app:** any `GPL-*` or `AGPL-*` dep
  linked into a proprietary binary. Stop; do not ship without legal sign-off
  or replacing the dep.
- **REVIEW -- weak copyleft:** any `LGPL-*` or `MPL-*` dep. Check static vs.
  dynamic linking (see reference file). iOS LGPL is almost always static:
  flag for counsel, do not assert compliance.
- **REVIEW -- no license declared:** treat as all-rights-reserved. Do not ship.
  Flag for legal review.
- **REVIEW -- dual-licensed or BUSL:** confirm which grant covers commercial use
  and whether a commercial license is in place.
- **OK -- permissive:** MIT, BSD-*, Apache-2.0, ISC, Zlib. Proceed to Step 3.

## Step 3: attribution notices

For every permissive dep, confirm the attribution notice will be delivered
with the binary:

- Mobile: an "Open Source Licenses" screen reachable from Settings/About.
- Desktop/CLI: a `NOTICES` or `THIRD_PARTY_NOTICES.txt` file in the package.
- Apache-2.0: include each dep's `NOTICE` file verbatim.

Automate notice generation from the scanner's output rather than maintaining
the file manually. Gradle-License-Report, ORT, and LicenseFinder all have
notice-generation modes.

## Step 4: generate the SBOM

Produce an SBOM in SPDX JSON (preferred for EU CRA readiness) or CycloneDX.
For exact ORT and LicenseFinder commands, see
[references/oss-license-scan-detail.md](references/oss-license-scan-detail.md) (Step 4 section)
and the SBOM formats section in
[references/oss-license-scan.md](references/oss-license-scan.md).
Store the SBOM under version control alongside the release artifact.

## Verify: pass/fail checklist

Run before every release build. Call the audit complete only when every box
is PASS or has an explicit, documented resolution:

```
[ ] All ecosystems have a lockfile; no ecosystem marked unknown
[ ] Scanner ran over transitive deps (not just direct deps)
[ ] Zero GPL/AGPL deps in any closed-app binary -- PASS or BLOCK documented
[ ] All LGPL/MPL deps reviewed for static-linking risk -- PASS or REVIEW logged
[ ] All unlicensed / no-license deps flagged for legal review
[ ] Dual-licensed and BUSL deps have documented commercial grant in place
[ ] Attribution notices generated and wired into the UI/package
[ ] Apache-2.0 NOTICE files included
[ ] SBOM committed alongside the release artifact
```

Any BLOCK or unresolved REVIEW must be escalated to counsel before shipping.
Do not resolve a copyleft finding unilaterally by marking it "probably fine".

## Outbound: get the operator's yes first

Local work is fine to do without asking. Outbound here (submitting an app binary that includes a newly confirmed copyleft dep, publishing the SBOM to a public registry, responding to a third-party license inquiry on behalf of the project): stop, present exactly what would go out, and get the operator's explicit "yes" first.

## References

- [references/oss-license-scan.md](references/oss-license-scan.md) -- license category
  table, LGPL linking rules, scanner quick-reference, SBOM formats.
- [references/oss-license-scan-detail.md](references/oss-license-scan-detail.md) -- scanner
  commands (Step 1) and SBOM generation commands (Step 4).
- SPDX License List (v3.28, Feb 2026): https://spdx.org/licenses/
- OSS Review Toolkit (ORT): https://oss-review-toolkit.github.io/ort/
- jk1/Gradle-License-Report: https://github.com/jk1/Gradle-License-Report
- license-checker-rseidelsohn (npm): https://www.npmjs.com/package/license-checker-rseidelsohn
- LicenseFinder (multi-ecosystem): https://github.com/pivotal/LicenseFinder
- OSI: copyleft license taxonomy: https://opensource.org/licenses/category
