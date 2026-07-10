<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
# Add your own skill

A skill is the portable, primary unit of guidance: how to do one task. It loads automatically when its description matches the work.

## Where it goes

```
plugins/<pack>/skills/<name>/SKILL.md
```

The skill `name` in the frontmatter **must match its directory name** (a hard fail otherwise).

## The shape

```markdown
---
name: my-skill
description: "This skill should be used when the user asks to '...' or '...'. <what it produces>."
version: 0.1.0
---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# My skill

<one-line purpose>

## Steps

1. ...
2. ...

## References

- [references/<name>.md](references/<name>.md): <the deep detail this skill cites>

## Verify

<the failable check: the thing that passes or fails to prove the skill worked>
```

What the format asks for:

- **A trigger-rich, third-person `description`.** Write it as "This skill should be used when ..." with the phrases a user would actually say. This is what makes the skill load at the right time.
- **Numbered steps.** The procedure, in order.
- **A References section.** Deep detail lives in `references/<name>.md`, one hop away, so the skill body stays short (progressive disclosure).
- **A failable check.** State how the work is proven done. Evidence over assertion.

## The rules the checker enforces

Run [`tools/check-packs.py`](../../tools/check-packs.py) against your pack. Hard fails (these block):

- An em-dash anywhere (literal or escaped). Use commas, colons, or parentheses.
- An agentic-coding-tool-specific path variable (`${CLAUDE_PLUGIN_ROOT}`) in any prose. It resolves on only one deploy target, so cite references **by name** instead: same-pack as `[references/<name>.md](references/<name>.md)`, another pack's named in prose.
- Missing or invalid frontmatter, a missing `name` or `description`, or a `name` that does not match the directory.

Soft warnings (allowed, but worth fixing): no `version`, no References section, no failable check mentioned, or a skill over 260 lines.

## Verify

```bash
python3 tools/check-packs.py <pack>
```

Green means the skill clears the structural bar. See [pack-format](../pack-format.md) for the full unit rules and [concepts: packs](../concepts/packs.md) for how packs load.
