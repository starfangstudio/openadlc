<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
# Checkpoint files (ADLC)

Every consent checkpoint (per [loop-control.md](loop-control.md)) writes a record of the ask to disk before it asks the operator. This is the one durable, machine-readable trace of "what would leave this machine, and what was decided", so a terminal, a teammate, or an external surface can all see the same state. Loaded by intake, plan, implement, and review wherever they hit a consent checkpoint.

## Why a file
The terminal prompt is ephemeral: close the window and the ask is gone. A checkpoint file makes the ask durable and gives any consumer (a dashboard, a notifier, a second terminal) something to read and, optionally, resolve. **The free product needs none of this**: if nothing ever reads these files, the terminal ask still works exactly as it does today. The file is a byproduct of the ask, never a dependency of it.

## Where it lives
At every consent checkpoint, write:
```
~/.openadlc/runs/<workspace>/<run-id>/checkpoints/<seq>-<type>.md
```
`<seq>` is a zero-padded or plain integer, monotonic per run (1, 2, 3, ...). `<type>` is one of `post-issue`, `post-subissue`, `push`, `post-review`, matching the outbound action the checkpoint gates.

## Frontmatter
```yaml
---
id: <run-id>/<seq>            # unique within the run
seq: 3                        # integer, monotonic per run
type: post-issue | post-subissue | push | post-review
created: 2026-07-02T14:03:11Z # UTC ISO 8601
status: pending | approved | denied
resolved_by: terminal | cockpit   # set only on resolution
resolved_at: <UTC ISO 8601>       # set only on resolution
reason: "<one line>"              # optional, deny only
summary: "<one line: what would go out>"
---
```
The **body** is exactly what would leave the machine: for `push`, the branch, commit list, and per-file diffstat; for the `post-*` types, the title plus the full body as it would be posted. This mirrors the consent prompt shown in the terminal; it is not a summary of it.

## Writes are atomic
Every write (create, resolve) goes through write-temp-then-rename in the same directory: write the full file to a temp path, then rename it over the target. A reader never observes a half-written file.

## Status transitions
`pending -> approved` or `pending -> denied`, exactly once. A resolved file is never edited again. The agent that owns the checkpoint is the one that transitions it; a resolution written by any other actor is advisory input, not a direct state change (see Dual-channel resolution below).

## Heartbeat while pending
While the agent awaits the operator's answer, it touches a separate file, mtime-only, every ~30 seconds:
```
checkpoints/<seq>-<type>.heartbeat
```
A separate file keeps liveness touches from ever colliding with a resolution write on the same path. Consumers treat **3 missed touches (no mtime change for >90s)** as stale: the session may no longer be polling, so a resolution recorded now has no guaranteed effect until the session reads it again.

## Dual-channel resolution, agent-authoritative
The operator may answer in two places:
1. **The terminal**, the ask as it works today.
2. **An external surface** (e.g. a cockpit), which writes `status: approved | denied` (plus `resolved_by`, `resolved_at`, optional `reason`) into the checkpoint file via the same atomic write.

Both channels are live at once; the agent is the sole authority on which one wins:
- The agent polls the checkpoint file at a bounded interval while it also waits on terminal input.
- **First resolution observed wins.** Whichever answer the agent reads first, it acts on that one and records `resolved_by` accordingly.
- **A terminal answer at the agent's own prompt overrides a simultaneous file write.** If the operator answers in the terminal while an external write is in flight, the terminal answer is authoritative; the agent rewrites the file to match the answer it acted on.
- A resolution written to the file by an external surface is advisory input TO the agent, not a fact until the agent reads and acts on it. The agent is the only writer of the final, acted-on state.

This is a same-user convenience channel, not a security boundary: anything running as the user can write these files. State this honestly to any consumer; never claim enforcement.

## Run terminal-state marker
A run's `index.md` frontmatter (per [okf.md](okf.md)) carries:
```yaml
status: active | done | abandoned
```
Set to `active` when the run starts, and to `done` or `abandoned` when the run ends. This is the one durable signal that a run has finished, so a consumer never has to guess from the presence or absence of other artifacts.

## Seams (doc-level, no hooks)
No hooks exist in ADLC and none are designed. An overlay pack that wants to observe or extend the lifecycle hooks these four points by reading the same files this contract already writes, never by injecting code:
- **discovery-start**: the moment a run workspace is created (intake's first write). An overlay reads the new `index.md` to notice a run began.
- **pre-checkpoint**: the moment a checkpoint file is written, before the agent asks the operator. An overlay reads `checkpoints/<seq>-<type>.md` at `status: pending` to surface the ask elsewhere.
- **review lens menu**: the moment `/ai-implement` or `/ai-review` offers the review-type menu. An overlay observes the persisted `review-<lens>-*.md` files (per [run-isolation.md](run-isolation.md)) once written.
- **pre-push + post-run**: the `push` checkpoint file (pre-push) and the `index.md` status transition to `done`/`abandoned` (post-run). An overlay reads both to know a run shipped or ended.

These are stable read points, not an API: every seam is a file this contract writes anyway. An overlay pack never adds a hook, never blocks a write, and never changes checkpoint semantics; it only reads.

---

Author: OpenADLC core. Freshness: written for the checkpoint-file contract v1 (2026-07-02), covering the four consent-checkpoint types shipped in adlc-core 0.6.0. Re-verify the type enum against the four commands before extending it; a new consent checkpoint needs a new `type` value here first.
