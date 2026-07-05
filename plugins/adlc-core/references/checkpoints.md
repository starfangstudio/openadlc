<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
# Checkpoint files (ADLC)

Every consent checkpoint (per [loop-control.md](loop-control.md)) writes a record of the ask to disk before it asks the operator. This is the one durable, machine-readable trace of "what would leave this machine, and what was decided", so a terminal, a teammate, or an external surface can all see the same state. Loaded by intake, plan, implement, and review wherever they hit a consent checkpoint.

## Why a file
The terminal prompt is ephemeral: close the window and the ask is gone. A checkpoint file makes the ask durable and gives any consumer (a dashboard, a notifier, a second terminal) something to read. **The free product needs none of this**: if nothing ever reads these files, the terminal ask still works exactly as it does today. The file is a byproduct of the ask, never a dependency of it.

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
resolved_by: terminal            # set only on resolution
resolved_at: <UTC ISO 8601>       # set only on resolution
reason: "<one line>"              # optional, deny only
summary: "<one line: what would go out>"
---
```
The **body** is exactly what would leave the machine: for `push`, the branch, commit list, and per-file diffstat; for the `post-*` types, the title plus the full body as it would be posted. This mirrors the consent prompt shown in the terminal; it is not a summary of it.

## Writes are atomic
Every write (create, resolve) goes through write-temp-then-rename in the same directory: write the full file to a temp path, then rename it over the target. A reader never observes a half-written file.

## Status transitions
`pending -> approved` or `pending -> denied`, exactly once. A resolved file is never edited again. The agent that owns the checkpoint is the one that transitions it, from the operator's answer at its terminal. No other actor writes the status.

## Heartbeat while pending
While the agent awaits the operator's answer, it touches a separate file, mtime-only, every ~30 seconds:
```
checkpoints/<seq>-<type>.heartbeat
```
A separate file keeps liveness touches from ever colliding with a resolution write on the same path. Consumers treat **3 missed touches (no mtime change for >90s)** as stale: the session may no longer be polling, so a resolution recorded now has no guaranteed effect until the session reads it again.

## Resolution is terminal-only; external surfaces observe
The operator answers in ONE place: the agent's terminal prompt, the ask as it works today. The agent writes the resolution (`status: approved | denied`, plus `resolved_at` and an optional `reason`) into the checkpoint file via the atomic write above, and is the sole writer of the acted-on state.

A cockpit or any other observer is strictly read-only. It reads the pending checkpoint file to surface the ask elsewhere (a notification, a dashboard row). There is no path for an observer to close a checkpoint, no server endpoint, and no second write channel; resolution is machine-local, at the terminal.

These files are local and same-user: anything running as the user can read or write them. Safety does not rest on the file being unwritable; the agent is the sole writer of the acted-on state, resolves only from its terminal, and ignores any status it did not write. State this honestly to any consumer: an observer has no authority, and the checkpoint files are never an enforcement boundary.

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
