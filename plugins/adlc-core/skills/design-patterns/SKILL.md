---
name: design-patterns
description: "This skill should be used when the user asks \"which pattern fits here\", \"is a pattern warranted\", \"refactor to a strategy/factory/observer\", \"how do I decouple these objects\", or wants help recognizing/applying (or avoiding) a design pattern. Covers the common GoF patterns, when to reach for one, and the anti-patterns. Language-agnostic."
version: 0.1.0
---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# Design patterns

Patterns are named solutions to recurring design problems, a shared vocabulary, not a goal. **Reach for one when the problem actually appears**, never to show you know it (that's the #1 over-engineering trap).

## The ones you'll actually use
**Creational**
- **Factory / Factory Method**: choose/create a concrete type behind an interface; centralizes construction.
- **Builder**: assemble an object with many optional parts readably (avoids telescoping constructors).
- **Dependency Injection**: pass collaborators in rather than constructing them; the backbone of testable, decoupled code.

**Structural**
- **Adapter**: make an incompatible interface fit what callers expect (wrap a 3rd-party API).
- **Decorator**: add behavior by wrapping, not subclassing (composable cross-cutting concerns).
- **Facade**: one simple entry point over a complex subsystem.
- **Repository**: a collection-like interface over data access; keeps persistence out of the domain.

**Behavioral**
- **Strategy**: swap an algorithm/policy at runtime; the clean replacement for a growing type `switch`.
- **Observer / Pub-Sub**: notify many listeners of change without coupling (Flow/LiveData/event bus are this).
- **State**: behavior keyed to an explicit state instead of scattered booleans.
- **Command**: reify an action as an object (undo, queues, dispatch).

## When to reach for one (and when not)
- Apply a pattern when the **problem it solves is present**: real variation (Strategy), real incompatibility (Adapter), real construction complexity (Builder). If there's one case and no variation, a plain function/class is better, **YAGNI**.
- Prefer the **lightest** option: a function over a class, a lambda/Strategy over a class hierarchy, language features over ceremony.
- Name the pattern in code/PRs so readers get the vocabulary, but don't rename simple code into pattern-speak.

## Anti-patterns to flag
- **God object / blob**: one class that knows/does everything → split (SRP).
- **Singleton abuse**: global mutable state hiding dependencies → inject instead.
- **Premature abstraction / pattern-itis**: factories and interfaces with one implementation "for flexibility" → delete; add when the second case is real.
- **Anemic domain + fat service**: data classes with all logic in a service → move behavior to where the data is when it belongs there.

## References
- Gamma, Helm, Johnson, Vlissides (GoF), "Design Patterns: Elements of Reusable OO Software".
- Refactoring.Guru: patterns catalog with examples, https://refactoring.guru/design-patterns
