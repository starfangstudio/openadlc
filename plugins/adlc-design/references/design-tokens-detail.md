<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
Consumed by the `design-tokens` skill. Load on demand; do not load independently.

## Token directory layout (multi-brand)

```
tokens/
  globals/          # component-structure tokens; alias into brand refs
    color.json      # semantic: { "background": { "$value": "{brand.bg}" } }
    spacing.json
    typography.json
    motion.json
  brands/
    <app-a>/        # brand overrides: color, type, spacing, radius, shadow, motion
      color.json
    <app-b>/
      color.json
    <app-c>/
      color.json
```

Global tokens alias into brand tokens (`"{brand.primary}"`); brand files set the raw
values. Never put layout, grid, or z-index into brand files -- those are structural and
shared.

## Style Dictionary v5 full config (multi-brand, multi-platform)

Install: `npm install style-dictionary@^5` (or `bun add style-dictionary@^5`).

```js
// style-dictionary.config.mjs
import StyleDictionary from 'style-dictionary';

const BRANDS = ['<app-a>', '<app-b>', '<app-c>'];   // replace with actual brand names

for (const brand of BRANDS) {
  const sd = new StyleDictionary({
    usesDtcg: true,
    source: [
      'tokens/globals/**/*.json',
      `tokens/brands/${brand}/**/*.json`,
    ],
    platforms: {
      web: {
        transformGroup: 'css',
        buildPath: `build/web/${brand}/`,
        files: [{ destination: 'tokens.css', format: 'css/variables',
                   options: { outputReferences: true } }],
      },
      ios: {
        transformGroup: 'ios-swift',
        buildPath: `build/ios/${brand}/`,
        files: [{ destination: 'DesignTokens.swift', format: 'ios-swift/class.swift' }],
      },
      android: {
        transforms: ['attribute/cti', 'name/snake', 'color/hex8android'],
        buildPath: `build/android/${brand}/src/main/res/values/`,
        files: [
          { destination: 'colors.xml', format: 'android/colors', filter: { $type: 'color' } },
          { destination: 'dimens.xml', format: 'android/dimens', filter: { $type: 'dimension' } },
        ],
      },
      'android-compose': {
        transforms: ['attribute/cti', 'name/camel', 'color/composeColor',
                     'size/compose/remToDp'],
        buildPath: `build/android/${brand}/src/main/kotlin/theme/`,
        files: [{ destination: 'Tokens.kt', format: 'compose/object' }],
      },
    },
  });
  await sd.buildAllPlatforms();
}
```

If the project already has an SD config, extend it rather than replacing it. Merge
`usesDtcg: true` and add missing brand entries; preserve existing transforms.

## Tailwind integration (web only, optional)

```js
// tailwind.config.js
const tokens = require('./build/web/<app-a>/tokens.json');
module.exports = { theme: { extend: { colors: tokens.color } } };
```

## Verify script (pass/fail)

```bash
# Build all platforms for all brands
node style-dictionary.config.mjs

# Confirm output files exist for every brand x platform
ls build/web/*/tokens.css build/ios/*/DesignTokens.swift \
   build/android/*/values/colors.xml build/android/*/kotlin/theme/Tokens.kt

# Prove no hardcoded hex/color values remain in source (adjust paths)
grep -rEn '#[0-9a-fA-F]{3,8}|Color\(0x' \
  app/src/main/kotlin app/src/main/swift src/ \
  --include="*.kt" --include="*.swift" --include="*.tsx" | grep -v build/ | grep -v test

# Zero matches = clean. Any match = a value that should be a token reference.
```

## Figma REST API variables (Enterprise only)

```
GET /v1/files/:file_key/variables/local   (scope: file_variables:read)
GET /v1/files/:file_key/variables/published
```

Map `variableCollections` + `variables` from the response to DTCG groups/tokens.
Write a thin normalization script; do NOT call the Dev Mode MCP. Requires an Enterprise
Figma org. If access is unavailable, fall back to Priority 2 (DTCG JSON).

Do not write to the Figma REST API (POST /variables) without operator consent; that is
an outbound action that needs the operator's explicit yes first.
