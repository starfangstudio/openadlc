#!/usr/bin/env python3
# SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0
"""ip-boundary-gate: the IP-boundary leak gate for the public repo (FAIL-CLOSED).

The public repo (openadlc) carries ONLY the open standard plus the
broad-spectrum free solution; every enterprise mechanism lives in the private
enterprise repo (the IP boundary law, R75). This gate scans the FULL public
tree for the enterprise-marker terms that must never appear here and fails the
build on any hit outside an explicit allowlisted teaching-content line.
Stdlib-only Python 3, no network, no git. Runs anywhere Python 3 runs (no shell
builtins, so bash 3.2 is irrelevant).

  python3 tools/ip-boundary-gate.py [path ...]
    path   one or more files/dirs to scan (default: the repo root).

Exit codes: 0 clean, 1 one or more leaks, 2 fail-closed (zero files read).

The marker terms are base64-encoded below so this PUBLIC file never holds the
literal enterprise vocabulary it guards against (the same reason canon-gate.py
stores the em-dash by codepoint: a leak gate must not itself be the leak).
Decode to read or extend the list; the decoded content is the full marker list
from planning/v1/ip-boundary.md (the enterprise markers plus the additional
private terms it names). Matching is case-insensitive, one marker per line.
"""
import sys
import os
import base64
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# The marker list, base64-encoded (see the module docstring for why): every
# marker named in ip-boundary.md.
# Decodes to one marker per line.
_MARKERS_B64 = (
    "ZW50ZXJwcmlzZSBzb2NrZXQKb3JnX25vdGVzCnJldmlldyByb29tCndlZWtseSBwYXNz"
    "CmVudGl0bGVtZW50LWFzLW91ci1saWNlbnNpbmcKUEFTRVRPCndhdGVybWFyawpzZWF0"
    "IGF0dGVzdGF0aW9uCm9yZ19hZG1pbgpnaWZ0IGNyZWRpdAp0cnVlLXVwCmR1bm5pbmcK"
    "b3BlbmFkbGMgbm90ZXMKbG9jYWxfbm90ZXMKbWVtb3J5LWZvcm1hdApNRU0t"
)
MARKERS = [m for m in base64.b64decode(_MARKERS_B64).decode("utf-8").split("\n")
           if m]

# Directories never scanned: VCS, build caches, vendored trees, retired content.
SKIP_DIRS = {".git", "__pycache__", "node_modules", ".DS_Store", "_retired"}

# Binary / media extensions to skip outright (a NUL-byte probe catches the rest).
BINARY_EXT = {
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".ico", ".bmp",
    ".pdf", ".woff", ".woff2", ".ttf", ".otf", ".eot",
    ".mp4", ".mp3", ".wav", ".mov", ".webm", ".zip", ".gz", ".tar",
}

# This gate's own source IS scanned (so a literal term in its docstring or
# comments is caught); only the base64 marker-block lines are allowlisted.
SELF = os.path.abspath(__file__)


# The allowlist: explicit, reasoned exceptions for a legitimate teaching-content
# line that names a marker term in order to teach or prohibit it. Each entry is
# (marker-or-"*", path-substring-or-None, line-regex-or-None, reason); a hit is
# suppressed only when an entry covers the marker AND every set condition holds.
# Empty today: the public tree carries no marker after the R75 extraction.
ALLOWLIST = []


def allowlisted(marker, relpath, line):
    for mk, path_sub, line_re, _reason in ALLOWLIST:
        if mk != "*" and mk != marker:
            continue
        if path_sub and path_sub not in relpath:
            continue
        if line_re and not re.search(line_re, line):
            continue
        return True
    return False


def iter_files(targets):
    for t in targets:
        base = t if os.path.isabs(t) else os.path.join(ROOT, t)
        if os.path.isfile(base):
            yield base
        elif os.path.isdir(base):
            for r, dirs, files in os.walk(base):
                dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
                for name in files:
                    if os.path.splitext(name)[1].lower() in BINARY_EXT:
                        continue
                    yield os.path.join(r, name)


def read_text(path):
    try:
        with open(path, "rb") as fh:
            raw = fh.read()
    except OSError:
        return None
    if b"\x00" in raw[:65536]:
        return None
    return raw.decode("utf-8", errors="replace")


def scan(targets):
    """Return (violations, files_read). A violation is a dict with file/line."""
    violations = []
    files_read = 0
    lowered = [(m, m.lower()) for m in MARKERS]
    b64_line = re.compile(r'^\s*"[A-Za-z0-9+/=]+"\s*$')
    for path in iter_files(targets):
        text = read_text(path)
        if text is None:
            continue
        files_read += 1
        relpath = os.path.relpath(path, ROOT)
        is_self = os.path.abspath(path) == SELF
        for lineno, line in enumerate(text.splitlines(), 1):
            # Scan this gate's own file too; allowlist only the base64 block.
            if is_self and b64_line.match(line):
                continue
            low = line.lower()
            for marker, mlow in lowered:
                if mlow in low and not allowlisted(marker, relpath, line):
                    violations.append({
                        "file": relpath, "line": lineno,
                        "snippet": line.strip()[:120],
                    })
    return violations, files_read


def main(argv):
    targets = argv[1:] if len(argv) > 1 else [ROOT]
    violations, files_read = scan(targets)

    if files_read == 0:
        print("ip-boundary-gate: FAIL-CLOSED (zero files scanned)")
        return 2

    if not violations:
        print("ip-boundary-gate: PASS  (%d files scanned, no enterprise markers)"
              % files_read)
        return 0

    print("ip-boundary-gate: FAIL  (%d files scanned, %d leak(s))\n"
          % (files_read, len(violations)))
    for v in violations:
        print("  %s:%d: enterprise marker present  -> belongs in the private repo"
              % (v["file"], v["line"]))
        print("      | %s" % v["snippet"])
    print("\nRESULT: FAIL (%d enterprise-marker leak(s) in the public tree)"
          % len(violations))
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
