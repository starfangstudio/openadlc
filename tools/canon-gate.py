#!/usr/bin/env python3
# SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0
"""canon-gate: the vocabulary gate for OpenADLC's public surface (FAIL-CLOSED).

A commit-time gate that fails the build when banned vocabulary appears in the
public documentation surface, so old naming cannot drift back in unnoticed. It
scans the surface, prints every violation as file:line with a neutral reason,
and exits non-zero if any survive. Stdlib-only Python 3, no network, no git.
Matches the style of tools/adlc-check.py and tools/check-packs.py.

  python3 tools/canon-gate.py [path ...]
    path   one or more files/dirs to scan (default: the public surface below).

Exit codes: 0 clean, 1 one or more violations, 2 fail-closed (zero files read).

Each banned pattern carries a NEUTRAL reason. A small, explicit allowlist holds
the legitimate exceptions (each a reasoned rule keyed on the matched text, the
line, and/or the path), so the gate stays precise instead of skipping whole
files. The one exception with zero tolerance is the em-dash: never allowlisted.
"""
import sys
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# The public surface to scan (relative to the repo root). Directories are walked
# recursively. tools/ is deliberately absent: this script carries the banned
# patterns as data and must never flag itself.
SCAN_SURFACE = [
    "standard",
    "plugins/adlc-core",
    "docs",
    "README.md",
    "CONFORMANCE.md",
    "LICENSE",
    "NOTICE",
]

# Directories never scanned: VCS, retired content (allowed to keep old naming),
# build caches, and vendored trees.
SKIP_DIRS = {".git", "_retired", "__pycache__", "node_modules", ".DS_Store"}

# Binary / media file extensions to skip outright (a NUL-byte probe catches the
# rest, e.g. .DS_Store).
BINARY_EXT = {
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".ico", ".bmp",
    ".pdf", ".woff", ".woff2", ".ttf", ".otf", ".eot",
    ".mp4", ".mp3", ".wav", ".mov", ".webm", ".zip", ".gz", ".tar",
}

EMDASH = chr(0x2014)  # em-dash, by codepoint so this file never holds the literal


# --------------------------------------------------------------------------- #
# The banned patterns. Each is (id, compiled-regex, reason). Reasons are neutral
# and describe the correct naming, never a decision id.
# --------------------------------------------------------------------------- #

PATTERNS = [
    # 1. Command names.
    ("agentic-cmd", re.compile(r"/agentic-", re.I),
     "commands are /ai-*"),

    # 2. Dead tier names. Bare 'tier' (adapter tiers, conformance tiers) is fine;
    # only the numbered tiers and the retired named tiers are matched.
    ("tier-numbered", re.compile(r"\btier ?[12]\b", re.I),
     "one paid tier (Enterprise); Individual is free"),
    ("tier-named", re.compile(
        r"\b(?:(?:team|advanced) tier|tier (?:team|advanced)"
        r"|tier ?: ?(?:team|advanced))\b", re.I),
     "one paid tier (Enterprise); Individual is free"),

    # 3. Dead tier names.
    ("tier-promax", re.compile(r"\b(?:pro|max) tier\b", re.I),
     "dead tier names"),

    # 4. The standard says pull request. The phrase requires whitespace, so a
    # GitLab code identifier (merge_request) never matches; the ' MR ' token is
    # case-sensitive and space-bounded.
    ("merge-request", re.compile(r"merge[ \t]+request", re.I),
     "the standard says pull request"),
    ("mr-token", re.compile(r"(?<= )MR(?= )"),
     "the standard says pull request"),

    # 5. Removed product word.
    ("fleet", re.compile(r"\bfleet", re.I),
     "the word was removed from product vocabulary"),

    # 7. Deleted bots.
    ("dead-bots", re.compile(
        r"\b(?:gate-bot|retro-bot|legibility-bot|audit-bot)\b", re.I),
     "deleted bots"),

    # 8. Dead concept.
    ("batched-prs", re.compile(r"\bbatched PRs\b", re.I),
     "dead concept"),

    # 9. No spend or measurement in product copy. 'spend'/'cost'/'budget' are
    # ordinary English (cost of change, spends attention, error/perf budgets),
    # so they are matched ONLY in a spend/measurement SENSE: bound to a tracking
    # noun (ledger/meter/dashboard/limit/remaining/tracking), a tracking verb
    # (track/reduce/estimate/monthly/total/your/projected/actual, immediately
    # adjacent), or a number. This is the "scope to product copy/fields/metrics"
    # the surface needs; ordinary idiom and domain budgets pass untouched.
    ("money-metric", re.compile(
        r"\b(?:spend|cost|budget)s?\s+"
        r"(?:tracking|tracker|ledger|meter(?:ing|ed)?|dashboard"
        r"|limit|cap|remaining|report)\b"
        r"|\b(?:track(?:ing)?|reduc(?:e|ing)|estimate[ds]?|monthly|total"
        r"|your|projected|actual)\s+(?:spend|cost|budget)s?\b"
        r"|\b(?:spend|cost|budget)s?\s+(?:of\s+)?\$?\d", re.I),
     "no spend or measurement in product copy"),
    ("dollar-amount", re.compile(r"\$\d[\d,]*(?:\.\d+)?"),
     "no spend or measurement in product copy"),
    ("tokens-saved", re.compile(r"\btokens saved\b", re.I),
     "no spend or measurement in product copy"),
    ("roi", re.compile(r"\bROI\b"),
     "no spend or measurement in product copy"),

    # 10. Gate modes are lax / normal / strict.
    ("enforcement-mode", re.compile(r"\benforcement mode\b", re.I),
     "gate modes are lax / normal / strict"),

    # 11. Dead metric.
    ("edited-then-consented", re.compile(r"\bedited then consented\b", re.I),
     "dead metric"),

    # 12. The em-dash: never, anywhere. Zero tolerance, no allowlist.
    ("em-dash", re.compile(re.escape(EMDASH)),
     "never, anywhere"),

    # 13. Dead concept.
    ("daily-digest", re.compile(r"\bdaily digest\b", re.I),
     "dead concept"),

    # 14. Deleted screens / routes.
    ("dead-routes", re.compile(
        r"\b(?:cost-ledger|command-palette|pack-index|api-reference)\b", re.I),
     "deleted screens/routes"),
]


# --------------------------------------------------------------------------- #
# The allowlist. Each entry is an explicit, reasoned exception. A hit is
# suppressed only when an entry's `patterns` covers it AND every condition it
# sets (matched-text, line-text, path) holds. An entry MUST set at least one
# condition; a naked file skip is never allowed here. The em-dash pattern is
# listed by no entry, so it can never be suppressed.
# --------------------------------------------------------------------------- #

class Allow:
    def __init__(self, patterns, reason, match_re=None, line_re=None,
                 path_re=None):
        self.patterns = patterns            # set of pattern ids, or "*"
        self.reason = reason
        self.match_re = re.compile(match_re) if match_re else None
        self.line_re = re.compile(line_re) if line_re else None
        self.path_re = re.compile(path_re) if path_re else None

    def covers(self, pid):
        return self.patterns == "*" or pid in self.patterns

    def allows(self, matched, line, relpath):
        if self.match_re and not self.match_re.search(matched):
            return False
        if self.line_re and not self.line_re.search(line):
            return False
        if self.path_re and not self.path_re.search(relpath):
            return False
        return True


ALLOWLIST = [
    # Copy-law meta-mention: a sentence that QUOTES "merge request"/"MR" in order
    # to prohibit it (e.g. `"merge request/MR" banned`, `never "merge request"`).
    # It only fires on a line that already contains the term, so it stays precise.
    Allow({"merge-request", "mr-token"},
          "copy-law statement of the ban (quotes the term to prohibit it)",
          line_re=(r"(?i)(?:banned|never |not |instead of |say |use )"
                   r"[\"'“]?(?:merge[ \t]+request|MR)"
                   r"|[\"'“]merge request/MR[\"'”]")),

    # GitLab API field names live in code identifiers with underscores
    # (merge_request*), which the space-requiring phrase already never matches;
    # this documents the exception explicitly for a backticked identifier line.
    Allow({"merge-request", "mr-token"},
          "GitLab API field name inside a code identifier",
          line_re=r"`[^`]*(?:merge_request|mr_iid|merge_requests)[^`]*`"),

    # Copy-law disclaimer: a line that explicitly REFUSES a measurement (e.g. a
    # doc stating it computes no effectiveness/ROI/savings metric). Analogous to
    # the merge-request meta-mention: the term appears in order to be prohibited.
    # Only fires on a line already carrying a measurement word.
    Allow({"roi", "tokens-saved", "money-metric", "dollar-amount"},
          "copy-law disclaimer: the doc explicitly refuses this measurement",
          line_re=(r"(?i)(?:no effectiveness|claims no|derives no|no measurement"
                   r"|never measures|not measured|without (?:any )?measurement"
                   r"|no usage-measurement|no .*metric to reintroduce)")),

    # SQL / shell positional placeholder ($1..$9), not a price. Keyed on the
    # matched token itself so a real price like $20 on the same line still fails.
    Allow({"dollar-amount"},
          "positional placeholder ($1..$9), not a price",
          match_re=r"^\$[1-9]$"),
]


def allowlisted(pid, matched, line, relpath):
    """Return the reason if some allowlist entry permits this hit, else None."""
    for a in ALLOWLIST:
        if a.covers(pid) and a.allows(matched, line, relpath):
            return a.reason
    return None


# --------------------------------------------------------------------------- #
# File collection and scanning.
# --------------------------------------------------------------------------- #

def iter_files(targets):
    """Yield absolute paths of every scannable file under the given targets."""
    for t in targets:
        base = t if os.path.isabs(t) else os.path.join(ROOT, t)
        if os.path.isfile(base):
            yield base
        elif os.path.isdir(base):
            for r, dirs, files in os.walk(base):
                dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
                for name in files:
                    if name in SKIP_DIRS:
                        continue
                    if os.path.splitext(name)[1].lower() in BINARY_EXT:
                        continue
                    yield os.path.join(r, name)


def read_text(path):
    """Return the file's text, or None if it is binary / unreadable."""
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
    for path in iter_files(targets):
        text = read_text(path)
        if text is None:
            continue
        files_read += 1
        relpath = os.path.relpath(path, ROOT)
        for lineno, line in enumerate(text.splitlines(), 1):
            for pid, rx, reason in PATTERNS:
                for m in rx.finditer(line):
                    matched = m.group(0)
                    if allowlisted(pid, matched, line, relpath):
                        continue
                    violations.append({
                        "file": relpath, "line": lineno,
                        "pattern": pid, "reason": reason,
                        "text": matched, "snippet": line.strip()[:120],
                    })
    return violations, files_read


def main(argv):
    targets = argv[1:] if len(argv) > 1 else SCAN_SURFACE
    violations, files_read = scan(targets)

    if files_read == 0:
        print("canon-gate: FAIL-CLOSED (zero files scanned)")
        return 2

    if not violations:
        print("canon-gate: PASS  (%d files scanned, no banned vocabulary)"
              % files_read)
        return 0

    print("canon-gate: FAIL  (%d files scanned, %d violation(s))\n"
          % (files_read, len(violations)))
    for v in violations:
        print("  %s:%d: %r  -> %s"
              % (v["file"], v["line"], v["text"], v["reason"]))
        print("      | %s" % v["snippet"])
    print("\nRESULT: FAIL (%d banned-vocabulary hit(s))" % len(violations))
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
