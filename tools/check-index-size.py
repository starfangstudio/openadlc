#!/usr/bin/env python3
# SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0
"""Always-loaded INDEX-line size bound (dev-time test, not pack runtime).

B-172 rail (D62): the per-module INDEX line that stays in context the whole
run (the pack's `description` in .claude-plugin/marketplace.json) is the
always-loaded budget that makes progressive disclosure worthwhile. It MUST
stay tiny and single-line; a description that grows into a multi-line
paragraph defeats the point. This check asserts, red-before-green:
  - every pack index line is a SINGLE line (no embedded newline), and
  - every pack index line is <= MAX_INDEX_CHARS (HARD FAIL).

Two tiers (D64 option B):
  - MAX_INDEX_CHARS (600): a hard bloat ceiling. Exceeding it, or embedding a
    newline, FAILS the check (exit 1).
  - WARN_INDEX_CHARS (250): the genuinely-tiny one-trigger-sentence target.
    Exceeding it prints a WARN line (name + length) but does NOT fail; a
    handful of packs landing at 251-260 chars for meaning's sake is fine.
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANIFEST = os.path.join(ROOT, ".claude-plugin", "marketplace.json")

# Hard bloat ceiling: exceeding it (or embedding a newline) fails the check.
MAX_INDEX_CHARS = 600

# Warn tier: the genuinely-tiny one-trigger-sentence target. Exceeding it
# prints a warning but does not fail the check.
WARN_INDEX_CHARS = 250


def index_lines(manifest_path):
    m = json.load(open(manifest_path, encoding="utf-8"))
    plugins = m.get("plugins") or m.get("packs") or []
    return [(p.get("name", "?"), p.get("description", "")) for p in plugins]


def violations(lines, max_chars=MAX_INDEX_CHARS):
    out = []
    for name, desc in lines:
        if "\n" in desc:
            out.append((name, "multi-line (index line must be a single line)"))
        if len(desc) > max_chars:
            out.append((name, f"{len(desc)} chars > {max_chars} ceiling"))
    return out


def warnings(lines, warn_chars=WARN_INDEX_CHARS):
    return [(name, len(desc)) for name, desc in lines if len(desc) > warn_chars]


def main():
    if not os.path.isfile(MANIFEST):
        print(f"FAIL-CLOSED: manifest not found: {MANIFEST}")
        return 2
    lines = index_lines(MANIFEST)

    # TEETH: a synthetic over-budget / multi-line index line MUST be caught.
    planted = lines + [("fx-bloat-oneline", "x" * (MAX_INDEX_CHARS + 1)),
                       ("fx-bloat-multiline", "line one\nline two")]
    if len(violations(planted)) < 2:
        print("TEETH FAIL: the bound did not catch a planted over-budget / multi-line index line")
        return 1

    real = violations(lines)
    warn = warnings(lines)
    longest = max((len(d) for _, d in lines), default=0)
    print(f"packs checked: {len(lines)} | longest index line: {longest} chars | ceiling: {MAX_INDEX_CHARS} | warn tier: {WARN_INDEX_CHARS}")
    if warn:
        print(f"WARN: {len(warn)} pack(s) over the {WARN_INDEX_CHARS}-char tiny-target tier (not a failure):")
        for name, n in warn:
            print(f"  - {name}: {n} chars")
    if real:
        print("FAIL: index-line bound violated:")
        for name, why in real:
            print(f"  - {name}: {why}")
        return 1
    print("RESULT: PASS (every pack index line is single-line and within the bloat ceiling; TEETH proven)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
