---
name: architect-contract
description: >-
  This skill should be used when the user asks to "define the contract before
  coding", "design the API/module interface first", "what should this module
  expose", "set the boundary between feature A and feature B", "review this
  public API", "design the -api module", or "decide what's public vs internal".
  Produces a contract spec (types, methods, errors, ownership) that implementation
  must satisfy, before any -impl code is written.
version: 0.1.0
---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# Architect the contract first

Define the *interface* a module exposes before writing its implementation. The
contract is the agreement other modules depend on; the impl is a private detail
that can change freely. Get the contract right and the rest is replaceable.

Apply this when planning a new feature module, splitting a monolith, or letting
two features interact. Output a contract spec, not code.

## When to invoke
- New feature module → before any `-impl` code.
- Two features need to talk → before either side writes integration code.
- Reviewing a proposed public API / `-api` module diff.
- A bug traced to a leaky or accidental public surface.

## The flow
1. **Name the consumer and the need.** Who calls this and what do they actually
   need? If no concrete caller exists, the surface is speculative, cut it.
2. **Model the resource, not the action.** Prefer nouns (data + a few standard
   verbs) over a sprawl of bespoke methods. List the entities and their relations.
3. **Draft the contract spec** (format below). Types, methods, errors, ownership.
4. **Run the H1–H16 review heuristics** (below) against the draft. Fix every fail.
5. **State the stability promise.** What is guaranteed, what may change, version.
6. **STOP, get the contract approved** before any implementation begins.

## Contract spec format
Emit exactly this. Keep it tight.

```
# Contract: <module-name>-api

## Consumers
- <module> needs <capability>, because <concrete use case>

## Surface (public types + signatures)
interface/data only, no implementation, no DI framework annotations
- <Type/Method signature>   # one line on intent

## Errors
- <Operation> → <sealed result / Result<T> / typed exception>  (never null-on-failure)

## Ownership & stability
- Owner: <team/module>
- Stability: experimental | stable
- Version / compat policy: <additive-only? deprecation window?>

## Explicitly NOT in scope
- <thing>, kept internal because <reason>
```

## H1–H16: public-API review heuristics
Check the draft against each. Any fail blocks approval.

1. **Minimal surface**: every public element has a real caller. Default to private.
2. **No impl leakage**: no concrete classes, frameworks, threads, or transport
   types in the contract. Interfaces and data only.
3. **Resource-oriented**: model nouns + standard verbs (get/list/create/update/
   delete) before inventing custom methods.
4. **Consistent naming**: same concept, same name everywhere; verbs for actions,
   nouns for resources; no abbreviations that aren't already idiomatic here.
5. **Typed errors**: fallible operations return a sealed result / `Result<T>` /
   documented typed exception. Never null-on-failure, never throw across the boundary undocumented.
6. **No primitive obsession**: wrap meaningful values (Ids, money, urls) in types,
   not bare `String`/`int`.
7. **Nullability explicit**: every param and return states whether null/absent is allowed.
8. **No boolean traps**: replace ambiguous boolean params with enums/named types.
9. **Immutable data**: exposed data classes are immutable; no leaking mutable internals.
10. **Async contract clear**: suspend/Flow/callback shape and threading expectations stated.
11. **Additive evolution**: new fields/methods don't break callers; required fields
    aren't added to existing types; enums handle unknown values.
12. **No circular dependency**: an `-api` doesn't depend on another `-api` except a
    narrow documented one (navigation, feature-toggle).
13. **Stable identifiers**: IDs/keys exposed are stable and documented, not internal row ids.
14. **Pagination & limits**: list/collection methods specify paging and bounds, not unbounded returns.
15. **Idempotency & side effects**: each method documents whether it's safe to retry.
16. **Documented & versioned**: each element has a one-line doc; module states its
    version and compatibility policy.

## Hard gates
- The contract spec must exist and pass H1–H16 **before** implementation starts.
- **STOP and get explicit approval** of the contract before writing `-impl` code, the contract is what every other module will couple to.
- This skill produces a spec only. Pushing, publishing, or sharing the contract
  outside this machine needs the operator's explicit yes first, never autonomous.

## Android note
In a modular Android layout the contract IS the `-api` module: interfaces and
data classes, no DI framework, no UI. An `-impl` depends on its own `-api` and
other features' `-api` only, never another `-impl` (H12). See
the `adlc-android` plugin's `references/android-architecture.md` for the full module split and scope rules.

## References
- Google Cloud API Design Guide: resource-oriented design, standard methods,
  naming, versioning, backward compatibility, errors:
  https://docs.cloud.google.com/apis/design (AIP-121 resource design, AIP-180 compat).
