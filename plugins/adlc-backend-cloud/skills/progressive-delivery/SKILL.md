---
name: progressive-delivery
description: "This skill should be used when rolling out a backend change safely at scale, \"do a canary release\", \"set up blue-green\", \"ship behind a feature flag\", \"decouple deploy from release\", \"add a health gate to the rollout\", \"auto-rollback on a bad metric\", \"add a kill switch\", \"promote on metrics\", \"Argo Rollouts\", \"Flagger\", or reviewing a rollout strategy for a scaled service. Detect-first across Argo Rollouts, Flagger, and native orchestrator rollouts. Picks a strategy (blue-green vs canary), decouples deploy from release with feature flags, gates promotion on automated health metrics, and guarantees a fast automated rollback. Routes metrics/dashboards to adlc-ops, auth/secrets to adlc-security, schema/migration order to adlc-database."
version: 0.1.0
---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# Progressive delivery

Ship to a fraction first, watch the numbers, and let the machine promote or roll back. A rollout is not "kubectl apply and hope". The deploy (code on a box) and the release (users see it) are two separate switches, and a bad version must reverse itself in seconds without a human awake.

## Step 1: Detect what is already wired

Never impose a controller. Read the repo before writing anything:
- **Argo Rollouts:** look for `kind: Rollout`, `kind: AnalysisTemplate`, or `argoproj.io/v1alpha1` in the manifests; `kubectl argo rollouts` in CI.
- **Flagger:** look for `kind: Canary`, `flagger.app/v1beta1`, or the Flagger controller in the cluster.
- **Native:** plain `kind: Deployment` (RollingUpdate `maxSurge`/`maxUnavailable`), or a managed slot swap (AWS CodeDeploy, Cloud Run revisions + traffic split, Azure deployment slots).
- **Feature flags:** an existing SDK (OpenFeature, LaunchDarkly, Unleash, Flagsmith, GrowthBook) or a homegrown config table. Match it.

If the cluster already runs one controller, use it. Do not add a second. If nothing exists and the service is small, native RollingUpdate plus a feature flag may be all this change needs, say so instead of installing Argo.

## Step 2: Pick a strategy (blue-green vs canary)

Two shapes, pick by blast radius and cost:
- **Blue-green:** stand up the full new version (green) beside the old (blue), smoke-test green on a preview path, then flip 100% of traffic at once. Instant rollback (flip back). Costs double capacity during the window. Use when you cannot tolerate mixed versions (a schema flip, a protocol bump) or you want a clean preview.
- **Canary:** shift a slice of live traffic (5% then 25% then 50% then 100%), watching metrics at each step. Lower capacity cost, real production signal early, contains a bad version to a fraction of users. Use as the default for stateless request/response services.

State the choice and the why in one line. When the change touches a schema, route ordering to `adlc-database` (expand/contract: deploy code that tolerates both shapes before the migration that drops the old shape), then rollout is safe either way.

## Step 3: Decouple deploy from release with a flag

Deploy the binary dark. Wrap the new behavior in a flag so release is a config change, not a redeploy:
- The flag gives you a **kill switch** (flip off in seconds, no rebuild) and a **percentage rollout** (5% then 25% then 100%) independent of where the pods are.
- Prefer the **OpenFeature** vendor-neutral API so the provider is swappable. A minimal, runnable check-and-default pattern:

```python
# Release is a flag read, not a deploy. Default OFF, fail safe.
from openfeature import api
client = api.get_client()

def handle(request):
    if client.get_boolean_value("new-checkout", False, eval_context(request)):
        return new_checkout(request)   # released path
    return legacy_checkout(request)    # safe default
```

Rules: default the flag **off / safe** so a flag-service outage degrades to the known-good path; keep flags short-lived and remove them once the rollout is 100% and stable; never hide a security control behind a flag (route auth/secret gating to `adlc-security`).

## Step 4: Define the automated health gate

Promotion must be earned by metrics, not by a clock or a human eyeballing a graph. Pick a small set of signals that mean "this version is healthy" and bind them to the rollout. The numerator is usually success rate and latency.

**Argo Rollouts** binds an `AnalysisTemplate` to the canary. The controller runs an `AnalysisRun`, queries the provider on an interval, and aborts on `failureLimit`:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: AnalysisTemplate
metadata:
  name: success-rate
spec:
  args:
    - name: service
  metrics:
    - name: success-rate
      interval: 1m            # how often to sample
      count: 5                # number of samples
      successCondition: result[0] >= 0.95   # >=95% non-5xx
      failureLimit: 2         # 2 bad samples => abort + rollback
      provider:
        prometheus:
          address: http://prometheus.monitoring:9090
          query: |
            sum(rate(http_requests_total{service="{{args.service}}",code!~"5.."}[1m]))
            /
            sum(rate(http_requests_total{service="{{args.service}}"}[1m]))
```

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: web
spec:
  strategy:
    canary:
      analysis:
        templates:
          - templateName: success-rate
        args:
          - name: service
            value: web
      steps:
        - setWeight: 5
        - pause: {duration: 2m}
        - setWeight: 25
        - pause: {duration: 5m}
        - setWeight: 50
        - pause: {duration: 5m}
        # implicit setWeight: 100 on success
```

**Flagger** expresses the same idea in a `Canary` resource: `analysis` with `metrics` (built-in `request-success-rate`, `request-duration`, or a custom `MetricTemplate`), `interval`, `threshold` (allowed failed checks before rollback), `stepWeight`, and `maxWeight`. On each interval Flagger checks metrics and webhooks; cross the failed-check threshold and it shifts all traffic back to primary and fails the canary.

The metric source (Prometheus, Datadog, CloudWatch) and the dashboards/alerts around it are **observability**, route their setup to `adlc-ops`. This skill only consumes the metric as a gate.

## Step 5: Guarantee fast automated rollback

Rollback must be automatic and fast, not a 2am pager runbook.
- **Canary auto-abort:** a failed analysis (above) sets the canary weight back to 0 and marks the rollout `Degraded` with no traffic on the bad version. No human in the loop.
- **Blue-green revert:** keep blue running until green is proven; revert is flipping the service selector back to blue.
- **Flag kill switch:** the fastest lever, flip the flag off and the bad path is gone cluster-wide in seconds, even before the pods change.
- **Manual escape hatch:** `kubectl argo rollouts abort <name>` (Argo) reverts to the stable version on demand; document the one command an on-call runs.

Make the floor explicit: a bad version is contained to the canary slice and reversed automatically, and the worst case is a flag flip, never a full redeploy.

## Step 6: Verify

The failable check is a canary that **auto-rolls-back on a failing health metric**, run it in a test cluster (kind/minikube) and assert the abort, do not eyeball it:

1. Apply the `Rollout` + `AnalysisTemplate` (or Flagger `Canary`) above against a test deployment.
2. Trigger an update to an image that fails the metric (e.g. returns 500s so success-rate drops below the `successCondition`).
3. Watch it fail and roll back:

```bash
# Fails (non-zero exit) while the rollout is Degraded after auto-abort.
kubectl argo rollouts status web --timeout 5m
echo "exit=$?"   # expect non-zero: "Degraded - RolloutAborted"

# Assert canary carries zero weight and stable is serving 100%.
kubectl argo rollouts get rollout web -o json \
  | jq -e '.status.canary.weights.canary.weight == 0' >/dev/null \
  && echo "PASS: rolled back to stable" || { echo "FAIL: canary still weighted"; exit 1; }
```

Green-path counterpart: a healthy image must promote to 100% on its own (`status` exits 0, `Healthy`). A rollout that only ever promotes, or only rolls back on a manual command, has no gate and is not done.

## References
- **Argo Rollouts** analysis + auto-rollback: https://argo-rollouts.readthedocs.io/en/stable/features/analysis/ and basic usage https://argo-rollouts.readthedocs.io/en/stable/getting-started/
- **Flagger** deployment strategies + webhooks: https://docs.flagger.app/usage/deployment-strategies and https://docs.flagger.app/usage/webhooks
- **OpenFeature** (CNCF vendor-neutral flags): https://openfeature.dev/
- Strategy split (blue-green vs canary) and schema-change ordering: pair with `adlc-database` (expand/contract migrations).
- In-pack neighbors: `orchestration` (the Deployment/Service/Ingress this rolls), `containers` (the image being shipped).
- Out of lane (route, do not duplicate): metrics/dashboards/alerts -> `adlc-ops`; auth, secrets, flag-gated security controls -> `adlc-security`; schema and migration order -> `adlc-database`.
