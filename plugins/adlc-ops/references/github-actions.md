<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
# GitHub Actions: starter workflows, secrets, and environments

Reference for the `ci-cd-pipeline` skill. Paste, adapt, and commit locally; deploying or enabling auto-merge-to-prod is outbound: get the operator's explicit yes first.

---

## Starter workflow skeleton

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main]
  pull_request:

permissions:
  contents: read        # least-privilege default; widen per job as needed

jobs:
  build-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      # --- dependency cache (adapt key to your ecosystem) ---
      - name: Cache Gradle / npm / pip
        uses: actions/cache@v4
        with:
          path: |
            ~/.gradle/caches
            ~/.gradle/wrapper
          key: ${{ runner.os }}-gradle-${{ hashFiles('**/*.gradle*', '**/gradle-wrapper.properties') }}
          restore-keys: ${{ runner.os }}-gradle-

      - name: Build + test
        run: ./gradlew :app:assembleDebug :app:testDebugUnitTest

      # upload build artifact so deploy job can retrieve it
      - uses: actions/upload-artifact@v4
        with:
          name: debug-apk
          path: app/build/outputs/apk/debug/
```

---

## Staging + production environment with protection rules

```yaml
# .github/workflows/deploy.yml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  deploy-staging:
    runs-on: ubuntu-latest
    environment: staging             # maps to repo Settings > Environments > staging
    steps:
      - uses: actions/checkout@v4
      - uses: actions/download-artifact@v4
        with:
          name: debug-apk
      - name: Deploy to staging PaaS
        env:
          RAILWAY_TOKEN: ${{ secrets.RAILWAY_TOKEN }}    # environment-scoped secret
        run: railway up --environment staging

  deploy-prod:
    needs: deploy-staging
    runs-on: ubuntu-latest
    environment: production          # requires manual approval via protection rules
    steps:
      - uses: actions/checkout@v4
      - name: Deploy to prod
        env:
          RAILWAY_TOKEN: ${{ secrets.RAILWAY_TOKEN }}
        run: railway up --environment production
```

**Enable protection rules:** Settings > Environments > production > "Required reviewers" (add yourself or a reviewer). The job halts until approved.

---

## Mobile lane (Android + iOS via fastlane)

```yaml
  mobile-build:
    runs-on: macos-latest            # required for iOS signing
    environment: staging
    steps:
      - uses: actions/checkout@v4

      - name: Cache CocoaPods / Gradle
        uses: actions/cache@v4
        with:
          path: |
            ~/.gradle/caches
            Pods/
          key: ${{ runner.os }}-deps-${{ hashFiles('Podfile.lock', '**/*.gradle*') }}

      - name: Run fastlane lane
        env:
          MATCH_PASSWORD: ${{ secrets.MATCH_PASSWORD }}
          APP_STORE_CONNECT_API_KEY_JSON: ${{ secrets.APP_STORE_CONNECT_API_KEY_JSON }}
          GOOGLE_PLAY_JSON_KEY: ${{ secrets.GOOGLE_PLAY_JSON_KEY }}
        # DO NOT duplicate build/sign logic here; delegate entirely to the domain pack lanes
        run: |
          bundle exec fastlane android beta     # android-build-commands / android-store skill
          bundle exec fastlane ios beta         # ios-build-commands / ios-store skill
```

Secrets live in Settings > Secrets and variables > Actions, or scoped to an environment for prod credentials.

---

## Unity build lane (GameCI)

```yaml
  unity-build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          lfs: true
      - uses: game-ci/unity-builder@v4
        env:
          UNITY_LICENSE: ${{ secrets.UNITY_LICENSE }}
          UNITY_EMAIL: ${{ secrets.UNITY_EMAIL }}
          UNITY_PASSWORD: ${{ secrets.UNITY_PASSWORD }}
        with:
          targetPlatform: Android          # or iOS, StandaloneWindows64, WebGL
          buildName: MyGame
      - uses: actions/upload-artifact@v4
        with:
          name: unity-android
          path: build/Android/
```

---

## Backend PaaS deploy snippets

**Railway**
```bash
# Install CLI in CI: npm install -g @railway/cli
railway up --environment $RAILWAY_ENV
```

**Render** (webhook-based deploy hook, no CLI needed)
```yaml
      - name: Trigger Render deploy
        run: |
          curl -X POST "${{ secrets.RENDER_DEPLOY_HOOK_URL }}"
```

**Cloud Run**
```yaml
      - uses: google-github-actions/deploy-cloudrun@v2
        with:
          service: my-service
          image: gcr.io/${{ env.GCP_PROJECT }}/my-service:${{ github.sha }}
          region: europe-west1
```

---

## Secret hygiene rules

- Never commit secrets to source. Use `gh secret set NAME` or the GitHub UI.
- Use environment-scoped secrets for production credentials (Settings > Environments > production > Secrets).
- Prefer OIDC token federation (no static keys) for cloud providers that support it (GCP, AWS, Azure).
- Pin third-party actions to a full commit SHA, not a tag: `uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683`.

---

## References

- GitHub Docs, Environments for deployment: https://docs.github.com/actions/deployment/targeting-different-environments/using-environments-for-deployment
- GitHub Docs, Encrypted secrets: https://docs.github.com/en/actions/concepts/security/secrets
- GitHub Docs, Caching dependencies: https://docs.github.com/en/actions/writing-workflows/choosing-what-your-workflow-does/caching-dependencies-to-speed-up-workflows
- GameCI, Unity Builder action: https://game.ci/docs/github/builder
- fastlane GitHub Actions integration: https://docs.fastlane.tools/best-practices/continuous-integration/github-actions/
- Railway deploy GitHub Actions: https://docs.railway.com/guides/github-actions
- google-github-actions/deploy-cloudrun: https://github.com/google-github-actions/deploy-cloudrun
- GitHub 2026 Actions security roadmap: https://github.blog/news-insights/product-news/whats-coming-to-our-github-actions-2026-security-roadmap/
