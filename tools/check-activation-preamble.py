#!/usr/bin/env python3
# SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0
"""Domain-activation preamble check (dev-time test, not pack runtime).

Proves the S-A2 activation preamble is present, consistently, in all four
runtime commands: each of plugins/adlc-core/commands/ai-{discovery,plan,
implement,review}.md must carry a `## 0. Domain activation` section that
names all three rails (the mandatory floor, ambiguity-includes, and the
audit log), and the command's pipeline must start numbering at step 0.

This is a dev-time consistency check (like check-packs.py / check-domains.py),
not something a pack ships or a command runs: the four commands follow the
declarative `## 0.` section directly, this script only proves it is there
and says what it must say.

Usage: python3 tools/check-activation-preamble.py
Exit 0 pass, 1 fail (a command is missing the section, a rail, or the 0-start
pipeline marker), 2 no command files found (fail-closed).
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COMMANDS_DIR = os.path.join(ROOT, "plugins", "adlc-core", "commands")

COMMANDS = ["ai-discovery.md", "ai-plan.md", "ai-implement.md", "ai-review.md"]

SECTION_HEADING = "## 0. Domain activation"

# The three rails, each pinned to a literal marker the preamble must contain.
RAILS = {
    "mandatory floor": "MANDATORY FLOOR",
    "ambiguity -> include": "AMBIGUITY -> INCLUDE",
    "audit log": "**AUDIT:**",
}

# Load-bearing rail CONTENT, not just the marker: a future edit that keeps the
# marker but blurs the semantics (fail-open a gate, overwrite the stage-1
# section, or let a policy drop a floor member) must still fail this check.
CONTENT = {
    "gates never fail open (rail 2 is activation-only)": "never fail open",
    "audit appends, never overwrites stage-1": "never overwrite the stage-1",
    "a policy can never drop a floor member (stage-0 security boundary)": "drop a floor member",
}

# Every command's activation flow starts numbering at step 0: either a
# `## Pipeline` arrow line beginning "0." (ai-plan, ai-implement, ai-review),
# or, where there is no arrow-line overview (ai-discovery), the numbered
# section flow itself starting at `## 0.` before `## 1.`.
ZERO_START = re.compile(r"^## Pipeline\n0\.", re.M)


def check_file(name):
    path = os.path.join(COMMANDS_DIR, name)
    if not os.path.isfile(path):
        return [f"{name}: file not found"]
    text = open(path, encoding="utf-8").read()
    failures = []

    if SECTION_HEADING not in text:
        failures.append(f"{name}: missing '{SECTION_HEADING}' section")
        return failures  # nothing else to check meaningfully

    for rail_name, marker in RAILS.items():
        if marker not in text:
            failures.append(f"{name}: missing rail '{rail_name}' (expected marker {marker!r})")

    for content_name, needle in CONTENT.items():
        if needle not in text:
            failures.append(f"{name}: missing rail content '{content_name}' (expected phrase {needle!r})")

    has_pipeline_zero = bool(ZERO_START.search(text))
    has_zero_before_one = bool(re.search(r"^## 0\. Domain activation", text, re.M)) and bool(
        re.search(r"^## 1\.", text, re.M)
    )
    if not (has_pipeline_zero or has_zero_before_one):
        failures.append(f"{name}: numbering does not start at step 0 (no '## Pipeline' arrow line starting '0.', and no '## 0.' before '## 1.')")

    return failures


def main():
    if not os.path.isdir(COMMANDS_DIR):
        print(f"FAIL-CLOSED: commands dir not found: {COMMANDS_DIR}")
        return 2

    all_failures = []
    for name in COMMANDS:
        fails = check_file(name)
        status = "PASS" if not fails else "FAIL"
        print(f"{name}: {status}")
        for f in fails:
            print(f"  - {f}")
        all_failures.extend(fails)

    if all_failures:
        print(f"\nRESULT: FAIL ({len(all_failures)} issue(s))")
        return 1

    print("\nRESULT: PASS (all four commands carry the '## 0. Domain activation' section, all three rails, and 0-start numbering)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
