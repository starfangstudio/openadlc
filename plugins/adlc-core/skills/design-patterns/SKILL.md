---
name: design-patterns
description: "This skill should be used when the user asks \"which pattern fits here\", \"is a pattern warranted\", \"do I need a strategy/factory/builder/observer/adapter here\", \"how do I decouple these objects\", \"refactor this growing switch\", or wants to recognize, apply, or avoid a design pattern under real change pressure. A decision procedure, not a catalog: match a code smell to a candidate pattern, weigh its cost, gate it behind YAGNI. Boundary: design-principles = the always-on rules of good structure; design-patterns = named solutions reached for only under specific change pressure. Language-agnostic."
version: 0.2.0
---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# Design patterns

A pattern is a named solution to a recurring problem, reached for **only when the change pressure that earns it is actually present**. Applying a pattern to show you know it is the top over-engineering trap. This skill is a decision procedure, not a menu.

Boundary: `design-principles` holds the always-on rules (SOLID, DRY/KISS/YAGNI, composition). This skill holds the named moves you reach for under a specific pressure. Principles first; pattern only if the pressure survives step 1.

## Step 1: the YAGNI gate (do this before naming any pattern)
Reach for the **lightest option that removes the pressure**, in this order. Stop at the first that works.
1. **A function or a parameter.** One extra behavior? Pass a lambda or a flag. No new type.
2. **A plain data structure.** Branching on a kind? A map or table of values often beats a class hierarchy.
3. **A language feature.** Enums, sealed/union types, first-class functions, DI via constructor. Most "patterns" are ceremony around what the language already gives you.
4. **Only then, a named pattern**, and only when there are **two or more real cases now** (not one imagined case later). One variant is not variation; it is indirection tax.

## Step 2: signals -> candidate pattern
Match the smell or the pressure, not the vibe. If no row matches, you do not need a pattern.

| Signal you see in the code / PR | Candidate | Lightest thing to rule out first |
| --- | --- | --- |
| Growing `switch`/`when` on a type, each arm an algorithm | **Strategy** | A lambda parameter or a lookup map |
| Construction has many optional parts, telescoping constructors | **Builder** | Named/default args, a config object |
| Callers pick a concrete type by a runtime input | **Factory Method** | A `when` returning the type, if it is stable |
| A 3rd-party or legacy interface does not fit callers | **Adapter** | A thin wrapper function |
| Cross-cutting behavior (logging, caching) bolted onto many types | **Decorator** | A higher-order function |
| A complex subsystem leaks its internals to callers | **Facade** | One well-named module function |
| Persistence details bleed into domain logic | **Repository** | A single data-access function, if queries are few |
| Behavior branches on scattered booleans / a status field | **State** | A sealed type + exhaustive `when` |
| One change must notify many decoupled listeners | **Observer / Pub-Sub** | A direct call, if there is one listener |
| An action must be queued, undone, logged, or replayed | **Command** | A function reference |
| A collaborator is `new`ed inside the class that uses it | **Dependency Injection** | (Almost always do this; see design-principles D) |

## Step 3: per-pattern cost (when each one backfires)
No pattern is free. Reach for it only if the benefit above outweighs this.
- **Strategy**: with one strategy it is pure indirection tax; the reader now chases an interface to find one implementation.
- **Builder**: duplicates the object's fields; drifts out of sync and hides required-vs-optional. Skip it if defaults cover the cases.
- **Factory Method**: adds a layer that obscures which concrete type you get; over-applied, every `new` becomes a factory call.
- **Adapter**: hides the real cost/shape of the wrapped API; a leaky adapter is worse than calling the API directly.
- **Decorator**: deep wrap stacks make control flow and stack traces hard to follow; ordering becomes load-bearing and invisible.
- **Facade**: can become a god object that everything routes through, re-coupling what it was meant to hide.
- **Repository**: over a single store it is a pass-through; the abstraction earns its keep only across stores or for test seams.
- **State**: an explosion of state classes for a 3-state machine is heavier than a sealed type + `when`.
- **Observer / Pub-Sub**: creates invisible control flow (who reacts to this event?); leaks listeners and makes ordering nondeterministic.
- **Command**: reifies every action into an object; without undo/queue/replay it is just a slower function call.
- **Dependency Injection**: the exception, low cost and high payoff; the failure mode is a hand-rolled service locator masquerading as DI.

## Step 4: the one sketch (Strategy, the most common earned move)
A growing type `switch` is the classic signal. Collapse it behind one small interface, but only once there are two-plus real policies.
```
// smell: switch grows every time a new shipping rule appears
fun fee(order) = when (order.region) { "US" -> ...; "EU" -> ...; /* +N */ }

// earned Strategy: each policy is a value; adding one adds no branch
interface FeePolicy { fun fee(order): Money }
val policies: Map<Region, FeePolicy> = mapOf(US to UsFee, EU to EuFee)
fun fee(order) = policies.getValue(order.region).fee(order)
```
If there were one region, the `when` was fine. The pattern earns its place at the second policy, not the first.

## Apply-in-review checklist
Flag, at `path:line`, with the smallest fix:
- **Pattern without the pressure**: a factory/interface/strategy with exactly one implementation "for flexibility". Delete it; inline the concrete type. Add the seam when the second case is real.
- **Pattern half-applied**: a Strategy interface still switched on by callers; a Repository that returns ORM entities; an Observer no one unsubscribes from. Finish it or remove it.
- **Wrong pattern for the smell**: Builder where default args suffice; Command with no undo/queue; Decorator where a function composes cleaner.
- **Skipped the YAGNI gate**: a class hierarchy where a map or a lambda removed the same pressure. Prefer the lighter form.
- **Unnamed but present**: correct pattern, no name in code or PR. Name it so readers get the vocabulary. Do not rename simple code into pattern-speak.

## When NOT to reach for a pattern
- **One case, no variation.** A plain function or class is clearer. Patterns pay off across two-plus real cases.
- **The pressure is imagined.** "We might need to swap this later" is YAGNI. Add the seam when "later" arrives.
- **The language already solves it.** Sealed types, enums, first-class functions, and constructor DI dissolve many GoF patterns; do not rebuild them by hand.
- **It fights the framework.** If Flow/LiveData/Combine already give you Observer, or the DI container gives you Factory, use those; do not hand-roll a parallel one.
- **A principle, not a pattern, is the fix.** God object, singleton abuse, anemic domain: those are `design-principles` violations (SRP, DIP). Fix the principle, do not paper over it with a pattern.

## References
- Gamma, Helm, Johnson, Vlissides (GoF), "Design Patterns: Elements of Reusable OO Software".
- Refactoring.Guru: patterns catalog with worked examples, https://refactoring.guru/design-patterns
- Sibling skill: `design-principles` (SOLID, DRY/KISS/YAGNI, the always-on rules that come first).
