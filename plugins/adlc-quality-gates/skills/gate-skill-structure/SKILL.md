---
name: gate-skill-structure
description: "This skill should be used when the user asks to \"lint a skill\", \"check a SKILL.md\", \"validate skill structure\", \"review my skill against Anthropic guidelines\", \"gate a skill before merge\", or otherwise wants a SKILL.md file checked for correct frontmatter, body length, progressive-disclosure, and one-level references. Runs a structural quality gate over a single SKILL.md and reports PASS/FAIL with line-anchored fixes."
version: 0.1.0
---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# Gate: SKILL.md structure

Lint one `SKILL.md` against Anthropic's skill-authoring rules. Output a deterministic PASS/FAIL report with exact fixes. This gate checks STRUCTURE only, not whether the skill is useful.

## Inputs

Resolve the target file path:
- Use the path the user named.
- Else find candidates: `find . -name SKILL.md -not -path '*/node_modules/*'`. If more than one, list them and ask which to gate. Never guess.

This gate is read-only. It reports; it does not edit unless the user explicitly asks for the fixes to be applied afterward.

## Checks (run all: in order)

The mechanical checks below are scripted in `tools/lint-skill.sh`: run it first on the resolved file, then layer on the judgment-call checks this skill adds (description quality, voice, right-altitude).

Run each check against the resolved file. Each emits PASS or FAIL with the offending line number(s).

### 1. Frontmatter present and parseable
- File starts with `---` on line 1, a YAML block, and a closing `---`.
- FAIL if missing, malformed, or not the first thing in the file.

### 2. `name` field
- Present and non-empty.
- Max 64 characters.
- Lowercase letters, numbers, hyphens only: regex `^[a-z0-9-]+$`.
- No reserved words: must not contain `anthropic` or `claude`.
- SHOULD equal the parent directory name (warn, not fail, if it differs).

### 3. `description` field
- Present and non-empty; max 1024 characters; no XML tags (`<...>`).
- Written in THIRD PERSON. FAIL if it contains first/second-person openers: `I can`, `I help`, `You can`, `Use this to` at the start. PASS form: "This skill should be used when…" / "Lints…".
- States BOTH what it does AND when to use it (look for trigger phrases / "when"). Warn if no "when"/trigger phrasing is present.

### 4. Body length
- Count lines AFTER the closing frontmatter `---`.
- FAIL if > 500.
- WARN if > 150 (project bar: keep skills well under 150 lines; push detail into sibling reference files).

### 5. References are one level deep
- Collect every relative Markdown link in `SKILL.md` (e.g. `[x](references/y.md)`, `(forms.md)`).
- For each linked local `.md` file that exists, scan it for further relative `.md` links.
- FAIL if any referenced file links onward to another `.md` (deep nesting). All reference files must link directly from `SKILL.md`.
- Report the chain, e.g. `SKILL.md -> advanced.md -> details.md`.

### 6. Linked files exist
- Every relative path referenced from `SKILL.md` must exist on disk (forward slashes only). FAIL on broken links or backslash paths.

### 7. Long reference files have a table of contents
- For each linked `.md` reference file > 100 lines, WARN if it has no `## Contents` / table-of-contents section near the top.

### 8. Voice and hygiene (body)
- WARN on second-person instruction voice (`you should`, `you can`), prefer imperative.
- WARN on time-sensitive phrasing (`before <month> <year>`, `after <date>`) outside an "Old patterns" / `<details>` block.

### 9. Reference citations resolve at the link target
- A reference citation shows its pack-relative name as DISPLAY text (`[references/<file>.md](target)`), but the LINK TARGET inside `(...)` is what must resolve. Resolve each target against the `SKILL.md` directory and FAIL if it does not point at an existing file.
- Judge the target, never the display text: a shared pack-level reference is cited `[references/<file>.md](../../references/<file>.md)` from a skill (`../references/` from a command or agent); a bare `references/<file>.md` target only resolves for a skill's OWN co-located `references/` subdir. `[references/foo.md](references/foo.md)` FAILs when `foo.md` lives at the pack root, because the target resolves to the skill's absent `references/foo.md`.

## Commands

Use scripted greps for determinism. Substitute the resolved path for `$F`.

```bash
# body line count (lines after the 2nd '---')
awk 'f{n++} /^---$/{c++; if(c==2) f=1} END{print n}' "$F"
# name field
grep -m1 '^name:' "$F"
# relative .md links in SKILL.md
grep -oE '\]\(([^)]+\.md)\)' "$F"
```

## Report format

Emit exactly this structure. No prose preamble.

```
# Skill structure gate: <relative/path/to/SKILL.md>

RESULT: PASS | FAIL  (<n> failed, <m> warnings)

FAIL
- [check 4] Body is 612 lines (limit 500). Move detail to references/<topic>.md. (line 540+)
- [check 5] Deep reference: SKILL.md -> advanced.md -> details.md. Link details.md directly from SKILL.md.

WARN
- [check 4] Body is 180 lines; target is under ~150. Trim or split.
- [check 8] Second-person voice at line 92: "you should run". Use imperative.

PASS
- [check 1] Frontmatter present and parseable.
- [check 2] name "gate-skill-structure" valid, matches directory.
- [check 3] description is third-person and states what + when.
```

Rules for the report:
- `RESULT: FAIL` if ANY check fails; otherwise `PASS` (warnings do not fail the gate).
- Every check (1–9) appears under exactly one of FAIL / WARN / PASS.
- Each FAIL/WARN line names the check number, the problem, a one-line fix, and a line number where applicable.

## After the report

State the single most impactful fix. If, and only if, the user then asks to apply fixes, edit the file and re-run all checks (validator -> fix -> re-run loop) until `RESULT: PASS`. This gate performs no network or outbound action.

## References

- Anthropic, "Skill authoring best practices", https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices (frontmatter constraints, 500-line body limit, third-person descriptions, one-level references, TOC-for-long-files).
