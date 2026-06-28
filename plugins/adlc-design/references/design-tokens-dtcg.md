<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
# Design tokens reference: DTCG 2025.10 + Style Dictionary v5 multi-brand/multi-platform

This file is a load-on-demand reference cited by the `design-tokens` skill. It contains
format details and config templates; do not restate everything here in the skill body.

---

## DTCG 2025.10 format

The Design Tokens Community Group published the first stable release on 2025-10-28.
Canonical URL: https://www.designtokens.org/tr/2025.10/

### Core field conventions

Each token is a JSON object with:

| Field | Required | Purpose |
|---|---|---|
| `$value` | yes | The token's value (string, number, or composite object) |
| `$type` | recommended | Declares the semantic type (see table below) |
| `$description` | no | Human-readable note shown in tooling |
| `$extensions` | no | Vendor-specific metadata |
| `$deprecated` | no | Boolean or string explaining the deprecation |

### Defined token types

| `$type` | `$value` shape |
|---|---|
| `color` | CSS-compatible color string, e.g. `"#FF5733"`, `"oklch(60% 0.2 30)"` |
| `dimension` | String with `px` or `rem` unit, e.g. `"16px"`, `"1.5rem"` |
| `fontFamily` | String or array of strings (font-stack) |
| `fontWeight` | Number (100-900) or keyword |
| `duration` | String with `ms` or `s` unit, e.g. `"200ms"` |
| `cubicBezier` | Array of four numbers: `[x1, y1, x2, y2]` |
| `number` | Unitless number |
| `typography` | Composite: `{ fontFamily, fontSize, fontWeight, letterSpacing, lineHeight }` |
| `shadow` | Composite: `{ color, offsetX, offsetY, blur, spread }` or array thereof |
| `border` | Composite: `{ color, width, style }` |
| `transition` | Composite: `{ duration, delay, timingFunction }` |
| `gradient` | Array of `{ color, position }` stop objects |

### Groups and aliases

- Groups are plain JSON objects that contain tokens or other groups. Groups may carry a
  `$type` that is inherited by member tokens that do not declare their own.
- Aliases reference another token's `$value` with the curly-brace syntax:
  `"{group.token}"`. The resolver follows references transitively.
- JSON Pointer syntax (`"#/path/to/token/$value"`) references a sub-property.

### Minimal DTCG example

```json
{
  "brand": {
    "$type": "color",
    "primary": { "$value": "#1A56DB", "$description": "Primary brand color" },
    "on-primary": { "$value": "#FFFFFF" }
  },
  "spacing": {
    "$type": "dimension",
    "sm": { "$value": "8px" },
    "md": { "$value": "16px" },
    "lg": { "$value": "24px" }
  },
  "type": {
    "body": {
      "$type": "typography",
      "$value": {
        "fontFamily": "Inter, sans-serif",
        "fontSize": "16px",
        "fontWeight": 400,
        "lineHeight": "1.5"
      }
    }
  },
  "motion": {
    "easing-standard": {
      "$type": "cubicBezier",
      "$value": [0.4, 0, 0.2, 1]
    },
    "duration-medium": {
      "$type": "duration",
      "$value": "200ms"
    }
  }
}
```

---

## Style Dictionary v5 multi-brand/multi-platform config

Style Dictionary v5 uses native ESM (`style-dictionary.config.mjs`).
Docs: https://styledictionary.com/reference/config/
DTCG support in SD v5: https://styledictionary.com/info/dtcg/

### Token directory layout (multi-brand)

```
tokens/
  globals/         # component-structure tokens; aliases to semantic refs
    color.json
    spacing.json
    typography.json
    motion.json
  brands/
    app-a/         # brand overrides for App A
      color.json
      typography.json
    app-b/
      color.json
      typography.json
    app-c/
      color.json
      typography.json
  platforms/
    web/           # platform-specific aliases (if needed)
    ios/
    android/
```

Rule: component-structure tokens (layout, grid, elevation hierarchy) live in `globals/`
and do NOT change per brand. Brand files override ONLY color, type, spacing, radius,
shadow, and motion.

### Build script (`build.mjs`)

```js
import StyleDictionary from 'style-dictionary';

const BRANDS = ['app-a', 'app-b', 'app-c'];

for (const brand of BRANDS) {
  const sd = new StyleDictionary({
    // SD v5: use 'log.verbosity' and 'preprocessors' at top level
    usesDtcg: true,           // parse $value/$type instead of value/type
    source: [
      `tokens/globals/**/*.json`,
      `tokens/brands/${brand}/**/*.json`,
    ],
    platforms: {
      web: {
        transformGroup: 'css',
        buildPath: `build/web/${brand}/`,
        files: [{
          destination: 'tokens.css',
          format: 'css/variables',
          options: { outputReferences: true },
        }],
      },
      ios: {
        transformGroup: 'ios-swift',
        buildPath: `build/ios/${brand}/`,
        files: [{
          destination: 'DesignTokens.swift',
          format: 'ios-swift/class.swift',
          className: `${brand.replace('-', '')}Tokens`,
          filter: (token) => !token.filePath.includes('motion'),
        }],
      },
      android: {
        transforms: ['attribute/cti', 'name/snake', 'color/hex8android'],
        buildPath: `build/android/${brand}/src/main/res/values/`,
        files: [
          { destination: 'colors.xml',  format: 'android/colors',  filter: { $type: 'color' } },
          { destination: 'dimens.xml',  format: 'android/dimens',  filter: { $type: 'dimension' } },
        ],
      },
      'android-compose': {
        transforms: ['attribute/cti', 'name/camel', 'color/composeColor', 'size/compose/remToSp', 'size/compose/remToDp'],
        buildPath: `build/android/${brand}/src/main/kotlin/theme/`,
        files: [{
          destination: 'Tokens.kt',
          format: 'compose/object',
          className: `${brand.replace('-', '')}Tokens`,
        }],
      },
    },
  });

  await sd.buildAllPlatforms();
}
```

### Platform transform cheat-sheet

| Platform | Key transforms | Format |
|---|---|---|
| Web (CSS) | `transformGroup: 'css'` | `css/variables` |
| iOS (SwiftUI) | `transformGroup: 'ios-swift'` | `ios-swift/class.swift` or `enum.swift` |
| Android (XML resources) | `name/snake`, `color/hex8android` | `android/colors`, `android/dimens` |
| Android (Compose) | `name/camel`, `color/composeColor`, `size/compose/remToDp` | `compose/object` |

### Transform groups

`transformGroup: 'css'` bundles: `attribute/cti`, `name/kebab`, `color/css`, `size/rem`.
`transformGroup: 'ios-swift'` bundles: `attribute/cti`, `name/camelCase`, `color/UIColorSwift`, `content/swift/literal`, `asset/swift/literal`, `size/swift/remToCGFloat`, `font/swift/literal`.

Custom transforms are registered via `sd.registerTransform(...)` before `buildAllPlatforms()`.

---

## Figma REST API: token/variable endpoints

Use these endpoints to pull raw design data when Claude Design `/design-sync` is not yet
configured. Requires an Enterprise Figma org; scope: `file_variables:read`.

| Endpoint | Returns |
|---|---|
| `GET /v1/files/:file_key/variables/local` | All local variables + collections in the file |
| `GET /v1/files/:file_key/variables/published` | Published/library variables only |
| `GET /v1/files/:file_key/styles` | Legacy styles (color, text, effect, grid) |

Docs: https://developers.figma.com/docs/rest-api/variables-endpoints/

The response structure (`variableCollections`, `variables`) maps to DTCG groups/tokens;
write a thin normalization script to emit DTCG JSON before feeding Style Dictionary.

---

## References

- DTCG 2025.10 specification: https://www.designtokens.org/tr/2025.10/
- DTCG format module (draft): https://www.designtokens.org/tr/drafts/format/
- Style Dictionary v5 config reference: https://styledictionary.com/reference/config/
- Style Dictionary DTCG support: https://styledictionary.com/info/dtcg/
- Style Dictionary predefined formats: https://styledictionary.com/reference/hooks/formats/predefined/
- SD multi-brand-multi-platform example: https://github.com/amzn/style-dictionary/tree/master/examples/advanced/multi-brand-multi-platform
- Figma REST API variables endpoints: https://developers.figma.com/docs/rest-api/variables-endpoints/
