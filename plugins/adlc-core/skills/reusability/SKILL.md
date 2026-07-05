---
name: reusability
description: >-
  Guides the extract-vs-keep judgment: decide whether two similar pieces of code
  are real duplication worth extracting or coincidental look-alikes to leave apart,
  design a narrow API for the extracted unit, and un-extract an abstraction that
  turned out wrong. Use when the user asks to "make this reusable", "extract a
  shared component/helper", "should I abstract this yet", "is this duplication or
  coincidence", "this shared function has too many flags", "design a reusable API",
  or "this abstraction is fighting me, should I inline it".
version: 0.1.0
---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# Reusability

Reuse pays off when it captures **one real concept** that lives in many places and changes for one reason. Extract too early, or along the wrong axis, and you couple unrelated code: every future caller now needs a flag, and the shared unit costs more than the duplication it removed. This skill is the **judgment** (extract or not, and how to back out). The behavior-preserving mechanics of the extraction itself (Extract Method, Move, rename, keep tests green) live in the sibling skill `refactoring` (see [../refactoring/SKILL.md](../refactoring/SKILL.md)). Reach for this one to decide; reach for that one to do it safely.

## Extract-or-not checklist

Extract **only when every box is ticked**. Any unchecked box means leave the copies where they are.

- [ ] **Third occurrence.** This is the 3rd (not 2nd) place the shape appears. Two copies rarely reveal the true seam; the third shows what actually varies.
- [ ] **Same reason to change.** All copies would change *together, for the same reason* (a rule, a format, a policy). If one could change while the others stay, they are not the same knowledge.
- [ ] **Narrow API is possible.** You can name the concept and expose it behind a small, intention-revealing surface (one function or one component, a handful of params). If the only honest API is "do one of these five things", the concept is not real yet.
- [ ] **Stable core.** What is common is the *invariant*; what differs is passed in. If the "common" part keeps shifting per caller, wait.

If a box is unchecked, prefer duplication: "duplication is far cheaper than the wrong abstraction" (Sandi Metz). Duplication is visible and local; a wrong abstraction is load-bearing and spreads.

## Coincidental vs real duplication (before / after)

Two blocks can look identical and still be **coincidental**: same text today, different reasons to change tomorrow.

```
# COINCIDENTAL: both clamp a number, but for unrelated reasons.
def cap_retry_count(n):   return min(n, 5)   # capped by the retry policy
def cap_page_size(n):     return min(n, 5)   # capped by the UI grid
```
Do **not** extract a shared `clamp5`. The retry cap and the page cap change independently; the day one moves to 8 you would fork the "shared" helper anyway. Same text, different knowledge. Leave them apart.

```
# REAL: one tax rule, copied into three call sites. One reason to change.
subtotal * 1.20   # checkout.py
subtotal * 1.20   # invoice.py
subtotal * 1.20   # receipt.py
```
When VAT changes, all three must move as one. That is one decision duplicated. Extract it: `apply_vat(subtotal)` (or a `TaxRate` value), and the rate lives in exactly one place.

Test to tell them apart: **"if I change one copy, must the others change in lockstep for the program to stay correct?"** Yes = real, extract. No = coincidental, leave it.

## Design the extracted unit: parameterize behavior, not flags

Give the concept a narrow API and hide the rest. When callers vary, **pass in the varying behavior** (a function, a strategy, a slot), and keep the invariant core fixed. Do **not** grow a boolean per caller: flag soup is the top smell that an abstraction merged things that should be separate.

```
# SMELL: boolean-flag soup. Each new caller adds a flag; the body is a maze of ifs.
def send(msg, urgent=False, dry_run=False, retry=False, silent=False): ...

# FIX: parameterize the behavior that varies (strategy / lambda / slot).
def send(msg, transport):        # transport decides how; send() owns the invariant
    transport.deliver(msg)
```

Rules of thumb: compose small focused pieces rather than inherit deep hierarchies; place the unit at the **lowest level that all its users share** (keep a one-module helper in that module; promote to a shared module only when a second module truly needs it, or the shared module becomes a coupling dump); and treat a shared unit as a **contract** (breaking it ripples, so cover it with tests and deprecate deliberately).

## Un-extraction: backing out a wrong abstraction

Signals it is wrong: callers pass flags to *turn off* parts of it; you keep adding params; a change for one caller breaks another; the name is vague (`Manager`, `Helper`, `Base`) because no single concept fits. Reverse it in order:

1. **Inline it back.** Copy the shared unit's body into each caller verbatim (the mechanics are Inline Method / Inline Class in `refactoring`). Keep tests green at each step.
2. **Delete the abstraction** and its flags once every caller is inlined. The maze is gone.
3. **Fork the variants.** Let each call site keep its own now-simple version. Duplication here is the *correct* intermediate state, not a regression.
4. **Look again for the real seam.** With the variants side by side, re-run the extract-or-not checklist. Extract the *true* common core (often smaller than the failed one), or accept that there was none.

Do not skip to step 4. Trying to "fix" a wrong abstraction in place usually adds another flag.

## In UI / design systems

Reusable components plus design tokens are the highest-leverage reuse: one styled, accessible, previewable component beats copy-pasted markup. The same checklist applies (extract on the third real use, behind a clean slot-based API, never a flag per variant). Platform mechanics: `android-shared-composables`, `ios-shared-views`, `ios-design-system`.

## When NOT to use this

Skip extraction (and this skill) when: there are only two occurrences; the copies are coincidental (different reasons to change); the shape is still churning and the "common" part is not stable yet; or the duplication is trivial and local (a two-line idiom read at a glance is cheaper left inline than routed through an import). Reuse is a tool for shared *knowledge*, not a goal in itself. Do not extract to hit a DRY metric.

## References
- Sandi Metz, "The Wrong Abstraction": https://sandimetz.com/blog/2016/1/20/the-wrong-abstraction
- Rule of three / DRY (knowledge, not text): The Pragmatic Programmer; https://en.wikipedia.org/wiki/Rule_of_three_(computer_programming)
