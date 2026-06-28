---
name: software-design
description: "This skill should be used when the user asks to \"structure the code\", \"where should this live\", \"design the layers\", \"separate concerns\", \"decouple from the framework/DB/UI\", \"what architecture should I use here\", \"is this over-engineered\", or is reviewing whether dependencies point the right way. Broad, language-agnostic software design: separation of concerns, dependency direction, and a light domain/data/presentation/ui layering applied only where it earns its keep, plus picking the architecture that fits the context. Complements domain rules (e.g. android-architecture)."
version: 0.1.0
---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# Software design

Design for **change-cost, not purity**. Use the lightest structure that does the job, and add ceremony only when the code earns it. Full "clean architecture" (a port and an interface for everything) generates a lot of boilerplate; most apps want pragmatic layering instead.

## The principles that always apply
- **Separation of concerns.** One reason to change per unit. Business rules, data access, and presentation are different jobs; do not blend them in one class.
- **Dependency direction.** Point dependencies toward stable things: business logic depends on nothing; details (DB, UI, network) depend on the logic, never the reverse. Depend on an abstraction only where a real seam exists.
- **High cohesion, low coupling.** Things that change together live together; things that do not should not know about each other.
- **Keep the core clean.** Business logic must not import a framework, a UI type, or a DB driver. Cross a boundary with a plain data structure, never a leaked `Cursor` / `Response` / `View`.

## The light layering (the default)
Four layers, dependencies flowing toward the domain:
```
ui  ->  presentation  ->  domain  <-  data
```
- **domain**: entities, business rules, use-cases. Pure and framework-free; knows nothing about the others.
- **data**: repositories, data sources (DB / network / cache), DTOs and mapping to domain models. Implements interfaces the domain defines.
- **presentation**: state holders / ViewModels / controllers, presentation logic (what to show, formatting, handling events). Depends on the domain, not on the rendering toolkit.
- **ui**: views, components, screens; rendering only. Observes presentation state and emits events; no business logic.

This is the practical MVVM / MVI-shaped split. It gives you testable logic and swappable details without the full clean-architecture ring ceremony.

## Apply it where it earns its keep (do not over-engineer)
- **Match ceremony to stakes.** A CRUD screen, a script, or a tiny feature does not need four layers; collapse them (ui + presentation together, or domain folded into the data call). Full layering pays off in long-lived apps with real domain logic.
- **Start with the domain-vs-details split** (the highest-value boundary). Add presentation and data layers as logic and surfaces multiply.
- **No interface "just in case".** A seam you will never swap is YAGNI. Add an abstraction when a second implementation, a test seam, or real coupling pain actually appears, not before.

## Pick the architecture that fits
Layered (above) is the default and covers most apps. Reach for more only when the context demands it: hexagonal / ports-and-adapters for many delivery mechanisms, event-driven for decoupled async flows, a modular monolith for team and boundary scaling. Match the codebase's existing pattern before importing a new one.

## Smells that say "fix the boundary"
- Business logic importing `android.*` / `java.sql.*` / an HTTP client: a leak. Move the logic inward, hide the detail behind an interface.
- A "service" that hits the DB, formats UI strings, and decides policy: no boundaries. Split by responsibility.
- Cannot unit-test the logic without a DB or emulator: the logic is tangled with a detail. Invert the dependency.

## References
- Layered + MVVM / MVI presentation patterns are the practical default.
- Robert C. Martin, "The Clean Architecture" (for the dependency-rule intuition, not the full ceremony): https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html
- Alistair Cockburn, Hexagonal Architecture (Ports and Adapters), for when many delivery mechanisms justify it: https://alistair.cockburn.us/hexagonal-architecture/
- Domain-specific module / DI rules live in their own rules (e.g. `android-architecture`).
