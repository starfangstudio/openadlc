<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
# tools

OpenADLC checks, run in CI before a pack is certified.

- **`check-packs.py`**: the structural conformance eval (the per-pack cert bar, G3). Fail-closed. `python3 tools/check-packs.py [pack | all]`. Hard-fails on em-dashes, missing/invalid frontmatter, a skill name not matching its directory, or an invalid / incomplete manifest; warns on missing version, no References section, no failable check mentioned, or an over-length skill. Guidance skills are not behaviorally fixture-testable, so structure + the house conventions are the bar.
