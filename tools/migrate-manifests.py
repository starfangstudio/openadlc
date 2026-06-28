#!/usr/bin/env python3
# SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0
"""One-time manifest migration to the conformant pack format (G1-G7). Idempotent.

Adds, without removing harness-compat fields:
- owner {name, contact}  (G2; author is KEPT for Claude Code compatibility)
- adlc                    (G1; the ADLC standard version the pack targets)
- units                  (G1; generated from the folder tree)
- evals                  (G3; the eval bar the pack clears)
- capabilities           (G4; default-deny, {} for guidance packs)

Usage: python3 tools/migrate-manifests.py
"""
import os, json, glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLUGINS = os.path.join(ROOT, "plugins")
CONTACT = "https://openadlc.com"

def n(pdir, sub, pat):
    return len(glob.glob(os.path.join(pdir, sub, pat)))

for mf in sorted(glob.glob(os.path.join(PLUGINS, "*", ".claude-plugin", "plugin.json"))):
    pdir = os.path.dirname(os.path.dirname(mf))
    d = json.load(open(mf, encoding="utf-8"))

    name = d.get("author", {}).get("name", "OpenADLC") if isinstance(d.get("author"), dict) else "OpenADLC"
    owner = d.get("owner") if isinstance(d.get("owner"), dict) else {}
    owner.setdefault("name", name)
    owner.setdefault("contact", CONTACT)
    d["owner"] = owner

    d.setdefault("adlc", "0.1")
    d["units"] = {
        "skills": n(pdir, "skills", "*"),
        "agents": n(pdir, "agents", "*.md"),
        "commands": n(pdir, "commands", "*.md"),
        "references": n(pdir, "references", "*.md"),
    }
    has_evals = os.path.isdir(os.path.join(pdir, "evals"))
    d.setdefault("evals", "conformance+gate" if has_evals else "conformance")
    d.setdefault("capabilities", {})

    order = ["name", "version", "description", "author", "owner", "adlc", "units", "evals", "capabilities"]
    out = {k: d[k] for k in order if k in d}
    for k in d:
        if k not in out:
            out[k] = d[k]

    open(mf, "w", encoding="utf-8").write(json.dumps(out, indent=2, ensure_ascii=True) + "\n")
    print(f"migrated {os.path.relpath(mf, ROOT)}")
