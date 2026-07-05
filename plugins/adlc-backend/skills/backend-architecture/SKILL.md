---
name: backend-architecture
description: >-
  This skill should be used when the user asks to "shape the backend", "set up the backend
  structure", "add a new backend module", "split the backend into modules", "design the
  module boundaries", "set up accounts/leaderboards/payments/liveops/catalog", "pick a
  backend stack", "structure the Ktor project", "add a bounded context", "should I use
  microservices", "when to split a service", "set up the data layer", "add an outbox",
  "structure the transport layer", "lay out the backend for a solo dev", or "avoid over-
  engineering the backend". Shapes a solo-dev backend as a modular monolith: one deployable,
  bounded domain modules with clean seams, a strict layering contract, and a concrete
  when-to-split checklist so the architecture can evolve without being prematurely distributed.
version: 0.1.0
---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# backend-architecture

Shape a solo-dev backend as a **modular monolith by default**: one deployable, domain-bounded
modules, strict layering. Never jump to microservices without a measured reason.

## Step 1: Detect first -- never impose

Inspect the repo before changing anything:

```bash
# Language + framework signals
find . -name "build.gradle.kts" -o -name "go.mod" -o -name "package.json" \
       -o -name "supabase/config.toml" | head -20

# Existing module / package layout
ls -1 src/ 2>/dev/null || ls -1 modules/ 2>/dev/null || echo "unknown"

# DB in use
grep -rE "postgresql|mysql|sqlite|supabase" . \
  --include="*.kts" --include="*.yaml" --include="*.toml" -l | head -10

# Any existing service/repo boundaries
grep -rn "interface.*Service\|interface.*Repository" . \
  --include="*.kt" --include="*.go" --include="*.ts" | head -20
```

Record: language/framework, DB, existing module/package names, any services already split.
Mark anything unclear `unknown`. Ask before restructuring.

## Step 2: Confirm the default -- modular monolith, one deploy

State this explicitly if the operator hasn't: the default is ONE deployable. Do NOT propose
microservices, K8s, or an event bus unless the operator has a concrete, measured reason
listed in [references/modular-monolith.md](../../references/modular-monolith.md) (when-to-split checklist).

Anti-over-engineering gates (stop and ask before crossing):
- Proposing more than one deployable (service mesh, sidecar, separate services)
- Adding a message broker (Kafka, RabbitMQ, NATS) when an outbox table suffices
- Suggesting CQRS/event-sourcing without a stated read/write scaling problem
- Recommending K8s when a single VM + managed DB handles the load

## Step 3: Lay out the domain modules

For the standard module list (accounts, catalog, leaderboards, payments, liveops, simulation),
see [references/backend-architecture-detail.md](../../references/backend-architecture-detail.md) (Standard domain modules).

Add only the modules the product actually needs. Start with `accounts`; add others on demand.

Each module follows a three-layer layout. Full schema and visibility rules are in
[references/modular-monolith.md](../../references/modular-monolith.md) (Module seams section).

Key constraints:
- Only each module's `api` sub-package may be imported by other modules.
- Modules never share DB tables or cross-query each other's data layer.
- In-process calls are plain function calls; do NOT add a broker to decouple same-process modules.

## Step 4: Apply the layering contract

Enforce four layers: transport -> service -> data -> infra. Dependencies flow strictly
downward; transport never calls data directly.
For the full ASCII diagram, see [references/backend-architecture-detail.md](../../references/backend-architecture-detail.md)
(Layering contract).

For cross-module side effects that must survive a crash, use an outbox table (write to outbox
in the same transaction, poll + deliver via a background worker). Add an outbox only when
you have a real consistency requirement -- not by default.

## Step 5: Choose the stack (if greenfield)

Detect first (Step 1). If nothing exists, use the stack selection guide (decision tree
plus Ktor module structure) in [references/modular-monolith.md](../../references/modular-monolith.md).
Do not mix stacks in the same monolith without an explicit operator decision.

## Step 6: Cross-cutting deferrals

Do not handle these inside this skill. For the full deferral table (ops, security, privacy,
monetization, sim), see [references/backend-architecture-detail.md](../../references/backend-architecture-detail.md)
(Cross-cutting deferrals).

## Step 7: Verify (pass/fail)

```bash
# Compile clean
./gradlew build --configuration-cache   # Ktor/Gradle
go build ./...                          # Go
npm run build                           # Node

# No cross-module data-layer imports
grep -rn "import.*\.data\." src/ --include="*.kt" | grep -v "^src/<owning-module>"
# Expect zero results outside the owning module

# DB migrations apply cleanly
./gradlew flywayMigrate   # or: supabase db push
```

Do not mark done without a clean compile and passing migration.

## Outbound checkpoint

Local work needs no approval. Anything outbound (publish, push, post) needs the operator's explicit per-action "yes"; stop, present exactly what would go out, and wait for it before anything leaves the machine.

## References

- [references/backend-architecture-detail.md](../../references/backend-architecture-detail.md) -- module list, layering
  diagram, cross-cutting deferrals (load on demand).
- [references/modular-monolith.md](../../references/modular-monolith.md) -- module seams, visibility rules,
  when-to-split checklist, outbox pattern, stack decision tree.
- Milan Jovanovic, "Modular Monolith Architecture" --
  https://www.milanjovanovic.tech/blog/modular-monolith-architecture-dotnet
- JetBrains, "Modular Ktor: Building Backends for Scale" --
  https://blog.jetbrains.com/kotlin/2025/07/modular-ktor-building-backends-for-scale/
- sachith.co.uk, "Modular Monoliths Done Right" (Jun 2026) --
  https://www.sachith.co.uk/modular-monoliths-done-right-scaling-strategies-practical-guide-jun-3-2026/
