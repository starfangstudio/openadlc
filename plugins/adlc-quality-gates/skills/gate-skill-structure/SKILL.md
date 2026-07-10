---
name: gate-skill-structure
description: "This skill should be used when the user asks to \"lint a skill\", \"check a SKILL.md\", \"validate skill structure\", \"review my skill against Anthropic guidelines\", \"gate a skill before merge\", or otherwise wants a SKILL.md checked for correct frontmatter, body length, progressive disclosure, and one-level references. Runs a structural quality gate over a single SKILL.md and reports PASS or FAIL with line-anchored fixes."
version: 0.2.0
---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# Gate: SKILL.md structure

Lint one `SKILL.md` against Anthropic's skill-authoring rules and this project's discipline. This gate checks STRUCTURE only, not whether the skill works (that is gate-skill-efficacy).

Every check below is a declarative verify-or-fail step you run with your own tools (`ls`, `grep`, `wc`, `awk`). There is no helper script: run the exact command, apply the exact rule. If a command errors (missing file, unreadable), that check is FAIL, not skipped.

## Inputs

Resolve the target once. Set `F` to the SKILL.md path, `SKILLDIR` to its directory, `PACKROOT` to the enclosing `plugins/<pack>/` directory.
- Use the path the user named, else: `find . -name SKILL.md -not -path '*/node_modules/*'`. More than one, list them and ask. Never guess.
- Read-only: report only. Edit only if the user asks after the report.

## Checks

Run all in order. Each emits PASS or FAIL with the offending line number(s).

### 1. Frontmatter present and parseable
`awk 'NR==1&&$0!="---"{print "no-open"} /^---$/{c++} END{print "closes="c}' "$F"`
FAIL if line 1 is not `---`, or fewer than two `---` fences exist.

### 2. name field
`grep -nE '^name:[[:space:]]*[a-z0-9-]+[[:space:]]*$' "$F"` and `basename "$SKILLDIR"`.
FAIL if no match (missing, empty, or contains uppercase, spaces, or other characters), if the value exceeds 64 chars, if it contains `anthropic` or `claude`, or if it does not equal the directory basename.

### 3. description is third-person, trigger-rich, no XML
`grep -nE '^description:' "$F"`.
FAIL if absent, over 1024 chars, contains a `<...>` tag, opens (after the quote) with `I `, `I can`, `I help`, `You `, `You can`, or `Use this to`, or contains no `when`/trigger phrasing (a real skill states BOTH what it does AND when to use it).

### 4. Body length and progressive disclosure
`awk 'f{n++} /^---$/{c++; if(c==2)f=1} END{print n}' "$F"` (lines after the second fence).
FAIL if > 500. FAIL if > 150 and no reference link exists in the body (`grep -qE '\]\((\.\./)*references/' "$F"`): past 150 lines detail must move into a linked reference file, not stay inlined.

### 5. References are one level deep
Collect body links: `grep -oE '\]\(([^)]+\.md)\)' "$F"`. For each linked `.md` that exists (resolved per check 6), scan it: `grep -oE '\]\(([^)]+\.md)\)' "<resolved>"`.
FAIL if any referenced file links onward to another `.md` (report the chain, e.g. `SKILL.md -> advanced.md -> details.md`). All reference files link directly from SKILL.md.

### 6. Every reference citation resolves at the link target
A reference citation shows a readable pack-relative name as DISPLAY text (`[references/<file>.md](target)`), but the LINK TARGET inside `(...)` is what must resolve: per spec.md 5.2, the target is file-relative so an editor, agentic coding tool, or grader can follow it from the citing file. For each `.md` link from check 5 (and each `scripts/`/asset path), resolve the target against `SKILLDIR`: `ls "$SKILLDIR/<target>"`. A target like `../../references/<file>.md` resolves to the pack-level `references/`; a bare `references/<file>.md` resolves only to the skill's OWN co-located `references/` subdir.
PASS if the target resolves. FAIL if it does not point at an existing file, or the path uses a backslash, or it uses an agentic-coding-tool-specific path variable (a plugin-root-style variable that resolves on only one deploy target) instead of naming the file. Name the file; do not hardcode a tool root. Judge the target, never the display text: `[references/foo.md](references/foo.md)` FAILs when `foo.md` lives at the pack root, because the target resolves to the skill's absent `references/foo.md`.

### 7. Long reference files have a table of contents
For each resolved `.md` reference over 100 lines (`wc -l`), WARN if it has no `## Contents` or table-of-contents section near the top (`grep -nE '^##+ (Contents|Table of contents)' "<resolved>"`).

### 8. Voice and hygiene (body)
WARN on second-person instruction voice (`grep -nE '\b(you should|you can|you must)\b' "$F"`), prefer imperative. WARN on time-sensitive phrasing (`grep -nE 'before [A-Z][a-z]+ 20|after 20[0-9][0-9]' "$F"`) outside an "Old patterns" or `<details>` block.

## Report format

Emit exactly this. No prose preamble.

```
# Skill structure gate: <path/to/SKILL.md>

RESULT: PASS | FAIL  (<n> failed, <m> warnings)

FAIL
- [check 4] Body is 612 lines (limit 500). Move detail to references/<topic>.md. (line 540)
- [check 6] Broken citation `[references/foo.md](references/foo.md)`: the target resolves to <skilldir>/references/foo.md, which is absent (the file lives at the pack root; cite it as `../../references/foo.md`). (line 88)

WARN
- [check 8] Second-person voice: "you should run". Use imperative. (line 92)

PASS
- [check 2] name "gate-skill-structure" valid, matches directory.
- [check 6] `[references/gate-skill-efficacy-detail.md](../../references/gate-skill-efficacy-detail.md)` target resolves.
```

Rules for the report:
- `RESULT: FAIL` if ANY check fails, else `PASS` (warnings never fail the gate).
- Every check (1-8) appears under exactly one of FAIL / WARN / PASS.
- Each FAIL/WARN names the check number, the problem, a one-line fix, and a `file:line` where applicable.

## Final gate (verify or fail)

The run MUST end with an explicit `RESULT: PASS` or `RESULT: FAIL` verdict, and the FAIL block MUST list every failed check with its `file:line` evidence. No silent partial pass: if you could not run a check, mark it FAIL with the reason. State the single most impactful fix. Apply fixes only if the user then asks, and re-run all 8 checks to green. No network, no outbound.

## When NOT to use

This gate lints STRUCTURE (frontmatter, length, references, voice). To judge whether the skill actually works better than no skill, use gate-skill-efficacy instead.

## References

- Anthropic, "Skill authoring best practices": frontmatter constraints, 500-line body limit, third-person descriptions, one-level references, TOC for long files. https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices
- OpenADLC standard, spec.md 5.2 (pack format): a reference is named by its pack-relative `references/<file>.md`, but the markdown link target is file-relative so it resolves from the citing file; this is why check 6 judges the link target, not a pack-root fallback.
