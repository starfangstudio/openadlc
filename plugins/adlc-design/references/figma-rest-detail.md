<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
Consumed by the `figma-extract` skill (REST pull, drift, assets) and `figma-implement`
(asset wiring). Load on demand; do not load independently. The token pipeline (Variables
API) stays in `design-tokens-detail.md`.

## Auth: one token, env only

One credential, one env var name across this pack: `FIGMA_ACCESS_TOKEN`. It is a personal
access token (or OAuth bearer) with the `file_content:read` scope. REST sends it in the
`X-Figma-Token` request header (OAuth bearer tokens use `Authorization: Bearer <token>`
instead; pick one, not both).

```bash
export FIGMA_ACCESS_TOKEN="figd_xxx"   # in your shell, a CI secret, or a chmod-600 secrets file sourced by your shell (e.g. ~/.openadlc/secrets.env); never in a committed or project file
```

The token is a credential: read it from the environment, never hardcode it, never commit
it, never paste it into a doc or log line. A leaked `figd_` token is a full read of every
file the owner can see. Reading via REST is a network read, no approval needed; see the
outbound checkpoint in `figma-extract` for what needs the operator's explicit yes.

## Parse the file key and node-id from a Figma URL

A Figma URL is `https://www.figma.com/<type>/<file_key>/<file_name>?node-id=<node-id>`.

| Part | Where | Notes |
|------|-------|-------|
| `<type>` | path segment 1 | `design` (current) or `file` (older). Both carry the same key. `board`/`slides`/`deck` are FigJam/Slides, not design files. |
| `<file_key>` | path segment 2 | The string passed as `:key` to every endpoint below. |
| `<node-id>` | `node-id` query param | URL form is **hyphenated** (`5-3`). The REST API wants **colons** (`5:3`). Convert before calling. |

The single gotcha: the URL writes node ids with a hyphen, the API reads them with a
colon. `node-id=1-42` in the browser is `ids=1:42` in the request. Skip the conversion and
you get an empty `nodes` map, not an error.

```bash
# Extract both from a pasted URL (one chosen, runnable form).
URL='https://www.figma.com/design/ABC123def456/Checkout?node-id=5-3'
FILE_KEY=$(printf '%s' "$URL" | sed -E 's#.*/(design|file)/([^/]+)/.*#\2#')
NODE_ID=$(printf '%s' "$URL" | sed -E 's/.*node-id=([0-9]+)-([0-9]+).*/\1:\2/')
echo "$FILE_KEY $NODE_ID"   # ABC123def456 5:3
```

## Endpoint 1: GET file nodes (the structured tree)

`GET https://api.figma.com/v1/files/:key/nodes?ids=<colon-ids>`

| Param | Type | Use |
|-------|------|-----|
| `ids` | string, required | Comma-separated colon node ids, e.g. `5:3,5:4`. |
| `depth` | int, optional | How deep to traverse. `depth=1` = direct children only. Omit = whole subtree. Use a shallow depth first on a big frame so context does not blow up, then re-fetch the nodes you need. |
| `geometry` | string, optional | `geometry=paths` returns vector path data (needed only when you reason about raw geometry). |
| `version` | string, optional | A specific version id; omit for current. |
| `plugin_data` | string, optional | Comma-separated plugin ids or `shared`. |

Response: `{ name, lastModified, version, nodes: { "5:3": { document, components, styles } } }`.
The `document` is the node tree (each node has `absoluteBoundingBox` for geometry, plus
`layoutMode`/`layoutGrow`/`layoutSizingHorizontal` for auto-layout intent, `boundVariables`
for bound token names, and `componentId`/`componentSetId` for component refs). This is the
structured pull the drift check diffs.

```bash
curl -s "https://api.figma.com/v1/files/$FILE_KEY/nodes?ids=$NODE_ID&depth=2" \
  -H "X-Figma-Token: $FIGMA_ACCESS_TOKEN" \
  -o design-baseline/checkout@2026-06-27.nodes.json
```

Errors: `400` invalid param (often an un-converted hyphen id), `403` bad/expired token or
missing scope, `404` file not found. Tier-1 rate limit; back off on `429`.

## Endpoint 2: GET images (the rendered baseline + assets)

`GET https://api.figma.com/v1/images/:key?ids=<colon-ids>&format=<fmt>&scale=<n>`

| Param | Type | Use |
|-------|------|-----|
| `ids` | string, required | Comma-separated colon node ids. |
| `format` | string | `png`, `jpg`, `svg`, or `pdf`. PNG for the fidelity baseline; SVG for vector icons. |
| `scale` | number | `0.01`–`4`. The raster scaling factor (`2` = @2x). Ignored for `svg`. |
| `svg_outline_text` | bool, default `true` | `false` keeps real `<text>` so the SVG stays editable. |
| `svg_simplify_stroke` | bool, default `true` | Collapses strokes; leave on for smaller output. |
| `use_absolute_bounds` | bool, default `false` | `true` exports the node's full bounds (use for text nodes so they are not cropped). |
| `contents_only` | bool, default `true` | `false` includes overlapping content from outside the node. |
| `version` | string, optional | Render a specific version. |

Response is **not** the image: `{ "err": null, "images": { "5:3": "https://figma-alpha-api.s3..." } }`.
The values are short-lived S3 URLs (assets **expire after 30 days**); fetch them in a
second request. Max 32 megapixels per render; larger is scaled down. Same `400/403/404`
plus `500` on a render failure.

```bash
# Two-step: ask for the render URL, then download it.
PNG_URL=$(curl -s "https://api.figma.com/v1/images/$FILE_KEY?ids=$NODE_ID&format=png&scale=2" \
  -H "X-Figma-Token: $FIGMA_ACCESS_TOKEN" \
  | python3 -c 'import sys,json;print(json.load(sys.stdin)["images"]["5:3"])')
curl -s "$PNG_URL" -o design-baseline/checkout@2026-06-27@2x.png

# SVG render of the same node (scale ignored; keep text editable).
SVG_URL=$(curl -s "https://api.figma.com/v1/images/$FILE_KEY?ids=$NODE_ID&format=svg&svg_outline_text=false" \
  -H "X-Figma-Token: $FIGMA_ACCESS_TOKEN" \
  | python3 -c 'import sys,json;print(json.load(sys.stdin)["images"]["5:3"])')
curl -s "$SVG_URL" -o assets/icons/checkout.raw.svg
```

## Drift: diff the structured pull, not the PNG

Drift is detected on **metadata fields**, never on the rendered image. A pixel diff trips
on anti-aliasing and font hinting and tells you nothing about *what* changed; the node
JSON tells you the exact field. Store a small baseline beside the image at extract time and
diff the fresh `nodes` pull against it field-by-field.

Baseline metadata to store (one record per node id):

```json
{
  "nodeId": "5:3",
  "date": "2026-06-27",
  "geometry": { "w": 360, "h": 56, "x": 0, "y": 624 },
  "boundTokens": { "fill": "color/surface/raised", "cornerRadius": "radius/md" },
  "components": ["PrimaryButton@a1b2c3", "Icon/cart@d4e5f6"],
  "layout": { "mode": "HORIZONTAL", "sizingH": "FILL", "sizingV": "HUG" }
}
```

What trips a drift flag (any one is drift, stop and run `iterate-plan`):

| Field compared | Source in `nodes` JSON | Flag when |
|----------------|------------------------|-----------|
| Bound token name | `boundVariables.*` (variable id -> name) | Any token **rename or rebind** (a fill that was `color/surface/raised` now points elsewhere, or a literal where a token was). Tokens are the design-system contract; a rebind is always drift, even if the rendered color is identical. |
| Geometry | `absoluteBoundingBox` (`x,y,width,height`) | Change **beyond the `ui-fidelity` tolerance** (default 1px / 2%). Sub-tolerance jitter is noise, not drift. |
| Component ref | `componentId` / `componentSetId` | A referenced component is **removed or replaced** with a different one (id changed), or an instance became a detached frame. |
| Layout intent | `layoutMode`, `layoutSizingHorizontal/Vertical` | Resizing intent flips (Fill -> Fixed, Hug -> Fill); this changes responsive behavior even when one frame looks the same. |

Token rename/rebind and a removed/replaced component are **always** drift regardless of
magnitude. Geometry is the only field with a tolerance, and it reuses the `ui-fidelity`
number so "drift" and "fidelity FAIL" never disagree. Diff is field-by-field against the
stored record; report each drifted field as `field: baseline -> live` so the planner sees
exactly what moved.

## Assets: vectors as SVG, bitmaps per density

Export every **non-component vector node** (icons, logos, illustrations not already a DS
component) via the Images endpoint. Components go through Code Connect / reuse, not asset
export, so you do not fork a DS icon into a loose file. Save into the project's asset dir,
not `design-baseline/` (that is the fidelity baseline, not shipped assets).

**Vectors -> optimized SVG.** Render `format=svg` (above), then optimize with SVGO before
committing. Raw Figma SVG carries editor cruft (ids, metadata, redundant groups).

```bash
npx svgo assets/icons/checkout.raw.svg -o assets/icons/checkout.svg
# preset-default is applied automatically; add svgo.config.mjs only for per-repo overrides.
```

**Bitmaps -> platform densities.** Only raster what cannot be a vector (photographic /
gradient-baked art). Render the baseline (1x) node and request each density via `scale`,
mapping to the platform's convention:

| Platform | Buckets and `scale` values | Output convention |
|----------|----------------------------|-------------------|
| iOS | `@1x`=1, `@2x`=2, `@3x`=3 (@3x = Plus/Max + modern premium iPhones) | `Foo.imageset/` in `Assets.xcassets`: `foo@1x.png`, `foo@2x.png`, `foo@3x.png` with a `Contents.json` mapping scale -> file. Design unit is the **point**: 1pt = 1px @1x, 2px @2x, 3px @3x. |
| Android | mdpi=1 (160dpi baseline), hdpi=1.5, xhdpi=2, xxhdpi=3, xxxhdpi=4 | `res/drawable-<bucket>/foo.png`, one file per `drawable-mdpi … drawable-xxxhdpi` folder. Design unit is the **dp**: 1dp = 1px at mdpi. (Prefer a vector drawable when the art allows; raster only when it does not.) |
| Web | render @1x and @2x (add 3x for icon-dense UI) | `foo.png`, `foo@2x.png`; reference with `srcset` x-descriptors. |

Figma `scale` caps at 4, which is exactly Android xxxhdpi, so every bucket is reachable in
one request set. iOS @1x/@2x/@3x and Android mdpi/xhdpi/xxhdpi share the same scale numbers
(1/2/3), so a single render set covers both when sizes match.

```bash
# Android: render every bucket from one node id, named for the drawable folder.
for pair in mdpi:1 hdpi:1.5 xhdpi:2 xxhdpi:3 xxxhdpi:4; do
  bucket=${pair%%:*}; s=${pair##*:}
  url=$(curl -s "https://api.figma.com/v1/images/$FILE_KEY?ids=$NODE_ID&format=png&scale=$s" \
    -H "X-Figma-Token: $FIGMA_ACCESS_TOKEN" \
    | python3 -c 'import sys,json;print(json.load(sys.stdin)["images"]["5:3"])')
  mkdir -p "app/src/main/res/drawable-$bucket"
  curl -s "$url" -o "app/src/main/res/drawable-$bucket/hero.png"
done
```

Web `srcset` (x-descriptors for fixed-size raster; the `src` URL is the implicit `1x`):

```html
<img src="hero.png" srcset="hero@2x.png 2x, hero@3x.png 3x" alt="Checkout hero" />
```

## Sources

- Figma file & image endpoints: https://developers.figma.com/docs/rest-api/file-endpoints/
- Android pixel densities: https://developer.android.com/training/multiscreen/screendensities
- iOS image scales: https://developer.apple.com/design/human-interface-guidelines/images
- `srcset`: https://developer.mozilla.org/en-US/docs/Web/API/HTMLImageElement/srcset
- SVGO: https://github.com/svg/svgo
