---
name: decision-record
description: >-
  This skill should be used when the user asks to "write an ADR", "create an
  architecture decision record", "document this decision", "record why we chose
  X over Y", "capture the trade-offs for this design choice", or wants a durable
  record of a significant technical decision with its context, alternatives, and
  consequences. Use it when a choice between technologies, patterns, or
  approaches needs to be written down so future maintainers understand the
  reasoning.
version: 0.1.0
---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# Decision Record (ADR)

Output: one `NNNN-short-kebab-title.md` file, written locally, using exactly the template below.

## Template

Write exactly these sections, in this order:

```markdown
# NNNN. <Short noun phrase: the decision, not the problem>

- Status: Proposed
- Date: YYYY-MM-DD
- Deciders: <names or roles, or `unknown`>

## Context

The forces at play, technical, business, team, and constraint-driven, stated
neutrally, without taking sides. Why is a decision needed *now*? What tensions
must be balanced? 1-2 short paragraphs.

## Decision

"We will <do X>." State the choice in active voice as a directive. Be specific
and unambiguous about what is being adopted.

## Alternatives considered

For each real option NOT chosen, one line on what it was and why it lost. Omit
this section only if there were genuinely no alternatives.

- **<Option A>**: <why rejected>
- **<Option B>**: <why rejected>

## Consequences

What becomes easier and what becomes harder as a result, both positive and
negative, and any follow-up work this creates. Honest about the downsides.
```

## When to write one

Write an ADR for a decision that is **architecturally significant**: costly to
reverse, affects multiple modules/teams, or sets a precedent. Examples: choosing
a datastore, a DI framework, an API style, a module boundary, a build tool.

Do NOT write one for reversible, local, or obvious choices (variable naming, a
single function's internals). When unsure, ask: "Will someone six months from now
ask *why* we did this?" If yes, write it.

## Two homes: by audience

- **Product/code decisions** (datastore, DI, API style, module boundary in the project being built): the ADR lives **in the repo** at `docs/adr/NNNN-title.md` so it travels with the code and reviewers see it. In a poly-repo product, write it in the member repo the decision is about (its `docs/adr/`), on that repo's `adlc/<run-id>` branch.
- **Operator/setup decisions** (how the agentic coding tool, the config, or the workflow itself works): the ADR lives **at the user level** in `~/.openadlc/decisions/YYYY-MM-DD-title.md` so it spans projects.

Pick the home by what the decision is about. Whichever you write, drop a **one-line cross-pointer** in the other place's index and link back to the spawning plan (the run's `~/.openadlc/runs/<workspace>/<run-id>/plan/spec.md`, per [references/run-isolation.md](../../references/run-isolation.md)) if there is one. When an ADR is spawned mid-run, stage the draft under that run's out-of-repo `~/.openadlc/runs/<workspace>/<run-id>/decision/` before it lands in its permanent home, so the run's artifacts stay together. The staged draft is never committed; only the ADR in its permanent home (repo `docs/adr/` on `adlc/<run-id>`, or user-level `~/.openadlc/decisions/`) is. Never write the same decision in both with diverging text.

## Workflow

1. **Locate the ADR directory** (per the audience split above). Repo ADRs: look for `docs/adr/`, `doc/adr/`, `docs/decisions/`, or an `adr`/`decisions` folder; if none exists, ask the user and create it. User-level ADRs: `~/.openadlc/decisions/` uses `YYYY-MM-DD-title.md`. Match the existing convention in whichever home you write.
2. **Find the next number.** ADRs are numbered sequentially, zero-padded:
   `0001-...`, `0002-...`. Scan existing filenames for the highest number, add 1.
   File name = `NNNN-short-kebab-title.md` (e.g. `0007-use-postgres-for-events.md`).
3. **Gather the real forces.** Before drafting, confirm with the user: what
   problem forces a decision now, what options were genuinely considered, and what
   they actually chose. Do NOT invent alternatives or consequences, mark anything
   unconfirmed as `unknown` and ask.
4. **Draft** using the template below. Set `Status: Proposed`.
5. **Write the file** to the ADR directory.
6. **Report** the path and the one-line decision back to the user.

## Status lifecycle (immutability rule)

ADRs are an append-only log. **Never delete or rewrite an accepted ADR.**

- `Proposed` → `Accepted` when the team agrees.
- `Accepted` → `Deprecated` when no longer relevant (no replacement).
- `Accepted` → `Superseded by NNNN` when a later ADR reverses it. Add a link both
  ways: the old ADR points to the new one, the new one references the old.

To change a decision, write a NEW ADR and mark the old one superseded. The
historical record stays.

## Quality bar

- Title is a noun phrase naming the decision (`Use Postgres for the event store`),
  not the problem (`Database options`).
- Context is neutral: no advocacy. Save the choice for Decision.
- Alternatives are *real* ones that were weighed, with honest reasons for
  rejection. Do not fabricate to pad the list.
- Consequences include at least one genuine downside or trade-off.
- One decision per record. If two decisions appear, split into two ADRs.

## Outbound consent

Local work needs no approval. Anything outbound (publish, push, post) needs an explicit per-action "yes"; see the global consent law.

## References

- Michael Nygard, "Documenting Architecture Decisions" (the original ADR format):
  https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions
- ADR organization, tooling, and templates: https://adr.github.io/
