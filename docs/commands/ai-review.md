<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
# /ai-review

Independent, fresh-eyes review. It runs **embedded** inside [`/ai-implement`](ai-implement.md) (the review checkpoint that never skips) and **standalone** on any code.

| | |
|---|---|
| **Takes** | a diff, branch, PR (URL/#number), or path |
| **Produces** | a BLOCK or APPROVE verdict with `path:line` evidence |
| **Checkpoint** | post the verdict (only if you ask) |

Fetching, reading, and analyzing are local and need no approval. Posting anything back (PR comments, a verdict) is outbound and stops for your explicit yes.

## How to run

```text
/ai-review <a diff, branch, PR (URL/#number), or path>
```

Inside `/ai-implement`, an empty target means the change that was just built.

## The review types (pick one or more)

- **Code** (recommended default): correctness, logic, whether the tests actually assert anything, fit with the codebase conventions.
- **Security:** when the change touches auth, crypto, network, secrets, or a public surface.
- **Compliance:** when it touches PII, consent, retention, or a regulated flow. For UI, compliance also means design fidelity (did the build match the approved design).
- **Adversarial lenses:** one or more fresh-eyes passes (a pentest mindset, a test critic, a perspective-diverse pass).
- **Design / UI fidelity:** compares the rendered screens against the plan's Figma baseline; loaded on demand, only for UI work.
- **None:** not recommended; only for genuinely trivial changes.

## What it does

1. **Resolves the target** read-only; when embedded in a run, selects the plan by run-id.
2. **Loads each touched repo's review contract** (`CLAUDE.md` plus the touched rules).
3. **Dispatches the picked reviews concurrently** to fresh-context agents (`pr-reviewer` for the merge verdict, the domain reviewer, `security-reviewer`, `test-critic`, `design-critic` for UI), then drops low-signal findings.
4. **Persists the verdict, every run,** to `~/.openadlc/runs/<workspace>/<run-id>/review-<lens>-<timestamp>.md`, BLOCK or APPROVE, before any consent prompt. See [concepts: run isolation](../concepts/run-isolation.md).
5. **Prints the report,** then **stops and asks** before posting.

A visual or behavioral criterion is "met" only with real-run, saved evidence; a "looks right" claim with no saved artifact is a finding, not an approval, and the verdict is BLOCK.

## The checkpoint

Persisting the verdict is local and always happens. **Posting** the review back to the PR (and any tracker item it drives) is the only outbound step, and it waits for your explicit yes. Reviewing is not approving anything to leave the machine.

## Source

- Command: [plugins/adlc-core/commands/ai-review.md](../../plugins/adlc-core/commands/ai-review.md)
- Skill: [plugins/adlc-core/skills/ai-review/SKILL.md](../../plugins/adlc-core/skills/ai-review/SKILL.md)
