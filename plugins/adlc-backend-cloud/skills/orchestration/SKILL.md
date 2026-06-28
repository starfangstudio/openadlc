---
name: orchestration
description: "This skill should be used when deploying a containerized service to Kubernetes or a managed orchestrator, \"write a Deployment\", \"add a Service / Ingress\", \"set resource requests and limits\", \"add liveness / readiness / startup probes\", \"autoscale this with an HPA\", \"wire up ConfigMaps and Secrets\", \"do a zero-downtime rolling update\", \"add a PodDisruptionBudget\", \"validate my k8s manifests\", or reviewing an orchestration change before it ships. Detect-first across vanilla Kubernetes and managed orchestrators (EKS / GKE / AKS, ECS, Cloud Run, Fly, Render): write minimal, probe-backed, resource-bounded workloads that roll out safely. Pairs with `containers` (the image), `iac` (the cluster), `progressive-delivery` (canary / blue-green). Routes observability to `adlc-ops`, security hardening to `adlc-security`, data stores to `adlc-database`."
version: 0.1.0
---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# Orchestration

Run a container as a managed workload: declared desired state, health-gated, resource-bounded, and safe to roll forward and back. Keep the manifest set small. Reach for a primitive only when a concrete need names it, never to fill out a CNCF bingo card.

## Step 1: Detect the orchestrator first
Never impose Kubernetes. Look before you write:
- A managed PaaS already in the repo (`Procfile`, `fly.toml`, `render.yaml`, `app.yaml`, ECS task defs, Cloud Run / `service.yaml`)? Use it; its built-in rollout and health checks usually cover Steps 4 to 8 already. Do not bolt Kubernetes on top.
- Existing `k8s/`, `manifests/`, `*.yaml` with `kind:`, Helm charts, or Kustomize overlays? Match their layout, naming, namespace, and labels. Extend, do not reinvent.
- Nothing yet, and a real team-scale need? Then write plain Kubernetes manifests as below. Plain YAML beats a Helm chart until you have more than one environment to parametrize (then see `iac` and `progressive-delivery`).

Confirm the target API version against the live cluster (`kubectl version`); the API versions below are the current stable ones, but a managed cluster may lag.

## Step 2: Deployment, the unit of work
One Deployment per stateless service. Pin a real image tag (never `:latest`), set `replicas` (at least 2 so a node drain keeps you up), and label consistently so Services and PDBs can select.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api
  labels: { app: api }
spec:
  replicas: 3
  selector:
    matchLabels: { app: api }
  template:
    metadata:
      labels: { app: api }
    spec:
      containers:
        - name: api
          image: registry.example.com/api:1.4.2   # immutable tag or digest, never :latest
          ports:
            - containerPort: 8080
```

Stateful workloads (databases, brokers) belong in a StatefulSet and usually behind a managed service instead; route data-store choices to `adlc-database`.

## Step 3: Resource requests and limits, every container
No requests means the scheduler is guessing and you get noisy-neighbour failures. Set both:
- **requests:** what the scheduler reserves. Size from observed steady-state usage.
- **limits:** the ceiling. For **memory, set request == limit** (Guaranteed memory: no overcommit, predictable OOM, and the pod is evicted last under node pressure). Be cautious with CPU limits: a low CPU limit throttles latency, so request-only CPU with a memory limit is usually the saner default.

```yaml
          resources:
            requests: { cpu: "100m", memory: "256Mi" }
            limits:   { memory: "256Mi" }   # memory request == limit (Guaranteed); CPU request-only to avoid throttling
```

## Step 4: Probes, all three, each with one job
Separate, lightweight endpoints. Do not point a liveness probe at a check that calls your database (a slow dependency then restarts healthy pods and cascades).

- **startupProbe:** guards slow boot (JVM, migrations, cache warm). Until it passes, liveness and readiness are suspended, so a slow start cannot trigger a restart loop. Budget = `periodSeconds * failureThreshold`.
- **readinessProbe:** "can I take traffic right now". Failing it pulls the pod out of the Service, no restart. Check critical dependencies here, not in liveness.
- **livenessProbe:** "am I wedged, restart me". Cheapest possible, no dependencies. Only fail it on truly unrecoverable state.

```yaml
          startupProbe:
            httpGet: { path: /healthz, port: 8080 }
            periodSeconds: 5
            failureThreshold: 30          # up to 150s to boot, then it is considered dead
          readinessProbe:
            httpGet: { path: /readyz, port: 8080 }
            periodSeconds: 10
          livenessProbe:
            httpGet: { path: /healthz, port: 8080 }
            periodSeconds: 10
            failureThreshold: 3
```

## Step 5: Service, then Ingress
A Service gives the Deployment a stable in-cluster address; an Ingress (or Gateway API) exposes HTTP from outside. Keep the Service `ClusterIP` and let the Ingress own external exposure and TLS.

```yaml
apiVersion: v1
kind: Service
metadata: { name: api }
spec:
  selector: { app: api }       # matches the Deployment pod labels
  ports:
    - port: 80
      targetPort: 8080
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata: { name: api }
spec:
  rules:
    - host: api.example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service: { name: api, port: { number: 80 } }
```

TLS, cert issuance, WAF, and network policy are security surface: route them to `adlc-security`.

## Step 6: Config and Secrets, out of the image
Config that changes per environment goes in a ConfigMap; credentials go in a Secret. Inject by reference, never bake into the image or commit a plaintext Secret.

```yaml
          envFrom:
            - configMapRef: { name: api-config }
            - secretRef:    { name: api-secrets }
```

A raw Kubernetes `Secret` is base64, not encrypted at rest by default. For anything real, source from an external manager (SealedSecrets, External Secrets Operator, cloud secret store) and turn on encryption-at-rest; that wiring is `adlc-security` plus `iac`. Never commit a populated Secret to git.

## Step 7: Rolling update, zero downtime
`RollingUpdate` is the default; make it strict so a bad version never takes the whole fleet down. `maxUnavailable: 0` keeps full capacity during the roll; `maxSurge` adds temporary headroom. Readiness (Step 4) is what gates each new pod into rotation, so a broken image stalls the rollout instead of serving errors.

```yaml
  strategy:
    type: RollingUpdate
    rollingUpdate: { maxUnavailable: 0, maxSurge: 1 }
```

Canary, blue-green, flagged rollout, and automated rollback live in `progressive-delivery`.

## Step 8: HPA and PodDisruptionBudget
- **HorizontalPodAutoscaler** (`autoscaling/v2`) scales replicas on a metric. Requires the resource `requests` from Step 3 to compute utilization. Set `minReplicas` to your real floor.
- **PodDisruptionBudget** (`policy/v1`) protects availability during *voluntary* disruption (node drain, upgrade). Set `minAvailable` below HPA `minReplicas` or the cluster cannot drain a node.

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata: { name: api }
spec:
  scaleTargetRef: { apiVersion: apps/v1, kind: Deployment, name: api }
  minReplicas: 3
  maxReplicas: 10
  metrics:
    - type: Resource
      resource: { name: cpu, target: { type: Utilization, averageUtilization: 70 } }
---
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata: { name: api }
spec:
  minAvailable: 2            # strictly below HPA minReplicas so drains can proceed
  selector:
    matchLabels: { app: api }
```

Do not set a static `replicas` on the Deployment and an HPA on the same workload; the HPA owns the count. Leave `replicas` unset (or let your GitOps tool ignore it) once an HPA is attached.

## Step 9: Verify (failable check)
Two gates, both must pass:

1. **Static validation.** Lint every manifest against the cluster's API schemas:
   ```sh
   kubeconform -strict -summary -kubernetes-version 1.30.0 k8s/*.yaml
   ```
   Then a server-side dry run, which also runs admission webhooks and RBAC, catching what static schemas miss:
   ```sh
   kubectl apply --dry-run=server -f k8s/
   ```
2. **Readiness gate.** Apply for real to a non-prod namespace and require the rollout to converge; this is the check that fails on a bad probe, image, or config:
   ```sh
   kubectl apply -f k8s/
   kubectl rollout status deployment/api --timeout=120s   # non-zero exit if pods never go Ready
   ```

A manifest set that validates but whose rollout never reaches Ready is not done. Roll back with `kubectl rollout undo deployment/api`.

## References
- This pack: `containers` (the image probes assume), `iac` (the cluster and secret backends), `progressive-delivery` (canary / blue-green / rollback), `distributed-data`, `messaging`.
- Route out: monitoring, dashboards, alerts, CI/CD authoring -> `adlc-ops`. TLS, network policy, secret encryption, RBAC hardening -> `adlc-security`. Schemas, migrations, query depth -> `adlc-database`.
- Upstream: Kubernetes probe configuration <https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/>, HPA walkthrough <https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale-walkthrough/>, deprecated API migration <https://kubernetes.io/docs/reference/using-api/deprecation-guide/>, kubeconform <https://github.com/yannh/kubeconform>.
