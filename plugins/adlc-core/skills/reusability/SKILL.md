---
name: reusability
description: >-
  Guides the extract-vs-keep decision: when to pull shared code into a reusable
  unit and how to design its API without over-abstracting. Use when the user
  asks to "make this reusable", "extract a shared component", "should I abstract
  this yet", "is this duplication or coincidence", or "design a reusable API".
version: 0.1.0
---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# Reusability

Reuse cuts maintenance and bugs when it captures *one real concept used in many places*. Done too early or on the wrong axis, it couples unrelated code and costs more than the duplication it removed.

## The core judgment: duplication vs. the wrong abstraction
- **Rule of three.** Two occurrences? Usually leave them. On the **third**, look for the shared concept and extract, by then you can see what actually varies.
- **DRY is about knowledge, not text.** Extract when the duplicated thing is *one decision/rule* that must change together. Two snippets that look alike but change for different reasons are **coincidental duplication**: leave them apart.
- **"Duplication is far cheaper than the wrong abstraction"** (Sandi Metz). If an abstraction needs a flag/param for every new caller, it's wrong, inline it back and re-extract along the real seam.

## How to design something reusable
- **Find the stable concept first**, then give it a narrow, intention-revealing API. Expose what callers need, hide the rest. A reusable unit with a leaky or huge surface isn't reusable.
- **Parameterize behavior, not identity**: pass in the bits that vary (a strategy, a slot, a config), keep the invariant core fixed. Avoid boolean-flag soup; if flags multiply, you've merged two things.
- **Compose, don't inherit** for sharing, small focused pieces combined, over deep hierarchies.
- **Place it at the right level.** A util used in one module stays in that module; promote to a shared module only when a second module truly needs it (premature shared modules become dumping grounds and coupling hubs).
- **A reused thing is a contract.** Once shared, breaking it ripples, version/deprecate deliberately, and cover it with tests.

## In UI / design systems
Reusable components + design tokens are the highest-leverage reuse: one styled, accessible, previewable component used everywhere beats copy-pasted UI. See `android-shared-composables` (extracting composables) and `android-design-system` (component + token reuse). Same judgment applies: extract a component on the third real use, with a clean slot-based API, not on the first.

## References
- Sandi Metz, "The Wrong Abstraction": https://sandimetz.com/blog/2016/1/20/the-wrong-abstraction
- Rule of three / DRY: The Pragmatic Programmer; https://en.wikipedia.org/wiki/Rule_of_three_(computer_programming)
