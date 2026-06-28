<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
Consumed by the `ci-cd-pipeline` skill. Load on demand; do not load independently.

## Caching key patterns

Always add a cache step; it cuts CI time by 50-80% on warm runs.

```yaml
- uses: actions/cache@v4
  with:
    path: ~/.gradle/caches
    key: ${{ runner.os }}-gradle-${{ hashFiles('**/*.gradle*', '**/gradle-wrapper.properties') }}
    restore-keys: ${{ runner.os }}-gradle-
```

Adapt `path` and `key` hash input to the ecosystem:

| Ecosystem | `path` | `key` hash input |
|---|---|---|
| npm | `~/.npm` | `**/package-lock.json` |
| Bundler (Ruby) | `vendor/bundle` | `**/Gemfile.lock` |
| CocoaPods | `~/.cocoapods` | `**/Podfile.lock` |
| Gradle | `~/.gradle/caches` | `**/*.gradle*`, `**/gradle-wrapper.properties` |
| pip | `~/.cache/pip` | `**/requirements*.txt` |

## Secrets hygiene rules

- No secret ever in source. Set via `gh secret set NAME` or the GitHub UI.
- Prod credentials go in the `production` environment's secret store, not at repo level.
- Prefer OIDC token federation over static keys for GCP/AWS/Azure.
- Pin third-party actions to a commit SHA, not a floating tag.

## PaaS deploy options

Preferred order for solo scale:

| PaaS | Deploy mechanism | When to use |
|---|---|---|
| Railway | `railway up` CLI or auto-deploy on push | Default for Node/Python services; has managed Postgres |
| Render | Webhook deploy hook (one `curl`) | If already using Render; no CLI install needed |
| Fly.io | `flyctl deploy` | Need multi-region or container control |
| Cloud Run | `google-github-actions/deploy-cloudrun` | GCP ecosystem, pay-per-request scale-to-zero |

Do not introduce Docker Compose, Helm, or Terraform unless the operator explicitly asks.

## Unity CI lane snippet

Use `game-ci/unity-builder@v4` for Unity builds:

```yaml
- uses: game-ci/unity-builder@v4
  with:
    targetPlatform: Android   # or iOS, StandaloneLinux64, etc.
  env:
    UNITY_LICENSE: ${{ secrets.UNITY_LICENSE }}
    UNITY_EMAIL: ${{ secrets.UNITY_EMAIL }}
    UNITY_PASSWORD: ${{ secrets.UNITY_PASSWORD }}

- uses: actions/upload-artifact@v4
  with:
    name: build-artifact
    path: build/
```

Download the artifact in the deploy job with `actions/download-artifact@v4` to avoid a rebuild.
