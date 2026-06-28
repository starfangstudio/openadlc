---
name: containers
description: >-
  This skill should be used when the user asks to "write a Dockerfile", "containerize
  this service", "build a production image", "make a multi-stage Dockerfile", "slim down
  my Docker image", "run the container as non-root", "add a HEALTHCHECK", "fix the layer
  cache", "add a .dockerignore", "pin the base image", "stop leaking secrets into image
  layers", "set up docker-compose for local dev", or "scan my image for CVEs". Builds a
  production-grade container image for a detected language/runtime: multi-stage build,
  slim base pinned by digest, non-root user, a real HEALTHCHECK, layer-cache-friendly
  ordering, a tight .dockerignore, and no secrets baked into layers. Adds a docker-compose
  for local parity. Detect-first. Routes observability to adlc-ops, security hardening to
  adlc-security, and data modeling/migrations to adlc-database.
version: 0.1.0
---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# containers

Build a production container image that is small, reproducible, and runs as an unprivileged
user with a working healthcheck. Detect the language and runtime first, then write the
minimum Dockerfile that does the job. No kitchen-sink base images, no `latest`, no secrets
in layers.

**Boundaries (own little, route the rest):**
- **Observability** (metrics, logs shipping, tracing, dashboards, CI/CD pipeline authoring):
  route to `adlc-ops`. This skill only emits to stdout/stderr and exposes a healthcheck.
- **Security hardening** (image-signing policy, SBOM attestation, runtime seccomp/AppArmor,
  secrets-manager wiring, threat model): route to `adlc-security`. This skill applies the
  baseline (non-root, no secrets in layers, pinned digest, CVE gate) and stops there.
- **Data modeling / migrations / query depth**: route to `adlc-database`. A container that
  runs migrations on boot calls into that work, it does not redefine it.
- **Kubernetes / orchestration probes and resource limits**: route to the `orchestration`
  skill in this same pack. Here we define the image and its `HEALTHCHECK`; the orchestrator
  defines liveness/readiness probes against the same endpoint.

## Step 1: Detect the language and runtime first -- never impose

Before writing a Dockerfile, inspect what the project actually is:

```bash
# Language / build tool
ls package.json pnpm-lock.yaml yarn.lock 2>/dev/null        # Node
ls go.mod go.sum 2>/dev/null                                # Go
ls pyproject.toml poetry.lock requirements.txt 2>/dev/null  # Python
ls build.gradle.kts pom.xml 2>/dev/null                     # JVM (Kotlin/Java)
ls Cargo.toml 2>/dev/null                                   # Rust

# Existing container setup -- match it, do not overwrite blindly
ls Dockerfile* .dockerignore docker-compose*.yml compose.yml 2>/dev/null

# Runtime version the code already targets
grep -E '"node"|"engines"' package.json 2>/dev/null
grep -E '^go ' go.mod 2>/dev/null
grep -E 'python_requires|requires-python' pyproject.toml setup.cfg 2>/dev/null

# The start command / entrypoint the app expects
grep -E '"start"|"main"' package.json 2>/dev/null
```

Record the runtime and its pinned version. Mark anything not found as `unknown` and ask
before guessing. Never change an existing base image, package manager, or build tool
without an explicit operator request.

## Step 2: Multi-stage build -- builder heavy, runtime tiny

Compilers, dev headers, and the full dependency tree belong in a **builder** stage. The
final stage copies only the built artifact plus runtime dependencies. This is the single
biggest lever on image size and attack surface.

Go (compiles to a static binary, so the runtime stage can be near-empty):

```dockerfile
# syntax=docker/dockerfile:1
FROM golang:1.24-bookworm@sha256:<pinned-digest> AS build
WORKDIR /src
# Dependency layer first (Step 4): cached unless go.mod/go.sum change
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 go build -trimpath -ldflags="-s -w" -o /out/app ./cmd/server

FROM gcr.io/distroless/static-debian12:nonroot@sha256:<pinned-digest>
COPY --from=build /out/app /app
USER nonroot
EXPOSE 8080
ENTRYPOINT ["/app"]
```

Node (install prod deps in a clean layer, copy the build output, drop dev tooling):

```dockerfile
# syntax=docker/dockerfile:1
FROM node:22-bookworm-slim@sha256:<pinned-digest> AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --omit=dev

FROM node:22-bookworm-slim@sha256:<pinned-digest> AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM gcr.io/distroless/nodejs22-debian12:nonroot@sha256:<pinned-digest>
WORKDIR /app
COPY --from=deps  /app/node_modules ./node_modules
COPY --from=build /app/dist ./dist
EXPOSE 8080
CMD ["dist/server.js"]
```

Use the **exec form** (JSON array) for `ENTRYPOINT`/`CMD` so the process gets PID 1 and
receives signals directly. Never the shell form.

## Step 3: Slim base, pinned by digest, non-root user

- **Slim base.** Prefer `distroless` (no shell, no package manager) or `-slim` Debian over
  full distros. Alpine is fine for Go/static binaries; be cautious with it for Python and
  glibc-linked native deps (musl breaks some wheels).
- **Pin by digest, not tag.** `FROM image:tag@sha256:<digest>`. A tag like `22-slim` floats;
  a digest is reproducible. Get it once with `docker buildx imagetools inspect <image>:<tag>`
  and commit it. Pin every stage.
- **Run as non-root.** Distroless `:nonroot` variants set this for you. On a `-slim` base,
  create a user and switch to it before the entrypoint:

```dockerfile
RUN groupadd --system --gid 10001 app \
 && useradd  --system --uid 10001 --gid app app
USER 10001:10001
```

  Use a numeric `USER` so the orchestrator's `runAsNonRoot` check can verify it. The process
  must not need root at runtime: bind to a port > 1024 (e.g. 8080), write only to a volume
  or `/tmp`, never `chown` the whole tree at runtime.

## Step 4: Layer-cache-friendly ordering + .dockerignore

Order instructions cheapest-to-change first so a code edit does not bust the dependency
layer. The rule: **copy lockfiles and install dependencies before copying source.**

```dockerfile
COPY package.json package-lock.json ./   # changes rarely -> layer stays cached
RUN  npm ci --omit=dev                    # the expensive step, cached with it
COPY . .                                  # changes every commit -> only this rebuilds
```

Add a `.dockerignore` so the build context (and the image) stays small and secret-free:

```dockerignore
.git
node_modules
dist
build
target
.env
.env.*
*.log
.DS_Store
Dockerfile*
docker-compose*.yml
**/*_test.go
coverage/
```

A tight `.dockerignore` also stops a stray `.env` or `.git` from being copied by a broad
`COPY . .`.

## Step 5: A real HEALTHCHECK

The healthcheck must hit the app's actual readiness path, not just confirm the process is
up. Distroless images have no shell, no `curl`, no `wget`, so the probe must be a single
executable in exec form. Two patterns:

```dockerfile
# Base has a shell + curl (e.g. -slim with curl installed):
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD curl -fsS http://127.0.0.1:8080/healthz || exit 1
```

```dockerfile
# Distroless / no shell: ship a tiny static healthcheck binary and exec it directly.
COPY --from=build /out/healthcheck /healthcheck
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD ["/healthcheck", "--addr=127.0.0.1:8080", "--path=/healthz"]
```

Node distroless can self-probe with its own runtime: `CMD ["node", "healthcheck.js"]`.
Tune `--start-period` to cover real boot time (migrations, warm-up) so a slow start is not
flagged unhealthy. The orchestrator's probes target this same `/healthz`; keep them aligned
(see the `orchestration` skill).

## Step 6: No secrets in any layer

A secret `COPY`d in and `rm`d in a later layer is still in the image history. Never bake
secrets into layers.

- **Build-time secrets:** use BuildKit mounts, which never land in a layer:
  `RUN --mount=type=secret,id=npmrc npm ci`. Pass with `--secret id=npmrc,src=...`.
- **Runtime secrets:** inject as environment variables or mounted files at `docker run` /
  orchestrator deploy time, never via `ENV` or `ARG` in the Dockerfile.
- **Never** `COPY .env` (the `.dockerignore` above blocks it) and never put a token in an
  `ARG` default. Secrets-manager wiring and rotation policy are `adlc-security`'s lane.

Verify nothing leaked: `docker history --no-trunc <image>` should show no secret material,
and `docker run --rm <image> env` should show no baked credentials.

## Step 7: docker-compose for local parity

Give developers a one-command local stack that mirrors production wiring (same image, same
env contract), with only the conveniences dev needs (a bind mount, a local DB):

```yaml
services:
  app:
    build: .
    ports: ["8080:8080"]
    env_file: [.env.local]          # gitignored; never committed
    depends_on:
      db:
        condition: service_healthy
  db:
    image: postgres:17-bookworm@sha256:<pinned-digest>
    environment:
      POSTGRES_PASSWORD: localdev    # local only, never a real secret
    volumes: ["pgdata:/var/lib/postgresql/data"]
    healthcheck:
      test: ["CMD", "pg_isready", "-U", "postgres"]
      interval: 5s
      retries: 5
volumes:
  pgdata:
```

Keep the app image identical to production (build from the same Dockerfile); only compose-
level conveniences differ. Database schema and seed data are `adlc-database`'s lane.

## Outbound checkpoint

Local work (writing the Dockerfile, building, running, scanning locally) is unrestricted.
**Pushing an image to a registry, or deploying it, is outbound** and needs the operator's
explicit "yes" first: present the tag, digest, and target registry, then wait. See the global
consent law.

## Verify -- the failable check

The image is not done until all four pass locally:

```bash
# 1. It builds.
docker build -t app:verify .

# 2. It runs as a non-root user (must NOT print uid=0 / "root").
docker run --rm app:verify id        # distroless: inspect config instead
docker inspect app:verify --format '{{.Config.User}}'   # must be non-empty, non-root

# 3. The healthcheck reports healthy within the start period.
cid=$(docker run -d -p 8080:8080 app:verify)
until [ "$(docker inspect -f '{{.State.Health.Status}}' "$cid")" = healthy ]; do
  sleep 2
  [ "$(docker inspect -f '{{.State.Health.Status}}' "$cid")" = unhealthy ] && exit 1
done
docker rm -f "$cid"

# 4. A scan finds NO critical CVE in the final image (exit non-zero fails the build).
trivy image --severity CRITICAL --ignore-unfixed --exit-code 1 app:verify
#   or:  docker scout cves --only-severity critical --exit-code app:verify
```

If any step fails, the image ships nothing. A green build with a root user, a missing
healthcheck, or a critical CVE is a failed check, not a passing one.

## References

- Docker build best practices (multi-stage, cache, non-root, exec form):
  https://docs.docker.com/build/building/best-practices/
- Dockerfile `HEALTHCHECK` reference (intervals, start-period, exec form):
  https://docs.docker.com/reference/dockerfile/#healthcheck
- Pin base images by digest (reproducible builds):
  https://docs.docker.com/build/building/best-practices/#pin-base-image-versions
- BuildKit build secrets (`--mount=type=secret`, no layer leak):
  https://docs.docker.com/build/building/secrets/
- Distroless base images (slim, non-root `:nonroot` tags, no shell):
  https://github.com/GoogleContainerTools/distroless
- Healthchecks for distroless containers (ship a probe binary):
  https://medium.com/@aminmir326/health-checks-for-distroless-containers-a2180c4c4fcf
- Trivy image scanning + CI exit-code gate:
  https://trivy.dev/docs/latest/guide/target/container_image/
- Docker Scout CVEs (`docker scout cves`, severity + exit code):
  https://docs.docker.com/scout/
- `.dockerignore` reference:
  https://docs.docker.com/reference/dockerfile/#dockerignore-file
- In-pack: `orchestration` (probes, resource limits), `progressive-delivery` (rollout).
  Cross-pack: `adlc-ops` (observability, CI/CD), `adlc-security` (signing, SBOM, secrets
  manager), `adlc-database` (schema, migrations, seed).
