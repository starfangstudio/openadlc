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

B-177: presence of a marker phrase is not enough, a rewrite could keep the
marker while adding an INVERTED sentence elsewhere (same rail, flipped
polarity, e.g. "the floor is subject to ask-scoping" or "gates MAY fail
open"). `_check_direction` asserts the correct DIRECTION for the three rails
plus the floor-boundary: the negation word must sit in the same clause as the
trigger phrase, and a few banned literal inversions are rejected outright.

Usage: python3 tools/check-activation-preamble.py
Exit 0 pass, 1 fail (a command is missing the section, a rail, a rail's
direction, or the 0-start pipeline marker), 2 no command files found
(fail-closed).
"""
import bisect
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

# B-177: the checks above are SUBSTRING-presence only, so an edit that KEEPS
# the marker phrase intact somewhere in the file but ADDS an inverted
# sentence elsewhere (same meaning-bearing words, flipped polarity, e.g. "the
# floor is subject to ask-scoping" or "gates MAY fail open") still passes.
# DIRECTION_TRIGGERS asserts the correct polarity: every occurrence of the
# trigger phrase must have the negation word in the SAME CLAUSE (bounded by
# the nearest preceding '.'/':'), not just present somewhere in the file.
DIRECTION_TRIGGERS = [
    ("rail 1 (floor): 'model-optional' must always be negated", "model-optional", "never"),
    ("rail 3 (audit): 'overwrite the stage-1' must always be negated", "overwrite the stage-1", "never"),
    ("floor-boundary: 'drop a floor member' must always be negated", "drop a floor member", "never"),
]

# Rail 2 (gates): "fail open" alone is ambiguous ("activation fails OPEN" is
# the CORRECT, un-negated rail-2 behavior). Only flag a "fail open" occurrence
# that is talking about GATES specifically (the mandatory-never-fail-open
# rail), by requiring "gate(s)" in the same clause before requiring the
# negation too.

# A banned literal rewrite of the floor/stage-2 relationship: the rail states
# the floor is INDEPENDENT of stage-2 ask-scoping. A rewrite to the opposite
# claim keeps no negatable trigger word, so it needs its own banned phrase.
BANNED_PHRASES = {
    "floor stated as subject to (rather than independent of) ask-scoping": "subject to ask-scoping",
}

# Every command's activation flow starts numbering at step 0: either a
# `## Pipeline` arrow line beginning "0." (ai-plan, ai-implement, ai-review),
# or, where there is no arrow-line overview (ai-discovery), the numbered
# section flow itself starting at `## 0.` before `## 1.`.
ZERO_START = re.compile(r"^## Pipeline\n0\.", re.M)


# Any '.' or ':' followed by whitespace ends a clause. Used to bound the
# "same clause" window so a negation from a PRIOR sentence (e.g. the correct
# "which never fail open" clause) never leaks into the window checked for a
# later, separately-added inverted sentence.
CLAUSE_BOUNDARY = re.compile(r"[.:]\s")


def _clause_starts(lower):
    """Sorted list of clause-start offsets in `lower` (0, plus one right
    after every clause boundary), for a bisect lookup per trigger match."""
    return [0] + [m.end() for m in CLAUSE_BOUNDARY.finditer(lower)]


def _clause_start_for(starts, pos):
    i = bisect.bisect_right(starts, pos) - 1
    return starts[i] if i >= 0 else 0


def _check_direction(name, text):
    """B-177 direction-assertions: same-clause polarity, not just presence.

    Returns a list of failure strings (empty when every rail's polarity is
    intact)."""
    failures = []
    lower = text.lower()
    starts = _clause_starts(lower)

    for label, trigger, negation in DIRECTION_TRIGGERS:
        for m in re.finditer(re.escape(trigger), lower):
            window_start = _clause_start_for(starts, m.start())
            context = lower[window_start:m.start()]
            if negation not in context:
                snippet = text[max(0, m.start() - 60):m.end() + 20].replace("\n", " ")
                failures.append(
                    f"{name}: direction-assert FAILED for {label} "
                    f"(found {trigger!r} without {negation!r} in the same clause; "
                    f"inverted meaning?) near: ...{snippet}..."
                )

    for m in re.finditer(r"fail open", lower):
        window_start = _clause_start_for(starts, m.start())
        context = lower[window_start:m.start()]
        if re.search(r"\bgates?\b", context) and "never" not in context:
            snippet = text[max(0, m.start() - 60):m.end() + 20].replace("\n", " ")
            failures.append(
                f"{name}: direction-assert FAILED for rail 2 (gates): "
                f"found gate(s) ... 'fail open' in the same clause without 'never' in between "
                f"(inverted meaning?) near: ...{snippet}..."
            )

    for label, phrase in BANNED_PHRASES.items():
        if phrase in lower:
            failures.append(
                f"{name}: direction-assert FAILED for {label}: "
                f"banned inverted phrase {phrase!r} present"
            )

    return failures


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

    failures.extend(_check_direction(name, text))

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
