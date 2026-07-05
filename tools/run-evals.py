#!/usr/bin/env python3
# SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0
"""OpenADLC behavioral eval runner (P3b plumbing, FAIL-CLOSED).

The deterministic half of the behavioral eval. It discovers a pack's eval
cases, validates their shape, and turns an agent-filled scores.json into a
P3b verdict in the conformance checker's report shape. It never runs the
agent and never judges a signal; that is the agent's job (see
docs/eval-format.md, "Running an eval").

Usage:
  python3 tools/run-evals.py <pack>                 validate + print the run plan
  python3 tools/run-evals.py <pack> --score s.json  score + print the report
  python3 tools/run-evals.py all                    validate every pack's suite

Exit codes (match the conformance checker):
  0  P3b pass, or not-run (no cases)
  1  P3b fail (aggregate delta <= 0, or a must_not observed in treatment)
  2  usage or input error (bad path, malformed eval file, em-dash, bad scores)

Stdlib only. No new runtime dependencies.
"""
import sys, os, re, json, glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLUGINS = os.path.join(ROOT, "plugins")


def die(msg):
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(2)


def has_emdash(t):
    return ("\u2014" in t) or ("\\u2014" in t)


def frontmatter(text):
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    fm = {}
    for line in text[4:end].splitlines():
        m = re.match(r"^([A-Za-z0-9_-]+):\s*(\S.*)$", line)
        if m:
            fm[m.group(1)] = m.group(2).strip()
    return fm


def fenced_after(text, heading):
    """Return the body of the first fenced block after a heading, or None."""
    idx = text.find(heading)
    if idx == -1:
        return None
    rest = text[idx + len(heading):]
    open_m = re.search(r"^```[A-Za-z0-9]*\n", rest, re.M)
    if not open_m:
        return None
    body = rest[open_m.end():]
    close_m = re.search(r"^```\s*$", body, re.M)
    if not close_m:
        return None
    return body[:close_m.start()]


def parse_case(path):
    """Parse one .eval.md into a case dict; raise ValueError with a clear reason."""
    t = open(path, encoding="utf-8").read()
    r = os.path.relpath(path, ROOT)
    errs = []
    if has_emdash(t):
        errs.append("em-dash (banned)")
    fm = frontmatter(t)
    cid = fm.get("id")
    if not cid:
        errs.append("no 'id' in frontmatter")
    targets = [x.strip() for x in fm.get("targets", "").split(",") if x.strip()]
    if not targets:
        errs.append("no 'targets' in frontmatter")
    scenario = fenced_after(t, "## Scenario")
    if not scenario or not scenario.strip():
        errs.append("missing or empty '## Scenario' fenced block")
    raw = fenced_after(t, "## Assertions")
    assertions = []
    if raw is None:
        errs.append("missing '## Assertions' fenced block")
    else:
        try:
            assertions = json.loads(raw)
        except Exception as e:
            errs.append(f"assertions JSON does not parse: {e}")
        if not isinstance(assertions, list) or not assertions:
            errs.append("assertions must be a non-empty JSON list")
            assertions = []
    seen = set()
    for i, a in enumerate(assertions):
        if not isinstance(a, dict):
            errs.append(f"assertion {i} is not an object"); continue
        aid = a.get("id")
        if not aid or aid in seen:
            errs.append(f"assertion {i}: missing or duplicate id")
        seen.add(aid)
        if a.get("type") not in ("must", "must_not"):
            errs.append(f"assertion '{aid}': type must be must|must_not")
        p = a.get("points")
        if isinstance(p, bool) or not isinstance(p, int) or p < 0:
            errs.append(f"assertion '{aid}': points must be a non-negative int")
        if not a.get("signal"):
            errs.append(f"assertion '{aid}': missing signal")
        tgt = a.get("target")
        if tgt not in targets:
            errs.append(f"assertion '{aid}': target '{tgt}' not in the case targets {targets}")
    if errs:
        raise ValueError(f"{r}: " + "; ".join(errs))
    return {"id": cid, "path": r, "targets": targets,
            "scenario": scenario.strip(), "assertions": assertions}


def discover(pack):
    pdir = os.path.join(PLUGINS, pack)
    if not os.path.isdir(pdir):
        die(f"pack '{pack}' not found under plugins/")
    files = sorted(glob.glob(os.path.join(pdir, "evals", "*.eval.md")))
    cases = [parse_case(f) for f in files]  # raises on the first malformed file
    ids = [c["id"] for c in cases]
    if len(ids) != len(set(ids)):
        die(f"pack '{pack}' has duplicate case ids: {ids}")
    return cases


def print_plan(pack, cases):
    if not cases:
        print(json.dumps({"pack": pack, "status": "not-run",
                          "note": "no eval cases; P3b does not gate"}, indent=2))
        return
    plan = {"pack": pack, "cases": [
        {"id": c["id"], "targets": c["targets"], "scenario": c["scenario"],
         "assertions": c["assertions"]} for c in cases]}
    print(json.dumps(plan, indent=2))


def score(pack, cases, scores_path):
    if not cases:
        report = {"spec": "0.1", "runner": "0.1", "subject": "pack", "target": pack,
                  "check": {"id": "P3b", "status": "not-run", "provenance": "auto",
                            "note": "no eval cases"},
                  "cases": [], "verdict": "not-run", "exitCode": 0}
        print(json.dumps(report, indent=2)); sys.exit(0)
    try:
        s = json.load(open(scores_path, encoding="utf-8"))
    except Exception as e:
        die(f"cannot read scores file '{scores_path}': {e}")
    runs = s.get("runs", {})
    out_cases, total_delta, mustnot_hit = [], 0, False
    for c in cases:
        r = runs.get(c["id"])
        if not isinstance(r, dict) or "baseline" not in r or "treatment" not in r:
            die(f"scores missing baseline/treatment for case '{c['id']}'")
        base, treat = r["baseline"], r["treatment"]
        for a in c["assertions"]:
            for cond, d in (("baseline", base), ("treatment", treat)):
                if a["id"] not in d:
                    die(f"scores case '{c['id']}' {cond} missing assertion '{a['id']}'")
        b_score = sum(a["points"] for a in c["assertions"]
                      if a["type"] == "must" and base[a["id"]])
        t_score = sum(a["points"] for a in c["assertions"]
                      if a["type"] == "must" and treat[a["id"]])
        violated = any(a["type"] == "must_not" and treat[a["id"]] for a in c["assertions"])
        mustnot_hit = mustnot_hit or violated
        total_delta += (t_score - b_score)
        out_cases.append({"id": c["id"], "baseline": b_score, "treatment": t_score,
                          "delta": t_score - b_score, "mustNotViolated": violated})
    if mustnot_hit:
        status, exit_code = "fail", 1
        note = "a must_not was observed in a treatment run"
    elif total_delta <= 0:
        status, exit_code = "fail", 1
        note = f"aggregate delta {total_delta:+d} does not beat the baseline"
    else:
        status, exit_code = "pass", 0
        note = f"aggregate delta {total_delta:+d} across {len(cases)} cases; 0 must-not violations"
    report = {"spec": "0.1", "runner": "0.1", "subject": "pack", "target": pack,
              "check": {"id": "P3b", "status": status, "provenance": "auto", "note": note},
              "cases": out_cases, "verdict": status, "exitCode": exit_code}
    print(json.dumps(report, indent=2))
    sys.exit(exit_code)


def validate_all():
    packs = sorted(os.path.basename(p) for p in glob.glob(os.path.join(PLUGINS, "*"))
                   if os.path.isdir(p))
    bad = 0
    for pack in packs:
        files = sorted(glob.glob(os.path.join(PLUGINS, pack, "evals", "*.eval.md")))
        if not files:
            print(f"  {pack}: no evals (P3b not-run)"); continue
        try:
            cases = discover(pack)
            print(f"  {pack}: {len(cases)} case(s) valid")
        except ValueError as e:
            bad += 1
            print(f"  {pack}: INVALID - {e}")
    print(f"\npacks: {len(packs)} | suites with a problem: {bad}")
    sys.exit(2 if bad else 0)


def main():
    if len(sys.argv) < 2:
        die("usage: run-evals.py <pack|all> [--score scores.json]")
    target = sys.argv[1]
    if target == "all":
        validate_all(); return
    try:
        cases = discover(target)
    except ValueError as e:
        die(str(e))
    if "--score" in sys.argv:
        i = sys.argv.index("--score")
        if i + 1 >= len(sys.argv):
            die("--score needs a path to a scores.json")
        score(target, cases, sys.argv[i + 1])
    else:
        print_plan(target, cases)


if __name__ == "__main__":
    main()
