<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
Consumed by the `design-system-audit` skill. Load on demand; do not load independently.

---

## Step 2: Grep for hardcoded literals (Blocking candidates)

Run each grep from the repo root. Collect file + line references.

```bash
# Hardcoded hex colors
grep -rEn '#[0-9a-fA-F]{3,8}' --include="*.kt" --include="*.swift" --include="*.tsx" \
  --include="*.ts" --include="*.jsx" --include="*.js" \
  --exclude-dir=".git" --exclude-dir="build" --exclude-dir="node_modules" .

# Android dp/sp literals (Compose)
grep -rEn '\b[0-9]+\.(dp|sp)\b' --include="*.kt" . | grep -v "test\|Test\|Preview"

# SwiftUI raw CGFloat dimensions (not from tokens/constants)
grep -rEn '\.(frame|padding|font)\(.*[0-9]{2,}' --include="*.swift" . \
  | grep -v "Preview\|_Preview\|#Preview"

# React/CSS: raw pixel or rem literals not from a token variable
grep -rEn ':\s*[0-9]+(px|rem|em)' --include="*.tsx" --include="*.ts" \
  --include="*.css" --include="*.scss" . | grep -v "node_modules\|\.test\."

# Hardcoded font names (strings, not token references)
grep -rEn '"[A-Z][a-zA-Z]+(Bold|Regular|Medium|Light|Italic)"' \
  --include="*.kt" --include="*.swift" --include="*.tsx" .
```

Flag every match. Exempt: constants files that ARE the token definitions, test files, and
generated build outputs.

---

## Step 3: Raw platform widgets where a DS component exists

```bash
# Compose: Text/Button/Icon used directly instead of DS wrappers
grep -rEn '\b(Text|Button|IconButton|Surface|Card)\s*\(' \
  --include="*.kt" . | grep -v "test\|Test\|Preview\|designsystem\|ds/"

# SwiftUI: Text/Button without DS modifier or DS type alias
grep -rEn '\b(Text|Button|Label)\s*\(' \
  --include="*.swift" . | grep -v "Preview\|_Preview\|DesignSystem\|DS"

# React: HTML primitives (<p>, <button>, <span>) instead of DS components
grep -rEn '<(p|button|span|h[1-6]|input)\b' \
  --include="*.tsx" --include="*.jsx" . | grep -v "\.test\.\|\.spec\.\|stories\."
```

Triage each hit: is a DS equivalent available? If `unknown`, mark it `unknown`, do not
assume a wrapper exists.

---

## Step 4: Rule-of-three duplication scan

```bash
# Find repeated color/dimension values (identical literal in 3+ files)
grep -rEhon '#[0-9a-fA-F]{6}' --include="*.kt" --include="*.swift" \
  --include="*.tsx" . | sort | uniq -c | sort -rn | head -20

# Near-identical composable/view patterns (same modifier chain 3+ occurrences)
grep -rEn 'Modifier\.(fillMaxWidth|padding|background|clip)' --include="*.kt" . \
  | sort | uniq -c | sort -rn | head -15
```

Promotion threshold: flag when the same knowledge (value, modifier chain, or component
shell) appears in 3+ locations. Note 2-occurrence pairs under Suggestions; they are watch
items, not yet blocking.

---

## Step 5: Missing states, Previews, and accessibility

```bash
# Compose: @Composable without a @Preview sibling in the same file
grep -rln "@Composable" --include="*.kt" . | while read f; do
  grep -q "@Preview" "$f" || echo "NO_PREVIEW: $f"
done

# Missing content descriptions on icons (Compose)
grep -rEn 'Icon\s*\(' --include="*.kt" . \
  | grep -v 'contentDescription\s*=\s*"[^"]\|stringResource'

# SwiftUI: Image without .accessibilityLabel / .accessibilityHidden
grep -rEn 'Image\s*(' --include="*.swift" . \
  | grep -v "accessibilityLabel\|accessibilityHidden"

# React: <img> without alt, interactive element without aria-label
grep -rEn '<img\b' --include="*.tsx" --include="*.jsx" . | grep -v 'alt='
grep -rEn '<(button|a)\b' --include="*.tsx" --include="*.jsx" . \
  | grep -v 'aria-label\|aria-labelledby\|children'

# Components with no error/empty/loading state handling
grep -rln "LazyColumn\|LazyRow\|FlatList\|List" \
  --include="*.kt" --include="*.swift" --include="*.tsx" . \
  | while read f; do
    grep -q "Empty\|empty\|Error\|error\|Loading\|loading" "$f" \
      || echo "MISSING_STATES: $f"
  done
```

---

## Step 6: Severity tier definitions and report example

Severity tiers:
- **BLOCKING**: hardcoded value or raw widget where the DS alternative is confirmed to
  exist; missing `contentDescription`/`alt` on a non-decorative element.
- **SUGGEST**: duplication at 2 occurrences (watch item); raw widget where DS equivalent
  status is `unknown`; missing Preview.
- **INFO**: duplication at 3+ occurrences where a token already exists; missing
  error/empty/loading state.

Example findings table (one row per finding, never collapse):

```
## Design-system audit findings

| # | Severity | Platform | File:Line | Finding | Rule |
|---|----------|----------|-----------|---------|------|
| 1 | BLOCKING | Compose  | ui/Home.kt:42 | Hardcoded `#FF5733`: use `MaterialTheme.colorScheme.primary` or token equivalent | Step 2 |
| 2 | SUGGEST  | React    | Button.tsx:18 | Raw `<button>`: DS `<Button>` component available | Step 3 |
| 3 | INFO     | All      | 4 files       | `#1A1A2E` appears 3x: promote to token `color.background.brand` | Step 4 |
```
