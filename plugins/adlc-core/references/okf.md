<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
# OKF artifacts (ADLC)

Every lifecycle artifact is one **OKF bundle**: a directory of markdown files with YAML frontmatter, conformant to the [Open Knowledge Format v0.1](https://github.com/GoogleCloudPlatform/knowledge-catalog/tree/main/okf). Intake produces one, plan produces one, and they travel through the tracker between commands. The run workspace IS the bundle; we do not invent a second container. Loaded by intake, plan, implement, and review; cited from [tracker-adapters.md](tracker-adapters.md) wherever a body is posted.

## Why OKF
One canonical artifact, plain files, readable by a human and an agent without tooling, diffable, portable. We stopped asking "do you want .md or .html"; the bundle carries both jobs at once: a human-facing briefing and the full AI context, as typed concepts. The tracker is the store between commands; the OKF bundle is the source of truth.

OKF is consumed the way OKF intends: **an agent reads the markdown.** We do NOT require a byte-exact wire protocol or a custom parser, because nothing in the lifecycle reassembles a bundle programmatically. On GitHub the next command reads the issue; on Jira/ADO it untars the attached bundle. Keep the layout clean and typed so the agent reconstructs the context reliably.

## The bundle (what a run writes)
The bundle is the run workspace `~/.openadlc/runs/<workspace>/<run-id>/` (per [run-isolation.md](run-isolation.md)). Keep it **flat** (concepts at the bundle root, one level deep). Every concept is one `.md` file with frontmatter; the only hard rule is a non-empty `type`.

Intake bundle:
```
~/.openadlc/runs/<workspace>/<run-id>/
├── index.md          # okf_version: "0.1"; progressive-disclosure listing
├── briefing.md       # type: Briefing   THE HUMAN FACE (problem, goal, AC, open Qs)
├── story.md          # type: Story|Bug|Epic|TechDebt|Intent  the classified unit
├── discovery.md      # type: Reference  deep-discovery findings, cited
├── dependencies.md   # type: Reference  development dependencies, order
└── log.md            # optional  chronological run history (POSTED, urls)
```

Plan bundle (a new technical OKF, per domain, under the same run):
```
~/.openadlc/runs/<workspace>/<run-id>/plan/
├── index.md          # okf_version: "0.1"
├── briefing.md       # type: Briefing   the human-readable plan summary
├── spec.md           # type: Plan       run_id + branch in frontmatter; AC mapping
├── Plans.md          # type: Plan       slice breakdown mapped to AC
└── <contract>.md     # type: Reference  contracts, design refs, cross-repo order
```

`briefing.md` is always the human face. The rest is the AI context. There is no `.html` anymore.

## Concept types (frontmatter `type`, not `concept`)
Each concept's frontmatter MUST use `type`, with one of: `Briefing` (the human face), `Story` / `Bug` / `Epic` / `TechDebt` / `Intent` (the classified unit at intake), `Plan` (spec, slices), `Reference` (discovery, dependencies, contracts, design notes). Consumers tolerate unknown types; pick descriptive ones. Do not invent a `concept:` field; OKF's queryable field is `type`.

## Posting the bundle (per tracker)
The tracker has no concept of an OKF bundle, so each adapter serializes it on the way out. The visible body is always `briefing.md`. The AI concepts ride along: inline on GitHub (no attach API), attached as a tarball elsewhere.

### GitHub , briefing as the body, concepts in a `<details>`
1. **Visible body = `briefing.md`** (its markdown body; the frontmatter is not shown). A human editing it edits the source.
2. **AI concepts** go inside one collapsible block:
   ```
   <details>
   <summary>AI context (OKF bundle, okf_version 0.1)</summary>

   <!-- okf:concept path="story.md" type="Story" -->
   ...the concept's frontmatter + body...

   <!-- okf:concept path="discovery.md" type="Reference" -->
   ...

   </details>
   ```
   The `<!-- okf:concept ... -->` comments are lightweight boundary + type hints for the next agent; they are not a parser contract. Byte-exact reconstruction is not required, comprehension is.
3. **Overflow.** If the body would exceed ~60KB (safety margin under GitHub's 65,536-char limit), keep the briefing + as many concepts as fit in the body, and put the remaining concepts in follow-up issue **comments**, each comment opening with the same `<!-- okf:concept ... -->` line.

### Jira , briefing as ADF + attach the tarball
- Body = `briefing.md` converted markdown -> ADF (Jira Cloud stores ADF, not markdown).
- Attach `<slug>.okf.tgz` (tar+gzip of the bundle directory) via the Jira attachment API. The body is never empty; the full context is the attachment.

### Azure DevOps , briefing as HTML + attach the tarball
- Body = `briefing.md` converted markdown -> HTML (work-item large-text fields are HTML by default).
- Attach `<slug>.okf.tgz` via the ADO attachment API.

## Reading the bundle back (what plan/implement do on a ticket)
The tracker is the store, so each command rebuilds the bundle from the ticket, then works the local copy under `~/.openadlc/runs/<workspace>/<run-id>/`.
- **GitHub:** read the issue body + comments; reconstruct `briefing.md` from the body and each concept from its `<!-- okf:concept path=... -->` section. This is LLM-native reading, no parser.
- **Jira / ADO:** download the `<slug>.okf.tgz` attachment and untar it into the run workspace (byte-exact).

## Source of truth and human edits
The **OKF bundle is canonical**; the visible briefing is a live view of `briefing.md`. On re-entry a command rebuilds from the ticket. If a human edited the visible GitHub briefing, fold their edit back into `briefing.md` and note it; never silently discard a human's words.

## Conformance
A bundle is OKF-conformant when every non-reserved `.md` has parseable frontmatter with a non-empty `type`, and `index.md`/`log.md` follow the reserved-file shape. The em-dash ban applies to every file in the bundle.

---

Author: OpenADLC core. Freshness: written for OKF v0.1 (Google knowledge-catalog) and the GitHub/Jira/ADO trackers. Consumption is LLM-native by design (no custom parser); GitHub still has no issue-attachment API, so the bundle is inline there. Re-verify the Jira ADF conversion and the ADO HTML conversion against the live trackers before relying on them.
