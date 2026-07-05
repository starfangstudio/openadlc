<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
# tools

OpenADLC checks, run in CI before a pack is certified.

- **`adlc-check.py`**: the owned reference conformance checker the standard commits to ([standard/conformance-checker.md](../standard/conformance-checker.md)). Fail-closed, stdlib-only. `python3 tools/adlc-check.py <pack|team|harness> <path> [--json] [--level L] [--quiet]`. It runs the **auto** checks (pack P1-P6), records the team and harness declarations with their provenance (`auto`/`audit`/`attest`), and prints one verdict report shape across all three subjects. Exit `0` conformant, `1` not conformant, `2` usage/input error. `--json` emits the machine report; `--selftest` runs it against both example manifests and every shipped pack. Design: [tools/adlc-check-DESIGN.md](adlc-check-DESIGN.md).
- **`check-packs.py`**: the structural conformance eval (the per-pack cert bar). Fail-closed. `python3 tools/check-packs.py [pack | all]`. Hard-fails on em-dashes, missing/invalid frontmatter, a skill name not matching its directory, or an invalid / incomplete manifest; warns on missing version, no References section, no failable check mentioned, or an over-length skill. Guidance skills are not behaviorally fixture-testable, so structure + the house conventions are the bar.

`adlc-check.py` checks a pack against the **standard** (the P1-P6 conformance procedures); `check-packs.py` checks the shipped packs against the **house conventions** (frontmatter, naming, the em-dash ban). They are independent and overlap only in validating the manifest shape.
