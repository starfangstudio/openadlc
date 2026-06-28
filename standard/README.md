<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# The ADLC standard

ADLC is the open, vendor-neutral Agentic Development Lifecycle: a seven-phase lifecycle, seven principles, and a human-in-the-loop core, written so any agent or harness can implement it.

> Status: draft proposal, pre-ratification. Spec version 0.1. It goes live on openadlc.com with the OpenADLC core at launch; until then it is a draft and packs build against it.

## Read in order

- [onepage.md](onepage.md): the whole thing on one screen.
- [manifesto.md](manifesto.md): the why.
- [principles.md](principles.md): the seven non-negotiables.
- [spec.md](spec.md): the normative standard (RFC-2119), the seven-phase lifecycle, the laws, human-in-the-loop, the pack shape, the adapter seam, conformance.
- [adoption.md](adoption.md): how to declare it (Core / Governed / Certified).

## The buildable layer

- [conformance.md](conformance.md): the machine-checkable test plus a `.adlc/conformance.yaml` manifest.
- [conformance-checker.md](conformance-checker.md): the reference checker spec.
- [pack-format.md](pack-format.md) + [schema/](schema/pack-manifest.schema.json): the vendor-neutral pack manifest and capability vocabulary, with passing and failing validation.

## ADLC vs OpenADLC

ADLC is the open standard (the *what*). **OpenADLC** is this project's implementation of it (the *how*): the four-command harness, the consent checkpoint, and the pack library. The standard's seven principles are the neutral category's laws; OpenADLC's [PRINCIPLES.md](../PRINCIPLES.md) (ten) are this product's design tenets, a superset. The conformance levels (Core / Governed / Certified) are shared.

ADLC is a generic, multi-vendor term with no single owner. OpenADLC does not claim to own it; it aims to be the most rigorous open standard for the shared category.

## License

Two trees, two licenses. They are not the same thing and are not under the same terms.

- **This `standard/` tree is a genuine open standard, CC-BY-4.0.** Free for anyone to read, implement, and build on, with attribution. That is the credibility anchor: the *what* is open. Nothing in this tree is gated, and Principle 7 (vendor neutrality, no lock-in) is why.
- **The implementation and packs are NOT under this license.** The OpenADLC reference implementation (the harness, hooks, adapters, the four `/agentic-*` commands) and the packs are **source-available + commercial**: publicly viewable and free for individuals and the public to read, use, and modify, but use by a team or organization requires a commercial seat license (a solo individual, including a freelancer on client work, stays free). They are governed by the OpenADLC source-available license (see the `LICENSE` file), not by CC-BY. See the root [README](../README.md).

Framing: open standard, commercial reference implementation. The standard is open. The reference implementation is source-available and free for individuals; organizations need a seat.
