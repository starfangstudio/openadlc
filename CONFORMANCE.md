<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
# Conformance

OpenADLC is both a tool and a small open specification: the lifecycle, the command contract, the human checkpoints, and the pack format. "Conformant" means an implementation or a pack meets the requirements for a level. Levels are cumulative.

> Status: draft. The spec and the conformance suite are being built alongside the core. Items marked (planned) are not enforced yet.

## Levels

### Core

The baseline. A conformant Core implementation:

- exposes the four commands: `/ai-discovery`, `/ai-plan`, `/ai-implement`, `/ai-review`;
- stops at the lifecycle checkpoints before anything leaves the machine: the commands present what would go out and require an explicit human yes at each outbound boundary, with no separate ship step (outbound is a human decision, per Principle #2);
- never stops reading or local work: only the outbound boundary asks for approval, and the approval is recorded so the consent decision is auditable;
- ships packs as Agent Skills (`SKILL.md`) that install and function as plain files, with or without a package manager.

### Governed

Core, plus central policy:

- managed configuration a project cannot loosen (the checkpoints);
- a tamper-evident audit trail of human decisions and approved outbound actions (planned);
- the checkpoints enforceable across a fleet via managed settings (planned).

### Certified

Governed, plus currency and provenance:

- packs carry contamination-resistant evals and pass them;
- content is kept current against a published cadence;
- a per-task provenance record for what fed a task (planned).

## Conforming a pack

A pack conforms to Core when it:

- is a valid Agent Skill (`SKILL.md` with at least a name and description);
- carries a conformant manifest with `owner`, `adlc`, `units`, `evals`, and `capabilities`;
- installs and functions as plain files, with or without a package manager;
- ships at least one eval, and the suite is green;
- declares its license: the OpenADLC source-available license (see the `LICENSE` file) for implementation, CC-BY-4.0 for any `standard/` content it carries.

## Checking conformance

`openadlc doctor` (planned) verifies the level of an install. The conformance suite is the source of truth. The "OpenADLC Verified" badge is earned by passing it, never self-asserted.
