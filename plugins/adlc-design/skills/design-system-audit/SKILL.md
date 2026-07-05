---
name: design-system-audit
description: >-
  This skill should be used when the user asks to "audit the design system", "check for
  hardcoded colors or dimensions", "find raw hex values instead of tokens", "verify DS
  component coverage", "look for missing states or previews in components", "find
  accessibility gaps in the component library", "check token usage across platforms",
  "identify duplication candidates for the shared component set", "audit Compose/SwiftUI/React
  for design-system compliance", or "verify the codebase matches the design tokens". Wraps
  the 'design:design-system' human command and adds verify-against-code (greps the real
  source tree), a cross-platform findings report, and an outbound checkpoint. Read-only: emits a
  report only, never edits source.
version: 0.1.0
---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# Design-system audit

Read-only audit of a codebase against its design system. Greps the real source tree for
hardcoded values, raw platform widgets, missing component states, and accessibility gaps.
Emits a structured findings report.

## Step 1: Detect first

Never assume token format, DS library, or naming convention. Inspect before reporting.

```bash
# Token pipeline: DTCG JSON -> Style Dictionary -> platform outputs?
find . -name "*.tokens.json" -o -name "tokens.json" -o -name "*.token.json" | head -10
find . -name "*.xml" -path "*/values/*" | xargs grep -l "color\|dimen" 2>/dev/null | head -5
find . -name "Colors.swift" -o -name "Tokens.swift" -o -name "tokens.ts" | head -5

# DS component library location
find . -type d -name "designsystem" -o -name "design-system" -o -name "ds" | head -5
find . -name "*.kt" | xargs grep -l "@Composable" 2>/dev/null | head -3

# Confirmed token naming scheme (read one output file, do not guess)
cat $(find . -name "colors.xml" -path "*/values/*" | head -1) 2>/dev/null | head -30
```

Record: token pipeline (DTCG / Style Dictionary / manual), platform targets (Compose /
SwiftUI / React), DS library import alias, and token prefix scheme. Mark anything
unresolvable `unknown`. Never invent token names or component names.

## Step 2: Grep for hardcoded literals (Blocking candidates)

Run from the repo root. Collect file + line references.

```bash
# Hardcoded hex colors (all platforms)
grep -rEn '#[0-9a-fA-F]{3,8}' --include="*.kt" --include="*.swift" \
  --include="*.tsx" --include="*.ts" \
  --exclude-dir=".git" --exclude-dir="build" --exclude-dir="node_modules" .

# Android dp/sp literals (Compose)
grep -rEn '\b[0-9]+\.(dp|sp)\b' --include="*.kt" . | grep -v "test\|Test\|Preview"

# Hardcoded font names
grep -rEn '"[A-Z][a-zA-Z]+(Bold|Regular|Medium|Light|Italic)"' \
  --include="*.kt" --include="*.swift" --include="*.tsx" .
```

For SwiftUI CGFloat and React/CSS pixel literals, see
[references/design-system-audit-detail.md](../../references/design-system-audit-detail.md).

Flag every match. Exempt: constants files that ARE the token definitions, test files, and
generated build outputs.

## Step 3: Raw platform widgets where a DS component exists

```bash
# Compose: Text/Button/Icon used directly instead of DS wrappers
grep -rEn '\b(Text|Button|IconButton|Surface|Card)\s*\(' \
  --include="*.kt" . | grep -v "test\|Test\|Preview\|designsystem\|ds/"

# React: HTML primitives instead of DS components
grep -rEn '<(p|button|span|h[1-6]|input)\b' \
  --include="*.tsx" --include="*.jsx" . | grep -v "\.test\.\|\.spec\.\|stories\."
```

For SwiftUI Text/Button greps, see
[references/design-system-audit-detail.md](../../references/design-system-audit-detail.md).

Triage each hit: is a DS equivalent available? If `unknown`, mark it `unknown`, do not
assume a wrapper exists.

## Step 4: Rule-of-three duplication scan

```bash
# Find repeated color values (same literal in 3+ files)
grep -rEhon '#[0-9a-fA-F]{6}' --include="*.kt" --include="*.swift" \
  --include="*.tsx" . | sort | uniq -c | sort -rn | head -20
```

For near-identical modifier-chain detection, see
[references/design-system-audit-detail.md](../../references/design-system-audit-detail.md).

Promotion threshold: flag when the same value, modifier chain, or component shell appears
in 3+ locations. Note 2-occurrence pairs under Suggestions; they are watch items, not yet
blocking.

## Step 5: Missing states, Previews, and accessibility

```bash
# Compose: @Composable without a @Preview sibling in the same file
grep -rln "@Composable" --include="*.kt" . | while read f; do
  grep -q "@Preview" "$f" || echo "NO_PREVIEW: $f"
done

# Missing content descriptions on icons (Compose)
grep -rEn 'Icon\s*\(' --include="*.kt" . \
  | grep -v 'contentDescription\s*=\s*"[^"]\|stringResource'

# React: <img> without alt attribute
grep -rEn '<img\b' --include="*.tsx" --include="*.jsx" . | grep -v 'alt='
```

For SwiftUI `.accessibilityLabel` checks and missing error/empty/loading state greps, see
[references/design-system-audit-detail.md](../../references/design-system-audit-detail.md).

## Step 6: Emit the findings report

Severity tiers:
- **BLOCKING**: hardcoded value or raw widget where the DS alternative is confirmed to exist; missing `contentDescription`/`alt` on a non-decorative element.
- **SUGGEST**: raw widget where DS equivalent is `unknown`; duplication at 2 occurrences; missing Preview.
- **INFO**: duplication at 3+ occurrences where a token already exists; missing error/empty/loading state.

Output this exact table. One row per finding. Never collapse multiple findings into one row.

```
## Design-system audit findings

| # | Severity | Platform | File:Line | Finding | Rule |
|---|----------|----------|-----------|---------|------|
| 1 | BLOCKING | Compose  | ui/Home.kt:42 | Hardcoded `#FF5733`: use token equivalent | Step 2 |
| 2 | SUGGEST  | React    | Button.tsx:18 | Raw `<button>`: DS `<Button>` available | Step 3 |
| 3 | INFO     | All      | 4 files       | `#1A1A2E` 3x: promote to token | Step 4 |
```

After the table, output a one-line verdict:

```
Verdict: N blocking / N suggestions / N info: <one sentence on the most critical gap>.
```

## Outbound checkpoint

Local work needs no approval. Anything outbound (publish, push, post) needs an explicit per-action "yes" from the operator first; see the global consent law.

## References

- Design Tokens Format Module 2025.10 (DTCG stable spec): https://www.designtokens.org/tr/drafts/format/
- Style Dictionary v5 + DTCG integration: https://styledictionary.com/info/dtcg/
- Style Dictionary v5 migration guide: https://styledictionary.com/versions/v5/migration/
- WCAG 2.2 (W3C Recommendation, 2023-10-05): https://www.w3.org/TR/WCAG22/
- WCAG 2.2 mobile guidance (WCAG2Mobile): https://w3c.github.io/matf/
- Audit detail (full grep recipes, SwiftUI/React extensions, modifier-chain scan, full example): [references/design-system-audit-detail.md](../../references/design-system-audit-detail.md)
