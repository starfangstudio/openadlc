<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
# OKF bundles

Every lifecycle artifact is one **OKF bundle**: a directory of markdown files with YAML frontmatter, conformant to the [Open Knowledge Format v0.1](https://github.com/GoogleCloudPlatform/knowledge-catalog/tree/main/okf). Intake produces one, plan produces one, and they travel through the tracker between commands.

## Why a bundle

One canonical artifact, plain files, readable by a human and an agent without tooling, diffable, and portable. The bundle carries two jobs at once:

- **A human briefing** (`briefing.md`), built for comprehension: a cold reader gets the work at a glance.
- **The full AI context** as typed concepts, built for completeness: every detail, so the build does not drift.

This defeats the two ways intake fuel fails: too thin and the agent guesses; too AI-first and the human is locked out.

## What a run writes

The run workspace **is** the bundle (see [run isolation](run-isolation.md)). It is kept flat, concepts one level deep. Every concept is one `.md` file with frontmatter; the only hard rule is a non-empty `type`.

Intake bundle:

```
~/.openadlc/runs/<workspace>/<run-id>/
├── index.md          # okf_version: "0.1"; the listing
├── briefing.md       # type: Briefing   the human face (problem, goal, AC, open Qs)
├── story.md          # type: Story|Bug|Epic|TechDebt|Intent  the classified unit
├── discovery.md      # type: Reference  deep-discovery findings, cited
├── dependencies.md   # type: Reference  development dependencies, order
└── log.md            # optional  run history (POSTED, urls)
```

Plan bundle (one per domain, under the same run):

```
~/.openadlc/runs/<workspace>/<run-id>/plan/
├── index.md          # okf_version: "0.1"
├── briefing.md       # type: Briefing   the human-readable plan summary
├── spec.md           # type: Plan       run_id + branch in frontmatter; AC mapping
├── Plans.md          # type: Plan       slice breakdown mapped to AC
└── <contract>.md     # type: Reference  contracts, design refs, cross-repo order
```

## Concept types

Each concept's frontmatter uses `type` (not `concept`), one of: `Briefing` (the human face), `Story` / `Bug` / `Epic` / `TechDebt` / `Intent` (the classified unit at intake), `Plan` (spec, slices), or `Reference` (discovery, dependencies, contracts, design notes). `briefing.md` is always the human face; the rest is the AI context.

## How it travels through a tracker

A tracker has no concept of a bundle, so each adapter serializes it. The visible body is always `briefing.md`; the AI concepts ride along.

- **GitHub** (no attach API): the body is `briefing.md`, the concepts go inside one `<details>` block as typed sections (each opened by a `<!-- okf:concept path=... type=... -->` hint), overflowing past ~60KB into follow-up comments.
- **Jira:** the body is `briefing.md` converted to ADF, and the bundle is attached as `<slug>.okf.tgz`.

GitHub and Jira are the committed trackers; a demand-driven work-item tracker (added only on partner demand) follows the same body-plus-attachment shape as Jira.

Reading is LLM-native: the next command reads the issue (GitHub) or untars the attachment (Jira) and rebuilds the local bundle. There is no byte-exact wire protocol; comprehension is the contract.

## Source of truth

The bundle is canonical; the visible briefing is a live view of `briefing.md`. If a human edits the visible GitHub briefing, the edit is folded back into `briefing.md`, never silently discarded. The em-dash ban applies to every file in the bundle.

## Source

- Reference: [plugins/adlc-core/references/okf.md](../../plugins/adlc-core/references/okf.md)
