<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
# Packs

A **pack** is the portable unit of agentic guidance: a versioned bundle of skills, agents, references (and, for the core, commands), plus its evals and a capability declaration. Packs are how the lifecycle and the golden paths travel between teams and tools.

## The spine and the domain packs

- **`adlc-core` is always on.** It is the spine: the four `/ai-*` commands and the lifecycle checkpoints, plus software design, codebase research, decision records, docs, and commit linking.
- **Domain packs load on demand.** The domain pack loads by detected domain (web, backend, iOS, Android, Unity, desktop, database, and so on). A cross-cutting pack (security, privacy, AI, planning, testing, quality-gates, ops, monetization) loads when the work calls for it. `adlc-design` loads **only** when the work touches Figma or a design surface, never otherwise.

One lifecycle, any domain: the spine is identical whether the work is web, backend, iOS, or Unity. Only the domain pack changes.

## The units

- **Skill** (`skills/<name>/SKILL.md`): the primary unit, how to do a task. A trigger-rich description, numbered steps, a References section, and a failable check. It loads when its description matches the work.
- **Agent** (`agents/<name>.md`): a read-only subagent, an architect or a reviewer.
- **Reference** (`references/<name>.md`): the deep detail a skill points to, kept out of the skill body (progressive disclosure). Cited by name, never with an agentic-coding-tool-specific path variable.
- **Command** (`commands/<name>.md`): the entry points native to each agentic coding tool (the `/ai-*` commands), mapped per tool by APM. Not a portable unit.
- **Rule:** future work. Conventions ship as references today.

## Loading and installing

APM deploys packs to your agentic coding tool. The spine comes with the install:

```bash
apm install starfangstudio/openadlc
```

Domain packs install on demand from the same marketplace:

```bash
apm install adlc-web@openadlc
```

You can also load or disable packs from [config](../config/) (`packs.enabled` / `packs.disabled`).

## The two tiers

- **Community:** valid and useful, passes the machine floor, not held to the full certified bar. Most contributions start here.
- **Certified:** a golden-path domain the project stands behind and keeps current. Full conformance plus a maintainer review, and a reachable owner.

## Conformance

A conformant pack has a manifest (name, version, description, owner, targeted ADLC version, and a capability declaration), at least one guidance unit, evals, and a truthful capability declaration, and it does not weaken the human-in-the-loop checkpoints or take undeclared capabilities. The standard defines the shape; the adapter maps it onto a specific agentic coding tool. See [the spec, section 5](../../standard/spec.md).

## Source

- [pack-format](../pack-format.md) (the wire format and unit rules), [customize: add your own pack](../customize/own-pack.md), [the spec, section 5](../../standard/spec.md).
