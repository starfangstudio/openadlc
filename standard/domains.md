<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# The ADLC Domain Taxonomy

> Status: version 1.0 (closed vocabulary v1). For spec version 1.0.
> One line: the canonical domain vocabulary and the deterministic, file-marker-only procedure that resolves which domains a repo belongs to, so every command and pack activates the right guidance from the same names.

This is the single source of truth for domain strings. The core detector and every enterprise pack MUST cite these names exactly, character for character: a pack that means "web" writes `web`, never `frontend` or `Web`. Renaming or adding a domain here is a spec change, not a pack-local choice.

**The packs are the domains.** Each technical domain below maps 1:1 to a `plugins/adlc-<name>` pack, and its authoritative one-line trigger is the pack's `description` in [`.claude-plugin/marketplace.json`](../.claude-plugin/marketplace.json) at the repo root. This file adds the one thing the marketplace manifest does not carry: the deterministic file-marker condition that activates each pack from repo facts, without asking. `adlc-core` is the always-on spine (the four `/ai-*` commands + the lifecycle checkpoints); it is never activated or deactivated by this sniff, it always loads.

## 1. The vocabulary is closed (v1)

Eleven **technical domains** (repo-facts-detected, section 2), six **cross-cutting lenses** (never repo-detected, section 3), plus the always-on `adlc-core` spine (not a domain, loads unconditionally). A repo MAY match more than one technical domain: a monorepo that holds a React app and a Postgres schema is both `web` and `database`, and both activate. Do not invent a domain outside this list; propose an addition to this file instead (spec.md Law L6: ask, don't improvise).

## 2. Technical domains (repo-facts-detected)

Each domain is resolved from one or more deterministic file markers. A domain matches when at least one of its marker conditions is true.

| Domain | Pack | Marker (any one matches) |
|---|---|---|
| `web` | `adlc-web` | `package.json` containing a web framework dependency: `react`, `vue`, `svelte`, `next`, `nuxt`, `angular`, `vite`, `remix`, `astro` |
| `backend` | `adlc-backend` | a server-framework signal: `package.json` with `express`/`fastify`/`nest`/`koa`/`hapi`; OR `pyproject.toml`/`requirements.txt` with `fastapi`/`django`/`flask`; OR `go.mod` with `gin`/`echo`/`fiber`; OR `pom.xml`/`build.gradle`/`build.gradle.kts` with `spring`; OR an `openapi.yaml`, `openapi.json`, or `*.openapi.*` file |
| `backend-cloud` | `adlc-backend-cloud` | containers / Kubernetes / infrastructure-as-code signals: a `Dockerfile`; OR a `*.tf`/`*.tfvars` file; OR k8s manifests (a `k8s/` directory or `kustomization.yaml`); OR a Helm `Chart.yaml` |
| `android` | `adlc-android` | `build.gradle` or `build.gradle.kts` referencing `kotlin` or `android`; OR an `AndroidManifest.xml` |
| `ios` | `adlc-ios` | `Package.swift`; OR a `*.xcodeproj`; OR a `*.xcworkspace` |
| `desktop` | `adlc-desktop` | Tauri: `src-tauri/tauri.conf.json`; OR Electron: `electron` dependency in `package.json` |
| `database` | `adlc-database` | a `migrations/` directory; OR a `*.sql` file; OR `schema.prisma`; OR `alembic.ini` |
| `ai` | `adlc-ai` | an ML dependency (`torch`, `tensorflow`, `transformers`, `langchain`, `openai`, `anthropic`) in a manifest; OR an `evals/` directory of prompts |
| `unity` | `adlc-unity` | a `ProjectSettings/` directory, plus either a `*.unity` scene file or an `Assets/` directory (the `ProjectSettings/` dir is required; a bare `Assets/` alone does NOT match — many non-Unity repos name a folder `Assets`) |
| `ops` | `adlc-ops` | CI/CD or managed-deploy config: `.github/workflows/*.yml`/`*.yaml`; OR `.gitlab-ci.yml`; OR a managed-deploy manifest (`Procfile`, `fly.toml`, `render.yaml`, `vercel.json`, `netlify.toml`) |
| `monetization` | `adlc-monetization` | a store-billing SDK reference in a build/dependency manifest: Google Play Billing (`com.android.billingclient`) in `build.gradle`/`build.gradle.kts`; OR StoreKit/RevenueCat (`StoreKit`, `RevenueCat`, `purchases-ios`) in `Package.swift`/`Podfile`; OR a cross-platform IAP library (`react-native-iap`, `cordova-plugin-purchase`, `expo-in-app-purchases`) in `package.json` |

`backend-cloud` and `ops` intentionally do not overlap: containers/K8s/IaC markers (Docker, Terraform, k8s manifests, Helm) belong to `backend-cloud`; CI/CD pipeline and managed-deploy configs belong to `ops`. There is no standalone `infra` domain: what a first draft of this taxonomy called `infra` folds into these two, matching how the packs actually split the concern (`adlc-backend-cloud` routes observability to `adlc-ops`; `adlc-ops` routes the deploy gate to `adlc-quality-gates`).

## 3. Cross-cutting lenses (not repo-detected)

Never resolved from a marker file. Always eligible regardless of which technical domains matched; driven by org policy, the ask itself, a design surface, or the rail-1 mandatory floor (a later slice), never by what the repo-facts sniff finds.

| Lens | Pack | Driven by |
|---|---|---|
| `security` | `adlc-security` | org policy / the rail-1 mandatory floor |
| `privacy` | `adlc-privacy` | org policy / the rail-1 mandatory floor |
| `design` | `adlc-design` | the ask touching Figma or a design surface |
| `testing` | `adlc-testing` | the ask (test strategy, scenario expansion) |
| `planning` | `adlc-planning` | the ask (deeper planning, contracts, impact analysis) |
| `quality-gates` | `adlc-quality-gates` | org policy / release readiness |

## 4. The repo-facts detector (stage 1)

The detector is a **deterministic static file-marker sniff**, run over the repo the command executes in. It is a declarative procedure any command follows by reading the table in section 2, not a runtime script and not a daemon: no network call, no model judgment. (Judging which domains an *ask* actually needs, beyond what the repo contains, is stage-2 ask-scoping and is out of scope for this file; see the note at the end of this section.)

**Procedure:**
1. For each technical domain in section 2, check its marker conditions against the repo's files (read-only, no execution of any manifest's scripts).
2. A domain is in the **matched set** if any one of its marker conditions is true. This is not exclusive: a repo can match zero, one, or many domains.
3. The matched set is the stage-1 output: an unordered set of domain strings. Order MUST NOT be treated as significant (same repo -> same set, order-independent).
4. Zero matches means an empty repo or an unrecognized stack; the calling command falls back to asking the operator (per `spec.md` Law L6), it does not guess.

**Determinism:** the same repo state MUST always sniff to the same domain set. The sniff MUST NOT vary by run, by model, or by phrasing of the ask.

**What this stage does not do:** it does not decide which of the matched domains the current ask actually needs (a repo tagged both `web` and `database` may have a story that only touches one), and it does not apply the cross-cutting lenses or the mandatory floor. Narrowing the matched set to what an ask needs, and layering in the cross-cutting lenses (section 3), is stage-2 ask-scoping, specified in a later slice.

## 5. Caching and audit: `activation.md`

The matched domain set is written to the run record, so it is computed once per run and available to every later command without a re-sniff, and so the run has an audit trail of what was detected and why.

**Location:** `~/.openadlc/runs/<workspace>/<run-id>/activation.md` (the out-of-repo run workspace; never under the repo's `.claude/`, per [run-isolation.md](../plugins/adlc-core/references/run-isolation.md)).

**The section this slice owns** (stage 1 only; the full schema, policy candidate-set, activated set, reasons, and floor are a later slice and MAY extend this file):

```markdown
## Repo facts (stage 1, deterministic)
- repo: <path or workspace-relative name>
- detected: <UTC ISO 8601>
- matched domains: [web, database]
- markers:
  - web: package.json (react)
  - database: schema.prisma
```

**Refresh:** a command reads this section on later steps of the same run rather than re-sniffing; it refreshes the section when a marker file listed above has changed since `detected`. This file is shared by later slices (the policy candidate-set, the activated set, and the floor each add their own section); this slice defines only the section above.

## References

- The 18 shipped packs and their authoritative one-line descriptions: [`.claude-plugin/marketplace.json`](../.claude-plugin/marketplace.json) at the repo root (17 domain/cross-cutting packs + the always-on `adlc-core` spine).
- Run isolation, the run workspace, and the run-artifact list: [run-isolation.md](../plugins/adlc-core/references/run-isolation.md).
- The lifecycle's ask-don't-improvise law (zero matches, ambiguity): [spec.md](spec.md) Law L6.
