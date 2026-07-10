#!/usr/bin/env python3
# SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0
"""Activation-funnel red-proves (dev-time test, not pack runtime).

Slice S-A3 (B-172). Models the SUBSET of the activation funnel that these
red-proves exercise: stage 0's candidate-set boundary, stage 1's reused
repo-facts detector, stage 2's `candidate_set INTERSECT matched_domains`
over the TECHNICAL domains, and rail 1 (the mandatory floor). It does NOT
model stage-2 lens/ask-scoping, rail 2 (ambiguity->include), or rail 3
(audit log) - those are documented in the `## 0.` preamble but out of scope
for this check. It proves three load-bearing behaviors red-before-green:

  RED-PROVE 1  a repo matching TWO domains activates BOTH matched packs
               (stage 2's `candidate_set INTERSECT matched_domains` is a
               union over every match, not a pick-one).
  RED-PROVE 2  repo-supplied config CANNOT drop a floor member (rail 1:
               "the floor loads before and independent of ... stage 0 ...
               [and] can NEVER drop a floor member"). A malicious
               `.openadlc/config.yaml` inside the repo that tries to disable
               `adlc-security` via `packs.disabled` has zero effect (floor
               IMMUNITY).
  RED-PROVE 3  a candidate-set tightening that drops a DISCRETIONARY pack
               DOES narrow the activated set, while the floor stands (floor
               PRECEDENCE): proves the funnel is not merely ignoring
               `packs.disabled` wholesale. 2 + 3 together lock stage 0.

This script REUSES check-domains.py's marker detectors (imported, not
reimplemented) for stage-1 repo-facts detection. It does not ship with a
pack and no command shells out to it; the command follows the declarative
`## 0.` preamble directly. This script only proves that documented funnel
is correct, with fixtures that show a broken funnel fails first (the
"stub" variants below) before the correct funnel passes (TEETH).

Usage: python3 tools/check-activation-redproves.py
Exit 0 both red-proves pass (RED shown, then GREEN), 1 any assertion did not
behave as documented, 2 fixtures missing (fail-closed).
"""
import importlib.util
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIXTURES_DIR = os.path.join(ROOT, "tools", "test", "activation", "fixtures")
DOMAINS_FIXTURES_DIR = os.path.join(ROOT, "tools", "test", "domains", "fixtures")


def _load_check_domains():
    """Import tools/check-domains.py as a module (dash in filename, so this
    can't be a normal `import`). REUSE its detectors, never reimplement."""
    path = os.path.join(ROOT, "tools", "check-domains.py")
    spec = importlib.util.spec_from_file_location("check_domains", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


check_domains = _load_check_domains()
DETECT = check_domains.detect  # {domain_name, ...} for a fixture dir, stage 1

# The domain -> pack map from standard/domains.md section 2 (technical
# domains). Exact strings, cited verbatim from that table.
DOMAIN_TO_PACK = {
    "web": "adlc-web",
    "backend": "adlc-backend",
    "backend-cloud": "adlc-backend-cloud",
    "android": "adlc-android",
    "ios": "adlc-ios",
    "desktop": "adlc-desktop",
    "database": "adlc-database",
    "ai": "adlc-ai",
    "unity": "adlc-unity",
    "ops": "adlc-ops",
    "monetization": "adlc-monetization",
}

ALL_PACKS = frozenset(DOMAIN_TO_PACK.values())

# Rail 1, MANDATORY FLOOR (plugins/adlc-core/commands/ai-implement.md § 0):
# "the adlc-core spine ..., the security lens, and the org-policy pins load
# ALWAYS, before stage 2 runs, never model-optional." No org pins by default.
FLOOR = frozenset({"adlc-core", "adlc-security"})


def _read_repo_disabled_packs(fixture_dir):
    """Read a repo-local `packs.disabled` list from `.openadlc/config.yaml`
    or `openadlc.yaml` at the fixture root, the same key
    openadlc.example.yaml documents for tightening the stage-2 discretionary
    set. Intentionally NOT a general YAML parser (out of scope for a dev-time
    check): a narrow regex over the one key this red-prove exercises."""
    disabled = set()
    for name in (os.path.join(".openadlc", "config.yaml"), "openadlc.yaml"):
        path = os.path.join(fixture_dir, name)
        if not os.path.isfile(path):
            continue
        text = check_domains._read(path)
        m = re.search(r"disabled:\s*\[([^\]]*)\]", text)
        if m:
            disabled |= {p.strip() for p in m.group(1).split(",") if p.strip()}
    return disabled


# ---------------------------------------------------------------------------
# The funnel model (correct, per standard/domains.md + the § 0 preamble).
# ---------------------------------------------------------------------------

def activate(fixture_dir, candidate_set=ALL_PACKS, org_pins=frozenset()):
    """Stage 0 (candidate_set, a hard boundary) -> stage 1 (reused detector)
    -> stage 2 union -> rail 1 floor, independent of repo content and of the
    candidate set. Returns the activated pack set."""
    detected_domains = DETECT(fixture_dir)
    detected_packs = {DOMAIN_TO_PACK[d] for d in detected_domains}
    floor = FLOOR | set(org_pins)
    discretionary = candidate_set & detected_packs
    return floor | discretionary


# ---------------------------------------------------------------------------
# RED-PROVE 1: a broken funnel that keeps only ONE matched domain (a
# "single-domain" stub of stage 2), instead of the documented union over
# every match in `candidate_set ∩ matched_domains`.
# ---------------------------------------------------------------------------

def _broken_single_domain_activate(fixture_dir, candidate_set=ALL_PACKS, org_pins=frozenset()):
    detected_domains = DETECT(fixture_dir)
    if not detected_domains:
        detected_packs = set()
    else:
        first = sorted(detected_domains)[0]  # picks ONE match, drops the rest
        detected_packs = {DOMAIN_TO_PACK[first]}
    floor = FLOOR | set(org_pins)
    discretionary = candidate_set & detected_packs
    return floor | discretionary


def redprove_1_two_domain_activates_both():
    fixture = os.path.join(DOMAINS_FIXTURES_DIR, "fx-multi")  # {web, backend-cloud}
    if not os.path.isdir(fixture):
        print(f"FAIL-CLOSED: fixture not found: {fixture}")
        return False

    expect = {"adlc-web", "adlc-backend-cloud"}

    print("RED-PROVE 1: a two-domain repo activates BOTH matched packs")
    print(f"  fixture: {fixture}")

    broken = _broken_single_domain_activate(fixture)
    broken_ok = expect <= broken
    print(f"  [RED]  broken funnel (single-domain stub, keeps only the first match):")
    print(f"         activated={sorted(broken)}")
    if broken_ok:
        print("         UNEXPECTED: the broken stub still activated both packs (no teeth)")
    else:
        missing = expect - broken
        print(f"         correctly FAILS the assertion: missing {sorted(missing)}")

    correct = activate(fixture)
    correct_ok = expect <= correct
    print(f"  [GREEN] correct funnel (candidate ∩ matched, union over every match):")
    print(f"         activated={sorted(correct)}")
    print(f"         assertion {'PASSES' if correct_ok else 'FAILS'}: both {sorted(expect)} present"
          + ("" if correct_ok else f", missing {sorted(expect - correct)}"))

    teeth_ok = (not broken_ok) and correct_ok
    print(f"  TEETH: {'proven' if teeth_ok else 'NOT proven'} (broken must fail, correct must pass)\n")
    return teeth_ok


# ---------------------------------------------------------------------------
# RED-PROVE 2: a broken funnel that HONORS a repo-local `packs.disabled`
# list even against a floor member (the injection succeeds), instead of the
# documented rail: the floor loads before and independent of the candidate
# set / repo content, and NOTHING can drop a floor member.
# ---------------------------------------------------------------------------

def _broken_honor_repo_disable_activate(fixture_dir, candidate_set=ALL_PACKS, org_pins=frozenset()):
    detected_domains = DETECT(fixture_dir)
    detected_packs = {DOMAIN_TO_PACK[d] for d in detected_domains}
    floor = FLOOR | set(org_pins)
    repo_disabled = _read_repo_disabled_packs(fixture_dir)
    floor = floor - repo_disabled  # BUG: honors the repo's own disable list on the floor
    discretionary = (candidate_set - repo_disabled) & detected_packs
    return floor | discretionary


def redprove_2_floor_survives_repo_injection():
    fixture = os.path.join(FIXTURES_DIR, "fx-inject-disable-security")
    if not os.path.isdir(fixture):
        print(f"FAIL-CLOSED: fixture not found: {fixture}")
        return False

    disabled = _read_repo_disabled_packs(fixture)
    print("RED-PROVE 2: repo content cannot deactivate a floor pack (injection)")
    print(f"  fixture: {fixture}")
    print(f"  repo-supplied packs.disabled: {sorted(disabled)}")

    broken = _broken_honor_repo_disable_activate(fixture)
    broken_ok = "adlc-security" in broken
    print(f"  [RED]  broken funnel (honors the repo's own disable list on the floor):")
    print(f"         activated={sorted(broken)}")
    if broken_ok:
        print("         UNEXPECTED: adlc-security survived the broken stub (no teeth)")
    else:
        print("         correctly FAILS the assertion: adlc-security was dropped (injection succeeded)")

    correct = activate(fixture)
    correct_ok = "adlc-security" in correct
    print(f"  [GREEN] correct funnel (floor independent of stage-0 AND repo content):")
    print(f"         activated={sorted(correct)}")
    print(f"         assertion {'PASSES' if correct_ok else 'FAILS'}: adlc-security present")

    teeth_ok = (not broken_ok) and correct_ok
    print(f"  TEETH: {'proven' if teeth_ok else 'NOT proven'} (broken must fail, correct must pass)\n")
    return teeth_ok


# ---------------------------------------------------------------------------
# RED-PROVE 3: an org-policy candidate-set tightening that drops a DISCRETIONARY
# pack actually narrows the activated set, while the floor stands. Complements
# RED-PROVE 2: 2 proves the floor is IMMUNE to tightening; 3 proves tightening
# still WORKS on discretionary packs, so the funnel is not merely ignoring
# `packs.disabled` wholesale (a funnel that dropped `& candidate_set` would pass
# 1 and 2 but fail here). Together they lock stage-0 precedence.
# ---------------------------------------------------------------------------

def _broken_ignore_candidate_activate(fixture_dir, candidate_set=ALL_PACKS, org_pins=frozenset()):
    detected_domains = DETECT(fixture_dir)
    detected_packs = {DOMAIN_TO_PACK[d] for d in detected_domains}
    floor = FLOOR | set(org_pins)
    return floor | detected_packs  # BUG: ignores candidate_set; tightening never narrows


def redprove_3_candidate_tightening_narrows_discretionary():
    fixture = os.path.join(DOMAINS_FIXTURES_DIR, "fx-multi")  # {web, backend-cloud}
    if not os.path.isdir(fixture):
        print(f"FAIL-CLOSED: fixture not found: {fixture}")
        return False

    # Org policy tightens the candidate set by dropping a DISCRETIONARY pack.
    candidate = ALL_PACKS - {"adlc-backend-cloud"}
    print("RED-PROVE 3: a candidate-set tightening narrows a DISCRETIONARY pack (floor stands)")
    print(f"  fixture: {fixture}")
    print("  candidate set drops (discretionary): ['adlc-backend-cloud']")

    broken = _broken_ignore_candidate_activate(fixture, candidate_set=candidate)
    broken_ok = "adlc-backend-cloud" not in broken  # correct behavior would DROP it
    print("  [RED]  broken funnel (ignores candidate_set; tightening never narrows):")
    print(f"         activated={sorted(broken)}")
    if broken_ok:
        print("         UNEXPECTED: the broken stub dropped it anyway (no teeth)")
    else:
        print("         correctly FAILS the assertion: adlc-backend-cloud was NOT narrowed out")

    correct = activate(fixture, candidate_set=candidate)
    narrowed = "adlc-backend-cloud" not in correct
    floor_stands = {"adlc-core", "adlc-security"} <= correct
    web_stays = "adlc-web" in correct  # matched AND still in the candidate set
    correct_ok = narrowed and floor_stands and web_stays
    print("  [GREEN] correct funnel (candidate ∩ matched; floor independent):")
    print(f"         activated={sorted(correct)}")
    print(f"         assertion {'PASSES' if correct_ok else 'FAILS'}: "
          "backend-cloud narrowed out, floor + adlc-web stand")

    teeth_ok = (not broken_ok) and correct_ok
    print(f"  TEETH: {'proven' if teeth_ok else 'NOT proven'} (broken must fail, correct must pass)\n")
    return teeth_ok


def main():
    if not os.path.isdir(FIXTURES_DIR) or not os.path.isdir(DOMAINS_FIXTURES_DIR):
        print("FAIL-CLOSED: fixtures dir(s) not found")
        return 2

    ok1 = redprove_1_two_domain_activates_both()
    ok2 = redprove_2_floor_survives_repo_injection()
    ok3 = redprove_3_candidate_tightening_narrows_discretionary()

    if ok1 and ok2 and ok3:
        print("RESULT: PASS (all three red-proves show RED under a broken funnel, GREEN under the correct funnel)")
        return 0
    print("RESULT: FAIL")
    if not ok1:
        print("  - RED-PROVE 1 (two-domain union) did not behave as documented")
    if not ok2:
        print("  - RED-PROVE 2 (floor survives injection) did not behave as documented")
    if not ok3:
        print("  - RED-PROVE 3 (candidate tightening narrows discretionary) did not behave as documented")
    return 1


if __name__ == "__main__":
    sys.exit(main())
