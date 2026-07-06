#!/usr/bin/env python3
# SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0
"""OpenADLC pack conformance check (FAIL-CLOSED).

The per-pack structural eval: a pack must pass this to be certifiable.
Guidance skills are not behaviorally fixture-testable, so the bar is structure
+ the house conventions, checked mechanically.

Hard fails (exit 1): em-dash (literal or \\u2014), a harness-specific path
variable (${CLAUDE_PLUGIN_ROOT}) in any prose unit (commands/skills/agents/
references; it resolves on only one deploy target, so references are cited by
name), missing/invalid frontmatter, skill name != its directory, missing
name/description, invalid manifest JSON or a manifest violating the normative
shape (standard/schema/pack-manifest.schema.json), a manifest `adlc` that does not
equal the one spec-version SSOT (tools/adlc-check.py's SPEC_VERSION), or an
experimental marker inconsistent with the eval level (eval-less packs must be
"experimental": true; fully-evaled packs must not be), implemented here stdlib-only.
Soft warnings (exit 0): no version, no References section, no failable check
mentioned, over-length skill.
Fail-closed (exit 2): zero files checked.

Usage: python3 tools/check-packs.py [pack-name | all]
'all' also self-tests the manifest validator against the two example
manifests in standard/schema/ (valid must pass, invalid must fail).
"""
import sys, os, json, re, glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLUGINS = os.path.join(ROOT, "plugins")

def _read_spec_version():
    """The single source of truth for the spec version: tools/adlc-check.py's SPEC_VERSION.
    Every shipped pack's manifest `adlc` field must equal it, so a version can never drift
    across the 18 wire manifests again (one SSOT + this assert)."""
    p = os.path.join(ROOT, "tools", "adlc-check.py")
    try:
        m = re.search(r'^SPEC_VERSION\s*=\s*"([^"]+)"', open(p, encoding="utf-8").read(), re.M)
        return m.group(1) if m else None
    except Exception:
        return None

SPEC_VERSION = _read_spec_version()

def has_emdash(t):
    return ("\u2014" in t) or ("\\u2014" in t)

PLUGIN_VAR = re.compile(r"\$\{?CLAUDE_PLUGIN_ROOT\b")
def plugin_var_fail(t, r):
    # ${CLAUDE_PLUGIN_ROOT} resolves only on a native Claude plugin install; banned
    # in prose units so references stay portable across deploy targets.
    return [f"{r}: harness-specific path variable (CLAUDE_PLUGIN_ROOT); cite references by name"] if PLUGIN_VAR.search(t) else []

def split_frontmatter(text):
    if not text.startswith("---"):
        return None, ""
    end = text.find("\n---", 3)
    if end == -1:
        return None, ""
    fm = text[4:end]
    inline = {}
    for line in fm.splitlines():
        m = re.match(r"^([A-Za-z0-9_-]+):\s*(\S.*)$", line)
        if m:
            inline[m.group(1)] = m.group(2).strip()
    return inline, fm

hard, soft = [], []
checked = 0

def rel(p):
    return os.path.relpath(p, ROOT)

def check_skill(path):
    global checked
    checked += 1
    t = open(path, encoding="utf-8").read()
    r = rel(path)
    if has_emdash(t): hard.append(f"{r}: em-dash")
    hard.extend(plugin_var_fail(t, r))
    inline, fm = split_frontmatter(t)
    if inline is None:
        hard.append(f"{r}: missing/invalid frontmatter"); return
    name = inline.get("name")
    d = os.path.basename(os.path.dirname(path))
    if not name: hard.append(f"{r}: no name in frontmatter")
    elif name != d: hard.append(f"{r}: name '{name}' != dir '{d}'")
    if not re.search(r"^\s*description:", fm, re.M): hard.append(f"{r}: no description")
    if not re.search(r"^\s*version:", fm, re.M): soft.append(f"{r}: no version")
    if "References" not in t: soft.append(f"{r}: no References section")
    if not re.search(r"failable|check that can fail|## verify|\bverify\b", t, re.I):
        soft.append(f"{r}: no failable check mentioned")
    n = t.count("\n")
    if n > 260: soft.append(f"{r}: long ({n} lines)")

def check_agent(path):
    global checked
    checked += 1
    t = open(path, encoding="utf-8").read()
    r = rel(path)
    if has_emdash(t): hard.append(f"{r}: em-dash")
    hard.extend(plugin_var_fail(t, r))
    inline, fm = split_frontmatter(t)
    if inline is None:
        hard.append(f"{r}: missing/invalid frontmatter"); return
    if not inline.get("name"): hard.append(f"{r}: no name")
    if not re.search(r"^\s*description:", fm, re.M): hard.append(f"{r}: no description")

def check_doc(path):
    t = open(path, encoding="utf-8").read()
    r = rel(path)
    if has_emdash(t): hard.append(f"{r}: em-dash")
    hard.extend(plugin_var_fail(t, r))

def check_command(path):
    global checked
    checked += 1
    t = open(path, encoding="utf-8").read()
    r = rel(path)
    if has_emdash(t): hard.append(f"{r}: em-dash")
    hard.extend(plugin_var_fail(t, r))

# Normative manifest shape (mirrors standard/schema/pack-manifest.schema.json).
SEMVER = re.compile(r"^\d+\.\d+(\.\d+)?(-[0-9A-Za-z.\-]+)?(\+[0-9A-Za-z.\-]+)?$")
UNIT_KEYS = ("skills", "agents", "commands", "references")
EVAL_LEVELS = ("conformance", "conformance+gate")
MANIFEST_KEYS = ("name", "version", "description", "license", "author", "owner",
                 "adlc", "units", "evals", "experimental", "capabilities")

def manifest_violations(d):
    """Validate a parsed manifest against the normative shape; return hard-fail strings."""
    v = []
    for k in ("name", "version", "description", "license"):
        if k not in d: v.append(f"missing '{k}'")
        elif not (isinstance(d[k], str) and d[k]): v.append(f"'{k}' must be a non-empty string")
    for k in ("adlc", "units", "evals", "capabilities"):
        if k not in d: v.append(f"missing '{k}'")
    ver = d.get("version")
    if isinstance(ver, str) and not SEMVER.match(ver):
        v.append(f"version '{ver}' is not semver")
    desc = d.get("description")
    if isinstance(desc, str) and len(desc) > 600:
        v.append(f"description over 600 chars ({len(desc)})")
    a = d.get("author")
    if a is not None and not (isinstance(a, dict) and a.get("name")):
        v.append("author must be an object with a name")
    o = d.get("owner")
    if o is not None and not (isinstance(o, dict) and o.get("name") and o.get("contact")):
        v.append("owner must have name + contact")
    if "adlc" in d and not isinstance(d["adlc"], str):
        v.append("adlc must be a string")
    u = d.get("units")
    if u is not None:
        if not isinstance(u, dict):
            v.append("units must be an object of counts")
        else:
            for k, n in u.items():
                if k not in UNIT_KEYS:
                    v.append(f"units key '{k}' not one of {'/'.join(UNIT_KEYS)}")
                elif isinstance(n, bool) or not isinstance(n, int) or n < 0:
                    v.append(f"units.{k} must be a non-negative int")
    if "evals" in d and d["evals"] not in EVAL_LEVELS:
        v.append(f"evals must be one of {EVAL_LEVELS}")
    if "experimental" in d and not isinstance(d["experimental"], bool):
        v.append("experimental must be a boolean")
    if "capabilities" in d and not isinstance(d["capabilities"], dict):
        v.append("capabilities must be an object")
    for k in d:
        if k not in MANIFEST_KEYS:
            v.append(f"unknown top-level key '{k}'")
    return v

def check_manifest(path):
    r = rel(path)
    t = open(path, encoding="utf-8").read()
    if has_emdash(t): hard.append(f"{r}: em-dash")
    try:
        d = json.loads(t)
    except Exception:
        hard.append(f"{r}: invalid JSON"); return
    hard.extend(f"{r}: manifest {m}" for m in manifest_violations(d))
    # Version SSOT (drift gate): every shipped pack targets the one spec version.
    if SPEC_VERSION is None:
        hard.append(f"{r}: cannot read the SPEC_VERSION SSOT from tools/adlc-check.py")
    elif d.get("adlc") != SPEC_VERSION:
        hard.append(f"{r}: adlc '{d.get('adlc')}' != spec SSOT '{SPEC_VERSION}' (tools/adlc-check.py)")
    # Experimental marker binds to the eval level: an eval-less (structural-only) pack must be
    # marked experimental, and a fully-evaled pack must not be. Keeps the marking honest + automatic.
    evals = d.get("evals")
    experimental = bool(d.get("experimental"))
    if evals == "conformance" and not experimental:
        hard.append(f"{r}: evals 'conformance' (structural only, no behavioral evals) must be marked \"experimental\": true")
    if evals == "conformance+gate" and experimental:
        hard.append(f"{r}: a 'conformance+gate' pack must NOT be marked experimental")
    lic = d.get("license")
    if lic and lic not in ("LicenseRef-OpenADLC-Source-Available-1.0", "CC-BY-4.0"):
        soft.append(f"{r}: license '{lic}' not in the known vocabulary (LicenseRef-OpenADLC-Source-Available-1.0, CC-BY-4.0)")
    if "capabilities" not in d:
        soft.append(f"{r}: no capabilities declared")

def selftest_examples():
    """The schema's own fixtures: the valid example must pass, the invalid must fail."""
    schema_dir = os.path.join(ROOT, "standard", "schema")
    valid = os.path.join(schema_dir, "example-pack.manifest.json")
    invalid = os.path.join(schema_dir, "example-pack-invalid.manifest.json")
    for p in (valid, invalid):
        if not os.path.isfile(p):
            hard.append(f"{rel(p)}: example manifest missing (validator self-test)")
    if not all(os.path.isfile(p) for p in (valid, invalid)):
        return
    try:
        v = manifest_violations(json.load(open(valid, encoding="utf-8")))
    except Exception:
        v = ["invalid JSON"]
    if v:
        hard.extend(f"{rel(valid)}: valid example must pass, got: {m}" for m in v)
    try:
        iv = manifest_violations(json.load(open(invalid, encoding="utf-8")))
    except Exception:
        iv = ["invalid JSON"]
    if not iv:
        hard.append(f"{rel(invalid)}: invalid example passed; the validator caught nothing")

target = sys.argv[1] if len(sys.argv) > 1 else "all"
if target == "all":
    packs = sorted(os.path.basename(p) for p in glob.glob(os.path.join(PLUGINS, "*")) if os.path.isdir(p))
    selftest_examples()
else:
    packs = [target]

for pack in packs:
    pdir = os.path.join(PLUGINS, pack)
    if not os.path.isdir(pdir):
        hard.append(f"pack '{pack}' not found"); continue
    for f in glob.glob(os.path.join(pdir, "skills", "*", "SKILL.md")): check_skill(f)
    for f in glob.glob(os.path.join(pdir, "agents", "*.md")): check_agent(f)
    for f in glob.glob(os.path.join(pdir, "references", "*.md")): check_doc(f)
    for f in glob.glob(os.path.join(pdir, "commands", "*.md")): check_command(f)
    mf = os.path.join(pdir, ".claude-plugin", "plugin.json")
    if os.path.isfile(mf): check_manifest(mf)

print(f"packs checked: {len(packs)} | files: {checked}")
if soft:
    print(f"\nWARN ({len(soft)}):")
    for s in soft[:50]: print(f"  - {s}")
    if len(soft) > 50: print(f"  ... +{len(soft) - 50} more")
if hard:
    print(f"\nFAIL ({len(hard)}):")
    for h in hard: print(f"  - {h}")
if checked == 0:
    print("\nFAIL-CLOSED: zero files checked"); sys.exit(2)
if hard:
    print(f"\nRESULT: FAIL ({len(hard)} hard)"); sys.exit(1)
print(f"\nRESULT: PASS (hard checks clean, {len(soft)} warnings)")
