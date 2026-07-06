---
name: design-principles
description: "This skill should be used when the user asks to \"apply SOLID\", \"is this good design\", \"this class does too much\", \"reduce coupling\", \"DRY this up\", \"should I add this abstraction\", or wants a principled critique of code structure. Covers SOLID, DRY/KISS/YAGNI, composition-over-inheritance, and the law of Demeter. Language-agnostic."
version: 0.1.0
---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# Software design principles

Principles are heuristics that lower the cost of change and reading, not laws. Apply where they pay off; **YAGNI and KISS outrank the rest** and guard against over-engineering.

Boundary: this skill holds the always-on rules (SOLID, DRY/KISS/YAGNI, composition). The sibling skill `design-patterns` holds named moves (Strategy, Factory, Observer, ...) reached for only once a specific change pressure is present; check principles first, reach for a pattern only if the pressure survives that gate.

## SOLID (with the smell each one fixes)
- **S, Single Responsibility.** A unit has one reason to change. Smell: a class that parses, validates, persists, and formats. Fix: split by axis of change.
- **O, Open/Closed.** Extend behavior without editing stable code. Smell: a growing `when/switch` on a type. Fix: polymorphism or a strategy, *only once variants actually multiply*.
- **L, Liskov Substitution.** A subtype must honor the supertype's contract. Smell: an override that throws or weakens guarantees. Fix: don't subclass; compose, or rethink the hierarchy.
- **I, Interface Segregation.** Many small role-interfaces over one fat one. Smell: implementers forced to stub methods they don't use. Fix: split the interface to the callers' real needs.
- **D, Dependency Inversion.** Depend on abstractions; high-level policy shouldn't depend on low-level detail. Smell: a ViewModel `new`-ing an HTTP client. Fix: inject an interface (see `software-design`).

## The pragmatic four (apply these first)
- **KISS**: the simplest thing that works and reads. Clever is a cost.
- **YAGNI**: build what's needed now, not what might be needed. Speculative generality is the most common waste.
- **DRY**: one authoritative home for each piece of *knowledge*. But DRY is about knowledge, not text: two lines that look alike but change for different reasons are **not** a duplication, see `reusability`.
- **Composition over inheritance**: prefer has-a/uses-a; reserve inheritance for genuine is-a with a stable contract.

## Also worth holding
- **Separation of concerns**: UI, logic, and data are different jobs; don't braid them.
- **Law of Demeter**: talk to immediate collaborators, not `a.b().c().d()`; long chains couple you to internals.
- **Make the change easy, then make the easy change** (Beck), refactor toward the seam first, then add the feature.

## How to apply in review
For each flagged spot: name the principle, show the smell at `path:line`, propose the smallest fix, and say whether it's worth doing now or is YAGNI. Don't demand an abstraction for a single case.

## References
- SOLID: Robert C. Martin, "The Principles of OOD", https://web.archive.org/web/20150906155800/http://www.objectmentor.com/resources/articles/Principles_and_Patterns.pdf
- DRY / KISS / YAGNI: The Pragmatic Programmer; https://martinfowler.com/bliki/Yagni.html
- Composition over inheritance: https://en.wikipedia.org/wiki/Composition_over_inheritance
