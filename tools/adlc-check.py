#!/usr/bin/env python3
# SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0
"""adlc-check: the owned reference conformance checker for OpenADLC (FAIL-CLOSED).

The tool the standard commits to. It runs the AUTO checks in
standard/conformance.md, records the AUDIT/ATTEST ones, and prints the verdict
shape from standard/conformance-checker.md. Stdlib-only Python, no network, no
git. Design: tools/adlc-check-DESIGN.md.

  python3 tools/adlc-check.py <subject> <path> [--json] [--level L] [--quiet]
    subject   pack | team | harness
    path      pack     -> a manifest file (JSON or YAML), or a pack directory
              team     -> a directory holding .adlc/conformance.yaml (or the file)
              harness  -> a probe-result fixture (JSON or YAML)
    --json    emit the JSON report instead of the human form
    --level   claim a level (team default = the manifest's; pack/harness = core)
    --quiet   human mode: print only the VERDICT line
    --selftest  run the bundled self-test (both example manifests + all packs)

Exit codes: 0 conformant, 1 not conformant, 2 usage/input error (fail-closed).

Two fields per check, never mixed: status (pass|fail|warn|n/a|not-run) and
provenance (auto|audit|attest). An attest/audit pass is reported with its
provenance so it is never read as machine-proven.
"""
import sys
import os
import re
import json
import glob

SPEC_VERSION = "0.1"
CHECKER_VERSION = "0.1"
LICENSE_VOCAB = ("LicenseRef-OpenADLC-Source-Available-1.0", "CC-BY-4.0")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCHEMA_PATH = os.path.join(ROOT, "standard", "schema", "pack-manifest.schema.json")

# The bundled authority (standard/conformance-checker.md). Carried in code so a
# stale checker cannot silently pass a newer pack.
PROVENANCE = {
    "T-C1": "attest",
    "T-C2": "audit", "T-C3": "audit", "T-C4": "audit", "T-C5": "audit",
    "T-G1": "auto", "T-G2": "audit", "T-G3": "audit",
    "T-X1": "audit",
    "P1": "auto", "P2": "auto", "P3a": "auto", "P3b": "auto",
    "P4": "auto", "P5": "auto", "P6": "auto",
    "H1": "auto", "H2": "auto", "H3-intool": "auto", "H3-external": "audit",
    "H4": "auto", "H5": "auto",
}

TEAM_LEVELS = {
    "core": ["T-C1", "T-C2", "T-C3", "T-C4", "T-C5"],
    "governed": ["T-C1", "T-C2", "T-C3", "T-C4", "T-C5", "T-G1", "T-G2", "T-G3"],
    "certified": ["T-C1", "T-C2", "T-C3", "T-C4", "T-C5",
                  "T-G1", "T-G2", "T-G3", "T-X1"],
}

# Official SemVer 2.0.0 (semver.org). P6 is advisory: a miss is warn, never fail.
SEMVER = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-((?:0|[1-9]\d*|\d*[A-Za-z-][0-9A-Za-z-]*)"
    r"(?:\.(?:0|[1-9]\d*|\d*[A-Za-z-][0-9A-Za-z-]*))*))?"
    r"(?:\+([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$"
)

USAGE = (
    "usage: adlc-check <pack|team|harness> <path> "
    "[--json] [--level L] [--quiet]\n"
    "       adlc-check --selftest"
)


class InputError(Exception):
    """A fail-closed input problem: bad path, unparseable manifest, bad subject."""


def err(msg):
    print(msg, file=sys.stderr)


# --------------------------------------------------------------------------- #
# mini_yaml: a constrained YAML subset, enough for ADLC manifests and the team
# conformance.yaml. Anything it cannot represent raises (never a lenient guess).
# --------------------------------------------------------------------------- #

class YamlError(Exception):
    pass


def _indent(line):
    return len(line) - len(line.lstrip(" "))


def _significant(lines, i):
    """Index of the next non-blank, non-comment line at or after i."""
    while i < len(lines):
        s = lines[i].strip()
        if s and not s.startswith("#"):
            return i
        i += 1
    return len(lines)


def _strip_comment(s):
    """Drop a trailing ' # ...' comment, respecting quotes. Keeps '#' in strings."""
    out = []
    q = None
    for idx, c in enumerate(s):
        if q:
            out.append(c)
            if c == q:
                q = None
        elif c in "\"'":
            q = c
            out.append(c)
        elif c == "#" and (idx == 0 or s[idx - 1] in " \t"):
            break
        else:
            out.append(c)
    return "".join(out).rstrip()


def _unquote(s):
    s = s.strip()
    if len(s) >= 2 and s[0] == s[-1] and s[0] == '"':
        body = s[1:-1]
        return (body.replace('\\"', '"').replace("\\\\", "\\")
                    .replace("\\n", "\n").replace("\\t", "\t"))
    if len(s) >= 2 and s[0] == s[-1] and s[0] == "'":
        return s[1:-1].replace("''", "'")
    return s


def _parse_scalar(s):
    s = s.strip()
    if s == "":
        return None
    if s[0] in "\"'":
        return _unquote(s)
    low = s.lower()
    if low in ("null", "~"):
        return None
    if low == "true":
        return True
    if low == "false":
        return False
    try:
        return int(s)
    except ValueError:
        pass
    try:
        return float(s)
    except ValueError:
        pass
    return s


def _split_flow(inner):
    """Split a flow body on top-level commas, respecting quotes and nesting."""
    parts, cur, depth, q = [], [], 0, None
    for c in inner:
        if q:
            cur.append(c)
            if c == q:
                q = None
        elif c in "\"'":
            q = c
            cur.append(c)
        elif c in "[{":
            depth += 1
            cur.append(c)
        elif c in "]}":
            depth -= 1
            cur.append(c)
        elif c == "," and depth == 0:
            parts.append("".join(cur))
            cur = []
        else:
            cur.append(c)
    tail = "".join(cur)
    if tail.strip() != "":
        parts.append(tail)
    return parts


def _split_key(content):
    """Split 'key: value' at the first depth-0 ':' followed by space or EOL."""
    depth, q = 0, None
    for i, c in enumerate(content):
        if q:
            if c == q:
                q = None
        elif c in "\"'":
            q = c
        elif c in "[{":
            depth += 1
        elif c in "]}":
            depth -= 1
        elif c == ":" and depth == 0 and (i + 1 == len(content)
                                          or content[i + 1] == " "):
            return content[:i], content[i + 1:]
    return content, None


def _parse_flow(s):
    s = s.strip()
    if s[:1] == "{":
        if s[-1:] != "}":
            raise YamlError("unterminated flow mapping: %r" % s)
        inner = s[1:-1].strip()
        d = {}
        if inner == "":
            return d
        for part in _split_flow(inner):
            if part.strip() == "":
                continue
            k, v = _split_key(part.strip())
            if v is None:
                raise YamlError("bad flow map entry: %r" % part)
            d[_parse_scalar(k)] = _parse_flow(v)
        return d
    if s[:1] == "[":
        if s[-1:] != "]":
            raise YamlError("unterminated flow sequence: %r" % s)
        inner = s[1:-1].strip()
        if inner == "":
            return []
        return [_parse_flow(p) for p in _split_flow(inner) if p.strip() != ""]
    return _parse_scalar(s)


def _parse_block_scalar(lines, i, parent_indent, header):
    style = header[0]
    chomp = "".join(ch for ch in header[1:] if ch in "+-")
    collected, block_indent = [], None
    while i < len(lines):
        ln = lines[i]
        if ln.strip() == "":
            collected.append("")
            i += 1
            continue
        ind = _indent(ln)
        if ind <= parent_indent:
            break
        if block_indent is None:
            block_indent = ind
        collected.append(ln[block_indent:] if len(ln) >= block_indent else "")
        i += 1
    while collected and collected[-1] == "":
        collected.pop()
    if style == ">":
        text = " ".join(collected).strip()
    else:
        text = "\n".join(collected)
    if chomp != "-" and style == "|":
        text += "\n"
    return text, i


def _parse_node(lines, i, min_indent):
    j = _significant(lines, i)
    if j >= len(lines) or _indent(lines[j]) < min_indent:
        return None, i
    indent = _indent(lines[j])
    content = _strip_comment(lines[j][indent:])
    if content.startswith("- ") or content == "-":
        return _parse_seq(lines, j, indent)
    return _parse_map(lines, j, indent)


def _parse_map(lines, i, indent):
    result = {}
    while True:
        i = _significant(lines, i)
        if i >= len(lines):
            break
        cur = _indent(lines[i])
        if cur < indent:
            break
        if cur > indent:
            raise YamlError("unexpected indent at line %d: %r" % (i + 1, lines[i]))
        content = _strip_comment(lines[i][cur:])
        key, rest = _split_key(content)
        if rest is None:
            raise YamlError("expected 'key: value' at line %d: %r"
                            % (i + 1, content))
        rest = rest.strip()
        i += 1
        if rest == "":
            val, i = _parse_node(lines, i, indent + 1)
        elif rest[0] in "|>":
            val, i = _parse_block_scalar(lines, i, indent, rest)
        else:
            val = _parse_flow(rest)
        result[_parse_scalar(key)] = val
    return result, i


def _parse_seq(lines, i, indent):
    result = []
    while True:
        i = _significant(lines, i)
        if i >= len(lines):
            break
        cur = _indent(lines[i])
        if cur < indent:
            break
        if cur > indent:
            raise YamlError("unexpected indent at line %d" % (i + 1))
        content = _strip_comment(lines[i][cur:])
        if not (content == "-" or content.startswith("- ")):
            break
        item = content[1:].strip()
        i += 1
        if item == "":
            val, i = _parse_node(lines, i, indent + 1)
        else:
            val = _parse_flow(item)
        result.append(val)
    return result, i


def mini_yaml_load(text):
    lines = text.replace("\t", "    ").split("\n")
    j = _significant(lines, 0)
    if j >= len(lines):
        return None
    content = _strip_comment(lines[j][_indent(lines[j]):])
    if content[:1] in ("{", "["):
        return _parse_flow(content)
    val, _ = _parse_node(lines, 0, 0)
    return val


def load_data(mpath):
    """Load a manifest as JSON or YAML. Raises on unparseable input (exit 2)."""
    with open(mpath, encoding="utf-8") as f:
        text = f.read()
    ext = os.path.splitext(mpath)[1].lower()
    if ext in (".yaml", ".yml"):
        return mini_yaml_load(text)
    if ext == ".json":
        return json.loads(text)
    try:
        return json.loads(text)
    except ValueError:
        return mini_yaml_load(text)


# --------------------------------------------------------------------------- #
# JSON Schema (draft 2020-12) subset validator: exactly the keywords that
# pack-manifest.schema.json uses. Loading the schema file (not re-coding its
# rules) keeps the checker and the schema a single source of truth.
# --------------------------------------------------------------------------- #

def _is_number(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def _type_ok(inst, t):
    for name in (t if isinstance(t, list) else [t]):
        if name == "object" and isinstance(inst, dict):
            return True
        if name == "array" and isinstance(inst, list):
            return True
        if name == "string" and isinstance(inst, str):
            return True
        if name == "boolean" and isinstance(inst, bool):
            return True
        if name == "integer" and isinstance(inst, int) and not isinstance(inst, bool):
            return True
        if name == "number" and _is_number(inst):
            return True
        if name == "null" and inst is None:
            return True
    return False


def validate(instance, schema, path="$"):
    errs = []
    t = schema.get("type")
    if t is not None and not _type_ok(instance, t):
        errs.append("%s: expected %s" % (path, t))
        return errs  # wrong type: further keywords would be noise
    if "enum" in schema and instance not in schema["enum"]:
        errs.append("%s: not one of %s" % (path, schema["enum"]))
    if isinstance(instance, str):
        if "minLength" in schema and len(instance) < schema["minLength"]:
            errs.append("%s: shorter than %d" % (path, schema["minLength"]))
        if "maxLength" in schema and len(instance) > schema["maxLength"]:
            errs.append("%s: longer than %d (%d)"
                        % (path, schema["maxLength"], len(instance)))
        if "pattern" in schema and not re.search(schema["pattern"], instance):
            errs.append("%s: does not match pattern" % path)
    if _is_number(instance):
        if "minimum" in schema and instance < schema["minimum"]:
            errs.append("%s: below minimum %s" % (path, schema["minimum"]))
        if "maximum" in schema and instance > schema["maximum"]:
            errs.append("%s: above maximum %s" % (path, schema["maximum"]))
    if isinstance(instance, dict):
        props = schema.get("properties", {})
        for req in schema.get("required", []):
            if req not in instance:
                errs.append("%s: missing '%s'" % (path, req))
        ap = schema.get("additionalProperties", True)
        for k, v in instance.items():
            if k in props:
                errs += validate(v, props[k], "%s.%s" % (path, k))
            elif ap is False:
                errs.append("%s: unknown key '%s'" % (path, k))
            elif isinstance(ap, dict):
                errs += validate(v, ap, "%s.%s" % (path, k))
    if isinstance(instance, list):
        items = schema.get("items")
        if isinstance(items, dict):
            for idx, it in enumerate(instance):
                errs += validate(it, items, "%s[%d]" % (path, idx))
    return errs


def load_schema():
    if not os.path.isfile(SCHEMA_PATH):
        raise InputError("bundled schema missing: %s" % SCHEMA_PATH)
    try:
        with open(SCHEMA_PATH, encoding="utf-8") as f:
            return json.load(f)
    except ValueError as e:
        raise InputError("bundled schema is not valid JSON: %s" % e)


# --------------------------------------------------------------------------- #
# Check helpers and the opaque-binary content scan (P5, directory input only).
# --------------------------------------------------------------------------- #

def chk(cid, status, note):
    return {"id": cid, "status": status,
            "provenance": PROVENANCE[cid], "note": note}


MEDIA_EXT = {".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".ico", ".bmp",
             ".pdf", ".woff", ".woff2", ".ttf", ".otf", ".eot",
             ".mp4", ".mp3", ".wav", ".mov", ".webm"}


def scan_opaque_binaries(pdir):
    """Flag shipped opaque binaries: NUL-containing, non-media, non-dot files.

    Dotfiles and dot-directories (.git, .DS_Store, .claude-plugin) are OS/VCS
    cruft, not shipped units, so they are skipped. Prose-that-coaxes-a-bypass is
    the certification program's scan, not this one.
    """
    hits = []
    for root, dirs, files in os.walk(pdir):
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        for name in files:
            if name.startswith("."):
                continue
            if os.path.splitext(name)[1].lower() in MEDIA_EXT:
                continue
            fp = os.path.join(root, name)
            try:
                with open(fp, "rb") as fh:
                    if b"\x00" in fh.read(8192):
                        hits.append(os.path.relpath(fp, pdir))
            except OSError:
                continue
    return hits


def _join(notes):
    return "; ".join(n for n in notes if n)


def _report(subject, target, checks, verdict, level, attested, code, error=None):
    r = {
        "spec": SPEC_VERSION,
        "checker": CHECKER_VERSION,
        "subject": subject,
        "target": target,
        "checks": checks,
        "verdict": verdict,
        "level": level,
        "attested": attested,
        "exitCode": code,
    }
    if error is not None:
        r["error"] = error
    return r


# --------------------------------------------------------------------------- #
# Pack mode
# --------------------------------------------------------------------------- #

def find_pack_manifest(path):
    """Return (manifest_path, is_directory). Raises if nothing is found."""
    if os.path.isfile(path):
        return path, False
    if os.path.isdir(path):
        candidates = [
            os.path.join(path, ".claude-plugin", "plugin.json"),
            os.path.join(path, "pack.json"),
            os.path.join(path, "manifest.json"),
            os.path.join(path, ".adlc", "pack.yaml"),
            os.path.join(path, ".adlc", "pack.json"),
        ]
        candidates += sorted(glob.glob(os.path.join(path, "*.manifest.json")))
        candidates += sorted(glob.glob(os.path.join(path, "*.manifest.yaml")))
        for c in candidates:
            if os.path.isfile(c):
                return c, True
        raise InputError("no pack manifest found under %s" % path)
    raise InputError("path not found: %s" % path)


def build_pack(path, level=None, schema=None):
    schema = schema or load_schema()
    mpath, is_dir = find_pack_manifest(path)
    try:
        data = load_data(mpath)
    except (ValueError, YamlError, OSError) as e:
        raise InputError("cannot read manifest %s: %s" % (mpath, e))
    if not isinstance(data, dict):
        raise InputError("manifest %s is not a mapping" % mpath)

    checks = []

    # P1: full schema validation.
    errs = validate(data, schema)
    if errs:
        shown = "; ".join(errs[:6]) + (" ..." if len(errs) > 6 else "")
        checks.append(chk("P1", "fail", "schema: " + shown))
    else:
        note = "schema-valid"
        lic = data.get("license")
        if lic not in LICENSE_VOCAB:
            note += " (warn: license %r outside known vocabulary)" % lic
        checks.append(chk("P1", "pass", note))

    # P2: at least one per-kind unit count >= 1.
    units = data.get("units")
    total = 0
    if isinstance(units, dict):
        total = sum(v for v in units.values()
                    if isinstance(v, int) and not isinstance(v, bool) and v > 0)
    if total >= 1:
        checks.append(chk("P2", "pass", "%d units declared" % total))
    else:
        checks.append(chk("P2", "fail", "no guidance unit (need at least one)"))

    # P3a: the eval bar is declared.
    evals = data.get("evals")
    if evals in ("conformance", "conformance+gate"):
        checks.append(chk("P3a", "pass", "eval bar: %s" % evals))
    else:
        checks.append(chk("P3a", "fail", "eval bar not declared (got %r)" % evals))

    # P3b: no eval runner is wired into the reference checker -> not-run (no gate).
    checks.append(chk("P3b", "not-run", "no eval runner declared (does not gate)"))

    # P4: capabilities well-formed; declared-vs-behavior match is the cert scan.
    caps = data.get("capabilities")
    if isinstance(caps, dict):
        cap_errs = validate(caps, schema["properties"]["capabilities"], "capabilities")
        if cap_errs:
            checks.append(chk("P4", "fail", "; ".join(cap_errs[:4])))
        else:
            checks.append(chk("P4", "pass",
                              "well-formed; behavior match -> certification "
                              "program scan"))
    else:
        checks.append(chk("P4", "fail", "capabilities missing or not an object"))

    # P5: no checkpoint-subverting key (none exists in the vocabulary, so it is
    # structurally absent). Opaque-binary half is scanned only for a directory.
    notes = ["no checkpoint-subverting capability key (structurally absent)"]
    status = "pass"
    if is_dir:
        binaries = scan_opaque_binaries(path)
        if binaries:
            status = "fail"
            notes.append("opaque binaries: " + ", ".join(binaries[:5])
                         + (" ..." if len(binaries) > 5 else ""))
        else:
            notes.append("content scan: no opaque binary")
    else:
        notes.append("opaque-binary half -> certification program scan "
                     "(no directory given)")
    checks.append(chk("P5", status, _join(notes)))

    # P6: SemVer, advisory.
    version = data.get("version")
    if isinstance(version, str) and SEMVER.match(version):
        checks.append(chk("P6", "pass", version))
    else:
        checks.append(chk("P6", "warn", "version not SemVer: %r" % version))

    by = {c["id"]: c for c in checks}
    gate = ["P1", "P2", "P3a", "P4", "P5"]
    ok = (all(by[i]["status"] == "pass" for i in gate)
          and by["P3b"]["status"] in ("pass", "not-run"))
    verdict = "conformant" if ok else "not-conformant"
    target = "%s@%s" % (data.get("name") or "?", data.get("version") or "?")
    return _report("pack", target, checks, verdict, "core", False,
                   0 if ok else 1)


# --------------------------------------------------------------------------- #
# Team mode
# --------------------------------------------------------------------------- #

def evidence_resolves(ev, base):
    """Evidence is a path that exists (abs or relative to base) or a valid URL."""
    if not isinstance(ev, str) or not ev.strip():
        return False
    s = ev.strip()
    if re.match(r"^[a-z][a-z0-9+.\-]*://\S+$", s, re.I):
        return True
    cand = s if os.path.isabs(s) else os.path.join(base, s)
    return os.path.exists(cand)


def _team_level_holds(by, level):
    for cid in TEAM_LEVELS[level]:
        c = by.get(cid)
        if c is None or c["status"] not in ("pass", "warn", "n/a"):
            return False
    return True


def build_team(path, level=None, schema=None):
    if os.path.isfile(path):
        cfg = path
        base = os.path.dirname(os.path.abspath(path)) or "."
    else:
        cfg = os.path.join(path, ".adlc", "conformance.yaml")
        base = path
        if not os.path.isfile(cfg):
            raise InputError("no .adlc/conformance.yaml under %s" % path)
    try:
        with open(cfg, encoding="utf-8") as f:
            data = mini_yaml_load(f.read())
    except (YamlError, ValueError, OSError) as e:
        raise InputError("cannot parse %s: %s" % (cfg, e))
    if not isinstance(data, dict):
        raise InputError("%s is not a mapping" % cfg)

    claimed = level or data.get("level")
    if claimed not in TEAM_LEVELS:
        raise InputError("unknown or absent team level: %r" % claimed)
    declared = data.get("checks") or {}
    if not isinstance(declared, dict):
        raise InputError("'checks' must be a mapping")

    checks = []
    for cid in TEAM_LEVELS[claimed]:
        if cid == "T-X1":
            checks.append(chk("T-X1", "not-run",
                              "certification program not operational "
                              "(defined, not runnable)"))
            continue
        entry = declared.get(cid)
        if not isinstance(entry, dict):
            checks.append(chk(cid, "fail", "required check missing from manifest"))
            continue
        status = entry.get("status")
        reason = entry.get("reason")
        evidence = entry.get("evidence")
        if status not in ("pass", "fail", "warn", "n/a"):
            checks.append(chk(cid, "fail", "invalid status %r" % status))
            continue
        if status == "fail":
            checks.append(chk(cid, "fail", "declared fail"))
            continue
        if status in ("warn", "n/a"):
            if not reason:
                checks.append(chk(cid, "fail", "status %s needs a reason" % status))
            else:
                checks.append(chk(cid, status, "reason: %s" % reason))
            continue
        # status == pass: evidence must resolve.
        if evidence_resolves(evidence, base):
            checks.append(chk(cid, "pass", "evidence resolves"))
        else:
            checks.append(chk(cid, "fail",
                              "evidence does not resolve: %r" % evidence))

    by = {c["id"]: c for c in checks}
    holds_claimed = _team_level_holds(by, claimed)
    achieved = None
    for lv in ("certified", "governed", "core"):
        if _team_level_holds(by, lv):
            achieved = lv
            break
    verdict = "conformant" if holds_claimed else "not-conformant"
    attested = any(PROVENANCE[c["id"]] in ("attest", "audit")
                   for c in checks if c["status"] == "pass")
    target = "%s (claims %s)" % (os.path.basename(os.path.abspath(base)) or base,
                                 claimed)
    return _report("team", target, checks, verdict,
                   achieved or "(none)", attested, 0 if holds_claimed else 1)


# --------------------------------------------------------------------------- #
# Harness mode (probe contract). The checker defines the probes; a fixture (the
# adapter's test suite) supplies the results. No live adapter is driven here.
# --------------------------------------------------------------------------- #

def build_harness(path, level=None, schema=None):
    if not os.path.isfile(path):
        checks = [chk("H1", "not-run", "derived; probes not run")]
        for cid in ("H2", "H3-intool", "H4", "H5"):
            checks.append(chk(cid, "not-run",
                              "run the harness probes in the adapter's test "
                              "suite (no fixture given)"))
        return _report("harness", path, checks, "not-conformant", "core",
                       False, 1)
    try:
        data = load_data(path)
    except (ValueError, YamlError, OSError) as e:
        raise InputError("cannot read fixture %s: %s" % (path, e))
    if not isinstance(data, dict):
        raise InputError("harness fixture %s is not a mapping" % path)
    probes = data.get("checks") if isinstance(data.get("checks"), dict) else data
    base = os.path.dirname(os.path.abspath(path)) or "."

    def read(cid):
        e = probes.get(cid)
        if isinstance(e, dict):
            return e.get("status"), (e.get("evidence") or e.get("note"))
        return (e if isinstance(e, str) else None), None

    checks = []
    for cid in ("H2", "H4", "H5"):
        s, _ = read(cid)
        st = "pass" if s == "pass" else ("fail" if s == "fail" else "not-run")
        checks.append(chk(cid, st, "probe: %s" % s if s else "no probe result"))

    s_in, _ = read("H3-intool")
    s_ex, ev_ex = read("H3-external")
    if s_in == "pass":
        checks.append(chk("H3-intool", "pass", "in-tool enforcement demonstrated"))
        h3_ok = True
    elif s_ex == "pass" and evidence_resolves(ev_ex, base):
        checks.append(chk("H3-external", "pass",
                          "external control denial (audit evidence resolves)"))
        h3_ok = True
    elif s_ex == "pass":
        checks.append(chk("H3-external", "fail",
                          "external denial claimed but evidence does not resolve"))
        h3_ok = False
    else:
        checks.append(chk("H3-intool",
                          "fail" if s_in == "fail" else "not-run",
                          "no enforcement demonstrated (in-tool or external)"))
        h3_ok = False

    by = {c["id"]: c for c in checks}
    core_ok = (h3_ok and all(by[c]["status"] == "pass"
                             for c in ("H2", "H4", "H5")))
    checks.insert(0, chk("H1", "pass" if core_ok else "fail",
                         "derived from H2, H3, H4, H5"))
    attested = any(PROVENANCE[c["id"]] == "audit"
                   for c in checks if c["status"] == "pass")
    return _report("harness", os.path.basename(path), checks,
                   "conformant" if core_ok else "not-conformant", "core",
                   attested, 0 if core_ok else 1)


# --------------------------------------------------------------------------- #
# Rendering
# --------------------------------------------------------------------------- #

def render_human(r, quiet):
    if r["verdict"] == "error":
        print("adlc-check %s  %s" % (r["subject"], r["target"]))
        print("\n  ERROR: %s   (exit %d)" % (r.get("error", ""), r["exitCode"]))
        return
    if not quiet:
        print("adlc-check %s  %s\n" % (r["subject"], r["target"]))
        for c in r["checks"]:
            print("  %-11s %-8s %-7s %s"
                  % (c["id"], c["status"], c["provenance"], c["note"]))
        print()
    flag = ("  [attested, not machine-proven]"
            if r["attested"] and r["verdict"] == "conformant" else "")
    lvl = " at level %s" % r["level"] if r["level"] and r["level"] != "(none)" else ""
    print("  VERDICT: %s%s%s   (exit %d)"
          % (r["verdict"], lvl, flag, r["exitCode"]))


# --------------------------------------------------------------------------- #
# Self-test
# --------------------------------------------------------------------------- #

def run_selftest():
    schema = load_schema()
    failures = []
    valid = os.path.join(ROOT, "standard", "schema", "example-pack.manifest.json")
    invalid = os.path.join(ROOT, "standard", "schema",
                           "example-pack-invalid.manifest.json")
    for label, target, want in (("valid example", valid, 0),
                                ("invalid example", invalid, 1)):
        try:
            code = build_pack(target, schema=schema)["exitCode"]
        except InputError as e:
            failures.append("%s: raised %s" % (label, e))
            continue
        if code != want:
            failures.append("%s: expected exit %d, got %d" % (label, want, code))

    packs = sorted(p for p in glob.glob(os.path.join(ROOT, "plugins", "*"))
                   if os.path.isdir(p))
    for p in packs:
        name = os.path.basename(p)
        try:
            r = build_pack(p, schema=schema)
        except InputError as e:
            failures.append("%s: raised %s" % (name, e))
            continue
        if r["exitCode"] != 0:
            bad = [c["id"] for c in r["checks"] if c["status"] == "fail"]
            failures.append("%s: expected conformant, got %s %s"
                            % (name, r["verdict"], bad))

    print("SELFTEST: %s  (%d packs, 2 example manifests)"
          % ("PASS" if not failures else "FAIL", len(packs)))
    for f in failures:
        print("  - " + f)
    return 0 if not failures else 1


# --------------------------------------------------------------------------- #
# Entry point
# --------------------------------------------------------------------------- #

BUILDERS = {"pack": build_pack, "team": build_team, "harness": build_harness}


def main(argv):
    flags = {"json": False, "quiet": False, "level": None, "selftest": False}
    positional = []
    i = 1
    while i < len(argv):
        a = argv[i]
        if a == "--json":
            flags["json"] = True
        elif a == "--quiet":
            flags["quiet"] = True
        elif a == "--selftest":
            flags["selftest"] = True
        elif a == "--level":
            i += 1
            if i >= len(argv):
                err("--level needs a value")
                return 2
            flags["level"] = argv[i]
        elif a.startswith("--level="):
            flags["level"] = a.split("=", 1)[1]
        elif a in ("-h", "--help"):
            print(USAGE)
            return 0
        elif a.startswith("-"):
            err("unknown flag: %s\n%s" % (a, USAGE))
            return 2
        else:
            positional.append(a)
        i += 1

    if flags["selftest"]:
        try:
            return run_selftest()
        except InputError as e:
            err("selftest error: %s" % e)
            return 2

    if len(positional) != 2:
        err(USAGE)
        return 2
    subject, path = positional
    if subject not in BUILDERS:
        err("unknown subject %r\n%s" % (subject, USAGE))
        return 2

    try:
        report = BUILDERS[subject](path, level=flags["level"])
    except InputError as e:
        report = _report(subject, path, [], "error", None, False, 2, error=str(e))
    except Exception as e:  # fail-closed: never crash into a traceback
        report = _report(subject, path, [], "error", None, False, 2,
                         error="unexpected: %s" % e)

    if flags["json"]:
        print(json.dumps(report, indent=2))
    else:
        render_human(report, flags["quiet"])
    return report["exitCode"]


if __name__ == "__main__":
    sys.exit(main(sys.argv))
