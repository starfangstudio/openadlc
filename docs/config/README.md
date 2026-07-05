<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
# Configuration

OpenADLC runs with no config. You pick your model and effort in your harness, per stage, with nothing to maintain. The optional `openadlc.yaml` exists for two things: declaring a poly-repo product, and (on the roadmap) tuning checkpoints, review, style, compression, and packs.

The starting point is [openadlc.example.yaml](../../openadlc.example.yaml). Copy it to `openadlc.yaml` in your project root and keep only the keys you need.

## Where config comes from

Settings resolve in this order, most authoritative first:

```
managed (org)  >  project (openadlc.yaml)  >  user (~/.openadlc/config.yaml)
```

Org policy can only **tighten**: a project cannot loosen a managed setting.

## What is live in v0.1

Only two keys do something today.

### `version`

```yaml
version: 1
```

The config schema version. Set it to `1`.

### `workspace` (poly-repo products)

```yaml
workspace:
  repos: [shared-components, web-app, backend]   # member repo paths under this root
  primary: web-app                               # where the PARENT story posts; the default tracker
```

Declares a **poly-repo product**: several repos that form one product, so a single run can span the member repos it touches. Omit this block for a single repo or a monorepo.

Without it, a parent directory of repos is treated as unrelated repos, not a product, and the commands ask which repo to target (or offer to declare a workspace). The four workspace shapes and the tracker and PR hierarchy are in [concepts: run isolation](../concepts/run-isolation.md).

- `repos`: the member repo paths under this root.
- `primary`: the repo whose tracker the parent story posts to, and the default tracker.

## Declared, not yet enforced in v0.1 (roadmap)

The keys below are part of the config shape but are not enforced yet. They document where tuning will land. The commands already reference some of them as their intended defaults (for example compression on by default), but per this file the block is roadmap in v0.1.

### `checkpoints`

```yaml
checkpoints:
  plan: true             # operator approves the plan before implementation
  review: true           # operator approves the reviewed change before release
```

Toggles for the two tunable checkpoints. The release (consent) checkpoint is not here on purpose: it always applies to anything outbound and is not a setting you turn off. See [concepts: checkpoints](../concepts/checkpoints.md).

### `review`

```yaml
review:
  strictness: standard     # lenient | standard | strict
```

How hard the review lenses push. Default `standard`.

### `style`

```yaml
style:
  verbosity: normal        # terse | normal | verbose
```

How much the human-facing output says. Default `normal`.

### `compression`

```yaml
compression:
  enabled: true            # on by default
  level: lite              # lite (readable) | full | ultra
  provider: native         # native (zero-install baseline) | caveman (full upstream, if installed)
  protect_human_facing: true   # never compress the story / plan / review / consent
```

Cuts AI-internal and inter-agent output tokens. It never compresses what you read (the story, plan, review, and consent prompt). The technique is adapted from Caveman (MIT) and reimplemented natively; the `caveman` provider uses the full upstream if installed. See [THIRD-PARTY.md](../../THIRD-PARTY.md).

### `packs`

```yaml
packs:
  enabled: []              # extra packs to load
  disabled: []             # core pieces to disable by name
```

Load extra packs, or disable core pieces by name. For installing and building packs, see [customize](../customize/).

## Source

- [openadlc.example.yaml](../../openadlc.example.yaml): the annotated example, the source of truth for this page.
