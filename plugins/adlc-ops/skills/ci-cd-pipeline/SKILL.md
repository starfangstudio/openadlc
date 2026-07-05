---
name: ci-cd-pipeline
description: >-
  Scaffolds and reviews GitHub Actions pipelines (build, test, quality gate, staging
  deploy, manual prod deploy) for solo-scale projects; delegates mobile lanes to
  Fastlane skills and backend deploys to managed PaaS. Use when asked to "set up
  CI/CD", "add a GitHub Actions pipeline", "automate deploys to staging and prod",
  "wire up Fastlane to CI", or "review the existing pipeline".
version: 0.1.0
---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# CI/CD pipeline

Default to GitHub Actions. Solo-scale means managed services and simple pipelines; steer
away from Kubernetes, Helm, Terraform, and multi-cluster setups until there is a concrete
reason for each.

## Detect first

Inspect the repo before proposing anything:

```bash
# Existing CI config?
find . -maxdepth 3 -path "*/.github/workflows/*.yml" -o -path "*/.github/workflows/*.yaml" | sort
ls .circleci/ .buildkite/ bitrise.yml 2>/dev/null

# Package ecosystem (drives caching strategy)
ls package.json Gemfile build.gradle settings.gradle *.sln Package.swift 2>/dev/null

# Fastlane present?
find . -maxdepth 4 -name "Fastfile" | head -5

# Existing environments / secrets (names only, values never shown)
gh secret list 2>/dev/null || echo "gh CLI not authenticated"
gh api repos/:owner/:repo/environments 2>/dev/null | jq '.[].name' || echo "unknown"
```

Record: which CI exists (if any), which ecosystems are present, whether Fastlane is
configured, and which environments/secrets already exist. Mark anything not found `unknown`;
never invent workflow names or secret names.

## Pipeline stages

```
PR push  ->  [build + test]  ->  [quality gate]  ->  [staging deploy]  ->  [prod deploy]
                                       |
                             adlc-quality-gates:
                             gate-deployment-readiness
                             (invoke that skill; do not duplicate its logic here)
```

Stage rules:
- **build + test**: always runs on every PR. Fail fast.
- **quality gate**: invoke `adlc-quality-gates gate-deployment-readiness` before any deploy.
- **staging deploy**: runs on merge to `main`. Automatic is fine for staging.
- **prod deploy**: runs only after staging succeeds AND a manual approval clears in the
  `production` environment (protection rule). Never auto-deploy to prod.

## Scaffold checklist

- [ ] `.github/workflows/ci.yml` -- build + test, runs on every PR and push to `main`
- [ ] `.github/workflows/deploy.yml` -- staging then prod, triggered on push to `main`
- [ ] GitHub environment `staging` created (Settings > Environments)
- [ ] GitHub environment `production` created with required-reviewer protection rule
- [ ] Secrets scoped to the correct environment (never at repo level for prod credentials)
- [ ] Dependency cache configured (see reference for key patterns)
- [ ] Artifacts uploaded so deploy job can retrieve them without a rebuild
- [ ] Actions pinned to commit SHA or verified version tag (not `@latest`)

See [references/github-actions.md](../../references/github-actions.md) for copy-paste workflow YAML,
secrets hygiene rules, caching key patterns, mobile/Unity lanes, and PaaS deploy snippets.

## Mobile lane

Do NOT duplicate build, signing, or store-upload logic here. Delegate entirely:

```yaml
- name: Run fastlane lanes
  run: |
    bundle exec fastlane android beta   # android-build-commands + android-store skills own this
    bundle exec fastlane ios beta       # ios-build-commands + ios-store skills own this
```

Read the project's `Fastfile` first: `grep "lane :" fastlane/Fastfile`. Pass secrets
(`MATCH_PASSWORD`, `APP_STORE_CONNECT_API_KEY_JSON`, `GOOGLE_PLAY_JSON_KEY`) as
environment-scoped CI secrets, never hardcoded.

For Unity: see the Unity CI lane snippet in [references/ci-cd-pipeline-detail.md](../../references/ci-cd-pipeline-detail.md).

## Backend lane (managed PaaS)

Choose the simplest option that fits the project. Preferred order (Railway default for Node/Python,
Render if already in use, Fly.io for multi-region, Cloud Run for GCP pay-per-request). Do not
introduce Docker Compose, Helm, or Terraform unless the operator explicitly asks.

For the full PaaS comparison table and deploy commands, see [references/ci-cd-pipeline-detail.md](../../references/ci-cd-pipeline-detail.md).

## Caching

Always add a cache step; it cuts CI time by 50-80% on warm runs. For caching key patterns
per ecosystem (npm, Bundler, CocoaPods, Gradle, pip), see [references/ci-cd-pipeline-detail.md](../../references/ci-cd-pipeline-detail.md).

## Secrets hygiene

- No secret ever in source. Set via `gh secret set NAME` or the GitHub UI.
- Prod credentials go in the `production` environment's secret store, not at repo level.
- Prefer OIDC token federation over static keys for GCP/AWS/Azure.
- Pin third-party actions to a commit SHA, not a floating tag.

## Verify

A pipeline is green when:
1. A PR triggers the CI job and it passes (build + test + lint).
2. Merge to `main` triggers the deploy job; staging deploys automatically.
3. The production job pauses for manual approval, then deploys after approval.

Check the Actions tab after each commit during setup; do not assume it works without a run.

## Outbound approval

Local work needs no approval. Outbound here (enabling auto-deploy to production, a workflow that publishes to the App Store or Play Store, a protection rule that sends an approval email, provisioning cost-incurring cloud resources like a Railway project, Cloud Run service, or Fly app, or any step that POSTs/PUTs to an external service): stop and ask the operator for an explicit yes. Present exactly what would go out and wait for the yes before doing it (global consent law).

## References

- [references/ci-cd-pipeline-detail.md](../../references/ci-cd-pipeline-detail.md) -- caching key patterns, PaaS table, Unity CI lane snippet, secrets hygiene detail
- [references/github-actions.md](../../references/github-actions.md) -- starter YAML, secrets/environments
  setup, mobile/Unity lanes, PaaS deploy snippets (created alongside this skill)
- GitHub Docs, Environments for deployment: https://docs.github.com/actions/deployment/targeting-different-environments/using-environments-for-deployment
- GitHub Docs, Encrypted secrets: https://docs.github.com/en/actions/concepts/security/secrets
- GitHub Docs, Caching dependencies: https://docs.github.com/en/actions/writing-workflows/choosing-what-your-workflow-does/caching-dependencies-to-speed-up-workflows
- GameCI, Unity Builder GitHub Action: https://game.ci/docs/github/builder
- fastlane CI integration: https://docs.fastlane.tools/best-practices/continuous-integration/github-actions/
- Railway deploy from GitHub Actions: https://docs.railway.com/guides/github-actions
- GitHub 2026 Actions security roadmap: https://github.blog/news-insights/product-news/whats-coming-to-our-github-actions-2026-security-roadmap/
