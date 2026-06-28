---
name: code-documentation
description: "This skill should be used when the user asks to \"write docs for\", \"document this\", \"create a README\", \"write a runbook\", \"write an onboarding guide\", \"document the API\", or otherwise needs technical writing for code (API docs, architecture docs, operational runbooks). Wraps the engineering:documentation built-in and adds the ADLC verify-against-code and outbound-consent deltas."
version: 0.1.0
---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# Code documentation (ADLC wrapper)

Wrap the built-in **`engineering:documentation`** skill for all technical writing (READMEs, API docs, architecture docs, runbooks, onboarding guides). That skill owns the structure, audience framing, and prose quality. This wrapper adds only the ADLC delta: **docs must be verified against the code**, and **publishing them is an outbound action that needs the operator's explicit yes**.

## How to run

1. **Invoke the built-in.** Run `engineering:documentation` to produce the draft. Let it choose the document type and structure.
2. **Apply the ADLC deltas below** before anything leaves the machine.

## Scope: what to document
Pick the right artifact for the need (the built-in handles prose/structure; this is the *what*):
- **In-code docs:** doc comments on every public class/interface and non-trivial method/function, purpose, params, return, throws, threading/nullability, and the *why* of non-obvious choices. Use the language convention (KDoc / Javadoc / Python docstrings / TSDoc). Don't restate the signature or document trivial getters.
- **READMEs:** per module/repo, what it is, how to build/run/test, entry points, gotchas. Keep beside the code.
- **Architecture docs / ADRs:** structure, boundaries, and the decisions behind them (pairs with `decision-record` and `software-design`).
- **Runbooks / onboarding:** operational and setup steps.
- **Diagrams, generate these** (the architect-level resources). Prefer text-based, version-controlled formats, **Mermaid** or **PlantUML**: so they diff and live in the repo:
  - module/dependency map or **C4** (context → container → component),
  - **sequence** diagrams for key flows, **ER** diagrams for the data model, **state** diagrams for state machines.
  Render to SVG/PNG only when a static asset is needed. Every diagram must match the real code, verify, don't sketch from memory.

## ADLC delta

### Verify against the code, never invent
- Every factual claim (function signature, flag, endpoint, env var, command, file path, return type) MUST be checked against the actual source before it goes in the doc. Read the code; do not document from memory or assumption.
- Run the exact commands the doc tells the reader to run (install, build, test, curl an endpoint). If a command or example cannot be verified, mark it `unknown` and flag it, do not present an unverified command as working.
- A doc that drifts from the code is worse than no doc. When the doc and the code disagree, the code is the source of truth, fix the doc, or raise the code bug separately.

### Keep it minimal and co-located
- Prefer deleting or updating stale docs over adding new ones. Match the surrounding docs' tone and depth.
- Document the *why* (decisions, trade-offs, gotchas), the *what* is already in the code. Skip narration the reader can read off the source.
- Put the doc where it will be maintained (README beside the module, docstring on the symbol, runbook in the ops dir) rather than a detached wiki that rots. Docs are repo content: inside an ADLC run, doc commits go on that repo's `adlc/<run-id>` branch (per repo, in a poly-repo product), never on `main`, never in the out-of-repo run workspace (see [references/run-isolation.md](references/run-isolation.md)).

### 🚦 Outbound consent, publishing is outbound
Writing and editing doc files locally needs no approval. The moment a doc is pushed to a remote, published to a docs site/wiki, posted to a PR, or sent to anyone, it leaves the machine and needs the operator's explicit yes.

Publishing/posting a doc anywhere is outbound: get the operator's explicit yes first (the global law): present what would go out + the verification results, wait for an explicit "yes". Never publish docs autonomously.

## References
- Built-in wrapped: `engineering:documentation`
- Run isolation (run branch `adlc/<run-id>`, code/docs in git vs out-of-repo artifacts, poly-repo): [references/run-isolation.md](references/run-isolation.md)
- ADLC outbound consent: see project `CLAUDE.md` (outbound needs the operator's explicit yes, THE law) and `rules/` deltas.
