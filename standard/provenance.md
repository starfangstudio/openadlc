<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# OpenADLC Provenance (git-trailer)

> Status: draft proposal, pre-ratification. For spec version 0.1.
> One line: how OpenADLC records which lifecycle phases ran, on what, in what order, as hash-linked git trailers on commits and pull requests, and how a reader verifies them at view time without any server or gate.

Provenance answers one question about a change: **did it actually move through the lifecycle, in order, on the artifacts it claims?** OpenADLC records the answer as a small hash-linked trailer on each commit and on the pull request, written by the four `/ai-*` commands ([`/ai-discovery`](../plugins/adlc-core/commands/ai-discovery.md), [`/ai-plan`](../plugins/adlc-core/commands/ai-plan.md), [`/ai-implement`](../plugins/adlc-core/commands/ai-implement.md), [`/ai-review`](../plugins/adlc-core/commands/ai-review.md)) as they run. A reader (the OpenADLC CLI, or the dashboard) verifies it **at view time**: it recomputes the chain from the git history and the pull request body and shows a verdict. There is no server, no stored verdict, and, deliberately, **no check-run** (see [Decision D6](#decisions)).

This is the git-trailer provenance for the lifecycle. It is **not** the per-seat cryptographic audit hash chain (a separate backend concern that gives non-repudiation across an org). These trailers give legibility and tamper-evidence on a single change; they do not claim identity or non-repudiation. That honest limit is stated where it matters below.

Cross-links: verification consumes the host adapter's `readTrailers` (the host adapter spec, authored in parallel); the run, branch, and artifact locations are defined in the adlc-core [run-isolation.md](../plugins/adlc-core/references/run-isolation.md) reference; the lifecycle phases and the consent checkpoint are [spec.md](spec.md) sections 2 and 4.

---

## 1. What provenance is

Each lifecycle phase, when it runs, produces one **provenance record**: a single line naming the phase, the run, a hash of the phase's artifact, and a hash-link to the prior phase. The records for a change form a chain: discovery, then plan, then implement, then review, in canonical order, including only the phases that ran. Because each record's identity is a hash of its own fields plus the prior record's identity, editing or dropping any earlier record breaks every later link. That is the tamper-evidence.

Two homes carry the records:

- **Commit trailers.** Only `/ai-implement` writes code, so only the implement record is born as a native git trailer, on the commit(s) it makes.
- **The pull request description.** All present records are embedded in a fenced block in the pull request body. This is what survives a squash or rebase (which discards commit messages), and it is what `readTrailers` reads.

Verification is a pure function of these two sources plus the local git tree. Nothing is trusted server-side, because nothing is stored server-side.

---

## 2. The trailer format

A provenance record is a git trailer: one `Key: value` line in a message footer. One key, repeated once per phase.

**Key:** `OpenADLC-Provenance`

**Value:** a single line of `field=value` pairs in fixed order, joined by `"; "` (semicolon then one space):

```
OpenADLC-Provenance: v=1; phase=<phase>; run=<run-id>; art=<algo>:<value>; prev=<id|none>; by=<seat>; at=<utc>; id=sha256:<hex>
```

| Field | Meaning | Grammar |
|---|---|---|
| `v` | Format version. This spec is `v=1`. | `1` |
| `phase` | Which lifecycle phase this record is for. | `discovery` \| `plan` \| `implement` \| `review` |
| `run` | The run-id from [run-isolation.md](../plugins/adlc-core/references/run-isolation.md) (`<slug>-<UTC-timestamp>`). | e.g. `add-login-20260628T141233Z` |
| `art` | A typed hash of this phase's canonical artifact (table below). | `sha256:<64-hex>` or `tree:<full-oid>` |
| `prev` | The `id` of the immediately prior **present** phase's record, forming the chain. `none` for the first present phase (Section 5). | `sha256:<64-hex>` \| `none` |
| `by` | The seat that ran the phase, as a self-asserted string (an email or handle). An **unverified claim** (Decision D8). | free ASCII, no `;` |
| `at` | When the phase ran, UTC ISO-8601, `Z` suffix, second precision, no fractional seconds. | `YYYY-MM-DDTHH:MM:SSZ`, e.g. `2026-07-05T14:03:11Z` |
| `id` | The hash-link handle: `sha256` of this record's own canonical bytes. | `sha256:<64-hex>` |

**Field-value grammar (pinned, so two stampers agree byte-for-byte).**

- Each pair is `field=value` with **no space around the `=`**, and a pair splits on its **first** `=` (no value begins with `=`), so a value that itself contains `=` is still unambiguous.
- Pairs are separated by exactly `"; "` (a semicolon and one space). No leading or trailing separator.
- **No field value may contain the separator sequence `"; "` or a bare `;`**, so a parser splits on `"; "` unambiguously. `by` is free ASCII with the single restriction that it carries no `;`.
- The value of the trailer is everything after the first `": "` that follows the key on the trailer line, taken verbatim (no whitespace trimming beyond stripping that one `": "`).

### The hash-link scheme (exact, so a verifier is deterministic)

The record's **canonical bytes** are the value string with fields `v; phase; run; art; prev; by; at` in that order, `"; "`-joined, encoded as **UTF-8** (every field this spec defines is US-ASCII), **with the `id` field omitted** and no surrounding whitespace. Then:

```
id = "sha256:" + lowercase_hex( sha256( canonical_bytes ) )
```

The full trailer value is `canonical_bytes + "; id=" + id`. A verifier recomputes `id` from the first seven fields and compares (check PROV-4). The next present phase sets its `prev` to this record's `id` (check PROV-5). That is the whole chain: `id` binds a record to its own content and to the prior record's `id` through `prev`.

`id` is derivable, so storing it is belt and suspenders. It earns its bytes by making a broken chain legible to a human reading the raw trailer and by letting a verifier report "`prev` points at X but no present record hashes to X" without recomputing everything.

### Golden test vector (reproducible)

One fully-computable discovery record, so an implementer can check a hasher against known bytes. The discovery artifact for this vector is a one-file OKF bundle whose exact content is the string `okf-bundle-example` plus a trailing newline (19 bytes total).

```
art canonical bytes : okf-bundle-example\n              (19 bytes)
art                 : sha256:dad61c558dee3fee3d4125e36f2238a17246a96e9c48daaa595e8d27e129e4bc

canonical_bytes (186 bytes, no trailing newline):
v=1; phase=discovery; run=add-login-20260628T141233Z; art=sha256:dad61c558dee3fee3d4125e36f2238a17246a96e9c48daaa595e8d27e129e4bc; prev=none; by=jane@example.com; at=2026-06-28T14:12:40Z

id                  : sha256:4cdc5ce6e1f5cbcd1c20ce35d22ea87873c3853fea87dc6cc9b0239d4c29a62b
```

Reproduce it: `printf 'okf-bundle-example\n' | shasum -a 256` yields the `art` hex; `printf '%s' '<the 186-byte canonical_bytes above>' | shasum -a 256` yields the `id` hex. The full trailer value is those `canonical_bytes` with `; id=sha256:4cdc5ce6...` appended.

### The canonical artifact per phase (what `art` hashes)

`art` is typed as `<algo>:<value>` so it is self-describing and each phase uses the cheapest thing a verifier can reproduce:

| Phase | Canonical artifact | `art` form |
|---|---|---|
| `discovery` | The intake-fuel OKF bundle (`briefing.md` + typed concepts) as written to the run workspace. | `sha256:` of the bundle's canonical bytes |
| `plan` | The plan OKF bundle (`spec.md` / `Plans.md` + contracts). | `sha256:` of the bundle's canonical bytes |
| `implement` | The **tip tree** of the run branch: the final content of the change. | `tree:<full-oid>` of `<tip>^{tree}` |
| `review` | The review report OKF (`review-<lens>-*.md` + `review-payload.json`). | `sha256:` of the report's canonical bytes |

**`tree:<full-oid>` is the complete git object id, never a shortened prefix.** It is 40 lowercase hex on a SHA-1 repository (for example `af5c9d3f21b8e0c7a4d5e6f7089a1b2c3d4e5f60`) and 64 lowercase hex on a SHA-256 repository. PROV-6 requires **exact equality** with `git rev-parse <tip>^{tree}`, so a prefix would never match.

The implement artifact is the git **tree object id**, not a diff and not a commit id, on purpose (Decision D4): a tree id survives a squash or a clean rebase (both preserve the final tree), it is reproducible from git alone with `git rev-parse <tip>^{tree}`, and it needs no run workspace. That is what lets the dashboard verify the implement record's integrity with nothing but the pull request and the repository.

**Canonicalizing an OKF bundle (pinned, so the stamper and the verifier hash identical bytes).** The `sha256:` of a discovery, plan, or review bundle is `sha256` over these exact bytes:

1. **File set.** Exactly the files [okf.md](../plugins/adlc-core/references/okf.md) defines as that phase's bundle (the `briefing.md` / `spec.md` / report plus the typed-concept files). The ephemeral `provenance.jsonl` and any run-local scratch are **excluded**.
2. **Order.** Files are sorted by their bundle-relative path, comparing the **raw UTF-8 bytes of the path** ascending (byte-wise, case-sensitive, not locale-aware).
3. **Line endings.** Inside each file, every `CRLF` and every lone `CR` is normalized to a single `LF` before hashing, so a platform's line endings never change the hash. No other transformation is applied; there is no Unicode normalization.
4. **Concatenation.** The (normalized) files are concatenated with a single `LF` (`\n`) byte **between** consecutive files, and **no separator before the first or after the last** file. Each file's own trailing newline, if any, is part of its bytes.

The command that stamps a record and the verifier that checks it MUST apply this identical rule; any deviation changes the hash. This spec fixes it here.

### Per-commit vs pull-request level

| Record | On a commit? | In the pull request body? | Written by |
|---|---|---|---|
| discovery | no (no code) | yes | assembled by `/ai-implement`, then `/ai-review` |
| plan | no (no code) | yes | assembled by `/ai-implement`, then `/ai-review` |
| implement | **yes** (on the commit(s)) | yes | `/ai-implement` |
| review | no (no code) | yes | `/ai-review` |

Discovery and plan never touch git, so their records live in the run workspace (a `provenance.jsonl` next to the OKF bundle, local only) until a git-writing command serializes the full chain. The commit trailer is the implement record's native home; the pull request body is the home for all present records. A record that appears in both places is one record, deduplicated by `id` by the verifier (Section 5).

---

## 3. How each `/ai-*` command writes provenance

Each command produces its phase's record when the phase completes, and appends it to the run's local `provenance.jsonl`. The two git-writing commands then materialize the chain. Nothing here is an outward action until the existing consent checkpoint fires for the push or the pull-request write.

| Command | Phase | Produces the record from | Materializes to git |
|---|---|---|---|
| `/ai-discovery` | discovery | the intake-fuel bundle it posts; `prev=none` | none (local only) |
| `/ai-plan` | plan | the plan bundle it posts; `prev` = the discovery record's `id` | none (local only) |
| `/ai-implement` | implement | the tip tree of the change; `prev` = the prior present record's `id` | **stamps the implement trailer on its commit(s)**, and at the push / pull-request checkpoint **writes the fenced provenance block** into the pull request body with every record present so far |
| `/ai-review` | review | the review report; `prev` = the implement record's `id` | at the pull-request write, **rewrites the fenced block** to append the review record |

Rules:

- The record for a phase MUST be stamped from that phase's real artifact, at that phase's completion. A command MUST NOT fabricate a record for a phase it did not run: a collapsed or skipped phase simply has no record (Section 5 handles partial coverage honestly, and the first present phase carries `prev=none`).
- `/ai-implement` MUST put the implement record on the tip commit at minimum, so that a non-squashed history carries provenance natively on the commit that introduced the change.
- Writing or updating the pull request body is an outward action. It passes the consent checkpoint ([spec.md](spec.md) section 4) exactly like any other pull-request write; provenance adds no new outward action and no new gate.
- **Re-running a phase re-stamps every later present phase.** A record's `id` hashes its `art` and `at`, so re-running an earlier phase (a second `/ai-implement`, say) yields a new `id`, which dangles the `prev` of every phase after it. A command that re-runs a phase MUST therefore regenerate the chain forward from that phase: re-stamp the re-run phase, then re-stamp each later present phase so its `prev` points at the new `id`. Re-serializing the fenced block is idempotent (Section 4); it never appends a duplicate.
- **The fenced block in the pull request body is the durable carrier; `provenance.jsonl` is a local convenience.** A command that must rewrite the block reads its prior records from `provenance.jsonl` when it is present, and **falls back to the existing fenced block in the pull request body** when it is not (a fresh checkout, or `/ai-review` running where `/ai-implement`'s workspace is gone). It never silently drops earlier records because a local file is missing.

---

## 4. The pull-request-description embedding (squash / rebase survival)

The pull request body carries the records in an HTML-comment-fenced block. HTML comments are invisible in rendered markdown, survive copy and edit, and give `readTrailers` an unambiguous region to find. Inside the fence, each line is a provenance trailer in the **exact same format** as a commit trailer, so one parser serves both homes.

```
<!-- openadlc-provenance v1 -->
OpenADLC-Provenance: v=1; phase=discovery; run=add-login-20260628T141233Z; art=sha256:9b1f...; prev=none; by=jane@example.com; at=2026-06-28T14:12:40Z; id=sha256:4d2a...
OpenADLC-Provenance: v=1; phase=plan; run=add-login-20260628T141233Z; art=sha256:7c08...; prev=sha256:4d2a...; by=jane@example.com; at=2026-06-28T15:01:22Z; id=sha256:be71...
OpenADLC-Provenance: v=1; phase=implement; run=add-login-20260628T141233Z; art=tree:af5c9d3f...; prev=sha256:be71...; by=jane@example.com; at=2026-07-05T14:03:11Z; id=sha256:77de...
OpenADLC-Provenance: v=1; phase=review; run=add-login-20260628T141233Z; art=sha256:1e6b...; prev=sha256:77de...; by=asha@example.com; at=2026-07-05T16:20:05Z; id=sha256:c40f...
<!-- end openadlc-provenance -->
```

(Hashes and tree oids are truncated with `...` for readability; a real record carries the full-length value, per Section 2.)

Rules the block MUST follow:

- The fence markers are matched **byte-for-byte**: the opening `<!-- openadlc-provenance v1 -->` and the closing `<!-- end openadlc-provenance -->`. The region is exactly the lines between them, inclusive of neither marker.
- Every record line inside the region begins with `OpenADLC-Provenance: ` and is parsed identically to a commit trailer.
- The block is written **once** and replaced as a whole (idempotent): a command regenerating provenance replaces the entire fenced region, never appending a second block. If two blocks are ever found, that is a fail the verifier reports (check PROV-3).
- Records appear in canonical phase order (discovery, plan, implement, review), including only the phases that ran. Order is a convenience for a human reader; the verifier does not trust it, it reconstructs the chain from the `prev` links (Section 5).

### The seam with `readTrailers` (who does what)

The host adapter's `readTrailers` and this spec's **verifier** split the work cleanly, and the split is the contract both specs are held to.

**`readTrailers` is a dumb, complete extractor.** Its full signature and return shape are fixed in the host adapter spec; what it MUST guarantee for provenance is:

1. It returns **every** syntactic git trailer it finds, from two sources, each record tagged with its `source` (`commit` or `description`). Although `readTrailers` accepts an optional `keys` restriction (the host adapter spec), the verifier calls it **without** `keys`, so it receives every record; filtering to the `OpenADLC-Provenance` key, deduping, and phase-ordering are the verifier's job, never this method's (it never parses the provenance value).
2. **Commit source:** the pull request's own commits, the `base..head` range (the commits the pull request adds, where `base` is the merge-base of `head` and the target branch), never the source branch's full ancestry. Commit footers are parsed with git-trailer grammar, and the trailer **value is returned byte-for-byte** with no trimming, folding, or continuation-line joining, so the verifier can recompute `id` over the exact bytes.
3. **Description source:** the trailers inside the provenance fence above, the markers matched byte-for-byte, one `OpenADLC-Provenance:` line per record.
4. It returns records in **source order** (commit order within `base..head`, then description-fence line order). The verifier does not depend on this for correctness; it links by `prev`.
5. When the description contains **more than one** fenced block, `readTrailers` returns the description trailers from all of them tagged `source: description`; it does not itself flag the duplication. Counting the fenced blocks (PROV-3) is the verifier's job, done by parsing the body (below).

**The verifier is the smart consumer.** Over the records `readTrailers` returns, the verifier: filters to the `OpenADLC-Provenance` key; splits each value into its fields; **dedupes by `id`** (a record present both on a commit and in the body is one record); resolves the chain by `prev` links (Section 5); and, from the pull request body it also holds, checks that the body carries exactly one fenced block (PROV-3). Deduping and ordering live in the verifier, never in `readTrailers`, which is what lets the provenance vocabulary evolve without touching the adapter seam.

**Dedup tie-break.** Dedup keys on each record's **recomputed content hash**, and per-raw-record self-consistency (Section 5, check 2) runs **before** dedup, so a record whose stored `id=` was altered cannot mask itself by deduping away. Two records with the same recomputed hash are byte-identical: keep one. Two records that name the **same phase** but hash differently are not a dedup case; they are a chain anomaly (a phase claimed twice), and the verifier reports it (`tampered`, Section 5). After dedup there is at most one record per phase.

**The `<tip>` for PROV-6** is the head commit of the change under view (the pull request's `headSha`); the implement record's `tree:<oid>` is compared against `git rev-parse <headSha>^{tree}`.

After a squash, the commit source is empty and the body is the sole carrier; before a squash, both agree and dedupe to the same set. **The body-side records are what remain when the commits are gone.** The two specs MUST agree on the fence markers and the trailer grammar; if either changes, both change in lockstep.

---

## 5. View-time verification (CLI and dashboard)

Verification is a read. It recomputes the chain from the records `readTrailers` returns plus the local git tree, and reports a verdict. It runs in two surfaces, the same computation in both:

- **CLI:** `openadlc verify [<pr>|<branch>]` reads the local git history and, when available, the pull request body (via the host adapter, e.g. `gh pr view --json body`). No network write, no backend. It prints the verdict.
- **Dashboard:** renders the verdict at view time by calling the host adapter's `readTrailers` (or a read model built from it, which also carries the body for the block-count check) and running the identical check. There is **no verdict stored anywhere**: the dashboard recomputes on every view, so there is nothing server-side to trust or to fall stale (Decision D7).

### The checks, in order

1. **Parse.** Every `OpenADLC-Provenance` line is well-formed: known `v`, known `phase`, all required fields present, `art` and `id` typed correctly, the field-value grammar of Section 2 respected, and **the `art` type matches the phase** (`implement` MUST be `tree:`, every other phase MUST be `sha256:`). A present `OpenADLC-Provenance:` line that is a valid git trailer but an invalid provenance value (unknown `v`, a missing field, a malformed `art` or `id`, or an `art` type that does not match its phase) fails this check and the verdict is `tampered`, naming the line.
2. **Self-consistency, then dedup.** For **each raw record** (before any deduplication), recompute `id` from its canonical bytes and compare (Section 2); a mismatch means the record was edited in place and the verdict is `tampered`. Only then dedupe, keying on the **recomputed content hash** (not the stored `id` field), so a record whose stored `id=` was altered to collide with another is caught by this per-raw-record check before it could dedupe away. After dedup there is at most one record per phase.
3. **Chain (pure `prev`-link resolution).** Build a map from `id` to record. Exactly one present record has `prev=none`; it is the **root**, and its phase MUST be the earliest present phase in canonical order (`discovery` < `plan` < `implement` < `review`). Every other record's `prev` MUST resolve to the `id` of another present record. Following `prev` from every non-root record MUST reach the root with no cycle and no dangling link, forming a single chain, and the phases along that chain MUST be strictly increasing in canonical order (no repeat, none out of place). This is what lets a collapsed chain verify: an implement-only change has `implement` as its root with `prev=none`, which is legal because `implement` is its earliest present phase.
4. **Artifact binding, where the artifact is locally available.** At minimum, the implement record's `art=tree:<oid>` MUST equal `git rev-parse <headSha>^{tree}` of the change under view (PROV-6). The discovery / plan / review artifacts are re-hashable only when their bundles are present locally (the CLI with the run workspace); when a bundle is present, its `art=sha256:` MUST re-hash to the recorded value (PROV-12); when absent, that record is chain-checked but not artifact-checked, and the report says so.

### The verdict vocabulary

| Verdict | Meaning | Is it bad? |
|---|---|---|
| **verified** | Every present record passes parse, self-consistency, chain, and every locally-checkable `art`. | no |
| **unverified** | No provenance records found at all. Absence is not tampering. | no (just absent) |
| **tampered** | Some present record fails a check. The report names the exact record and field. | **yes** |

The verdict carries a **coverage** annotation listing which phases are present (`discovery, plan, implement, review` = full; `implement` alone = thin but internally consistent). Coverage is honest reporting, not a pass/fail: the lifecycle lets trivial work collapse phases ([spec.md](spec.md) section 2), so a thin chain is still `verified`. A team policy MAY require full coverage (a Governed concern), but the base verdict is these three values.

### Honest limit: `tampered` cannot tell iteration from tampering

`art=tree:<oid>` binds the implement record to the tip tree at the moment implement ran. An honest follow-up commit that adds more work to an open pull request changes the tip tree just as a malicious rewrite does, so PROV-6 fails identically in both cases and the verdict reads `tampered`. **The verdict cannot distinguish honest mid-iteration from tampering**; it reports only that the recorded implement artifact no longer matches the change under view. In practice an open pull request shows `tampered` between the last `/ai-implement` stamp and the next: re-running `/ai-implement` re-stamps the implement record (and, per Section 3, every later present phase) to the new tip tree, and the verdict returns to `verified`. The honest reading of `tampered` is "the tip tree does not match the recorded implement artifact," which the report says plainly rather than implying foul play.

### Honest coverage for mixed and partial histories

- A history where some commits carry trailers and others do not (hand commits, or history predating OpenADLC) verifies the records it can see and reports the rest as uncovered. It never reports `verified` for the whole history on the strength of a partial chain, and it never reports `tampered` for a commit that simply has no provenance.
- A squashed pull request whose commit trailers are gone verifies fully from the body embedding. That is the design working as intended.
- A pull request with no embedding and no commit trailers is `unverified`, not `tampered`. Missing provenance is a gap, not evidence of foul play.

### What is deliberately absent: no check-run

**Verification is view-time only. OpenADLC v1 publishes no check-run, ever.** A required check-run on the host would be a host-native gate by another name: it would move the release decision off the local consent checkpoint and onto the host provider, which the standard forbids (Law L4 locality; [spec.md](spec.md) section 4, the consent checkpoint is where release is decided). So OpenADLC does not create, require, or block on any check-run for provenance. The name `openadlc/attested` is **reserved and unused by OpenADLC's own tooling**: nothing OpenADLC ships publishes it. Reserving it documents the intent, but it cannot stop a third party from publishing a lookalike check-run under any name; provenance therefore claims only that **OpenADLC publishes none**, and a reader trusts the view-time recomputation, not the presence or absence of a host check-run (check PROV-7, an attestation about OpenADLC's own tooling, not a claim about the whole host).

---

## 6. Worked examples

Hashes and tree oids below are truncated with `...` for readability, exactly as they would be in a rendered pull request. A real record carries the full-length value (Section 2); the fully-computable golden vector is in Section 2.

### 6.1 An implement commit with its trailer

```
$ git log -1 --format=%B
feat(auth): add login form and session bootstrap

Wires the login route to the session service and persists the
refresh token. Covers the acceptance criteria in the plan.

Closes: #142
OpenADLC-Provenance: v=1; phase=implement; run=add-login-20260628T141233Z; art=tree:af5c9d3f...; prev=sha256:be71c2a0...; by=jane@example.com; at=2026-07-05T14:03:11Z; id=sha256:77de4b19...
```

The provenance trailer sits in the footer with the `Closes:` trailer. The `art=tree:af5c9d3f...` is the full tip-tree oid at the moment implement ran (shown truncated here).

### 6.2 A pull request description with the embedded block

```markdown
## Add login

Adds the login form and session bootstrap. Fixes #142.

... (normal PR description the human reads) ...

<!-- openadlc-provenance v1 -->
OpenADLC-Provenance: v=1; phase=discovery; run=add-login-20260628T141233Z; art=sha256:9b1f...; prev=none; by=jane@example.com; at=2026-06-28T14:12:40Z; id=sha256:4d2a...
OpenADLC-Provenance: v=1; phase=plan; run=add-login-20260628T141233Z; art=sha256:7c08...; prev=sha256:4d2a...; by=jane@example.com; at=2026-06-28T15:01:22Z; id=sha256:be71...
OpenADLC-Provenance: v=1; phase=implement; run=add-login-20260628T141233Z; art=tree:af5c9d3f...; prev=sha256:be71...; by=jane@example.com; at=2026-07-05T14:03:11Z; id=sha256:77de...
OpenADLC-Provenance: v=1; phase=review; run=add-login-20260628T141233Z; art=sha256:1e6b...; prev=sha256:77de...; by=asha@example.com; at=2026-07-05T16:20:05Z; id=sha256:c40f...
<!-- end openadlc-provenance -->
```

After a squash merge, the four commits collapse to one and their trailers are gone, but this block is untouched, so `readTrailers` still returns all four records and the verifier reconstructs the chain from the body alone.

### 6.3 `openadlc verify`: the verified case

```
$ openadlc verify 314
Provenance for PR #314 (run add-login-20260628T141233Z)

  discovery  2026-06-28T14:12:40Z  by jane@example.com    chain ok
  plan       2026-06-28T15:01:22Z  by jane@example.com    chain ok
  implement  2026-07-05T14:03:11Z  by jane@example.com    chain ok  tree af5c9d3f == HEAD tree
  review     2026-07-05T16:20:05Z  by asha@example.com    chain ok

VERDICT: verified   coverage: discovery, plan, implement, review (full)
Note: 'by' is a self-asserted claim, not a verified identity.
```

### 6.4 `openadlc verify`: the tampered case

Someone edited the code after implement stamped its record (or rewrote the diff), so the tip tree no longer matches the recorded `art`:

```
$ openadlc verify 314
Provenance for PR #314 (run add-login-20260628T141233Z)

  discovery  2026-06-28T14:12:40Z  by jane@example.com    chain ok
  plan       2026-06-28T15:01:22Z  by jane@example.com    chain ok
  implement  2026-07-05T14:03:11Z  by jane@example.com    ART MISMATCH
             art=tree:af5c9d3f...  but HEAD tree is 1b7740e9...
  review     2026-07-05T16:20:05Z  by asha@example.com    chain ok

VERDICT: tampered   the implement record does not match the change under view
Note: an open PR mid-iteration shows this until '/ai-implement' re-stamps (Section 5).
```

An `id` recompute mismatch (a record edited in place) or a `prev` that resolves to no present record prints the same way, naming the record and the failing field. A pull request with no block at all prints `VERDICT: unverified` and exits without error, because absence is not tampering.

### 6.5 A collapsed (implement-only) chain

Trivial work that collapsed discovery, plan, and review has one record, and it is legal:

```
$ openadlc verify feature/typo-fix
  implement  2026-07-05T09:14:02Z  by sam@example.com    chain ok (root, prev=none)  tree 3c1af08a == HEAD tree

VERDICT: verified   coverage: implement (thin but internally consistent)
```

`implement` carries `prev=none` because it is the earliest present phase; the chain check accepts it (Section 5).

---

## 7. Conformance checklist

Each check has an **ID**, an **assertion**, and a verification tag (`auto` / `audit` / `attest`, per [conformance.md](conformance.md)).

- **PROV-1** - Each `/ai-*` command that runs a phase produces exactly one `OpenADLC-Provenance` record for that phase, well-formed per Section 2 (`v=1`, a known `phase`, all required fields, typed `art` and `id`, the field-value grammar). _(Section 2, 3.)_ **auto** (a parser validates the line shape).
- **PROV-2** - `/ai-implement` stamps the implement record as a git trailer on the change's commit(s), and the tip commit carries it. _(Section 3.)_ **auto**
- **PROV-3** - The pull request body carries exactly one fenced provenance block (`<!-- openadlc-provenance v1 -->` ... `<!-- end openadlc-provenance -->`) holding every present phase's record, in canonical phase order. Two blocks is a fail, detected by the verifier parsing the body. _(Section 4.)_ **auto**
- **PROV-4** - Every record's `id` recomputes from its canonical bytes; a mismatch is `tampered`. _(Section 2, hash-link.)_ **auto**
- **PROV-5** - The chain resolves by `prev` links: exactly one present record has `prev=none` and it is the earliest present phase; every other `prev` resolves to a present record's `id`; the linked phases are strictly increasing in canonical order; no cycle, no dangling link. A break is `tampered`. _(Section 5.)_ **auto**
- **PROV-6** - The implement record's `art=tree:<oid>` equals `git rev-parse <headSha>^{tree}` of the change under view (full-length oid, exact equality); a mismatch is `tampered`. _(Section 2, 5.)_ **auto**
- **PROV-7** - OpenADLC's own tooling publishes no check-run for provenance: `openadlc/attested` is reserved and unused by anything OpenADLC ships. This attests to OpenADLC's tooling only; it cannot and does not claim a third party never published a lookalike. _(Section 5, Decision D6.)_ **audit** (inspect the OpenADLC tooling and a sampled set of OpenADLC-produced pull requests; confirm none publishes the check-run).
- **PROV-8** - The CLI verifies from the local git history and the pull request body with no network write and no backend; `openadlc verify` prints `verified` for a consistent chain and names the failing record and field for a tampered one. _(Section 5.)_ **auto**
- **PROV-9** - The dashboard renders the same verdict, computed at view time via `readTrailers` (or a read model over it), with no stored verdict and no backend endpoint. _(Section 5, Decision D7.)_ **audit** (spans the dashboard and the host adapter; verify a rendered view against a known chain).
- **PROV-10** - A mixed or partial history reports honest coverage: `verified` never covers a whole history on a partial chain, and a commit with no provenance is never reported `tampered`. _(Section 5, honest coverage.)_ **audit** (sample histories with gaps and confirm the reported coverage).
- **PROV-11** - `by` and the git author are presented as self-asserted claims, not as verified identity or non-repudiation; the verdict says so, and provenance is not conflated with the per-seat cryptographic audit chain. _(Section 1, Decision D8.)_ **attest**
- **PROV-12** - Where a non-implement phase's bundle is locally available, its `art=sha256:` re-hashes to the recorded value under the canonicalization rule of Section 2; where absent, that record is chain-checked only and the report says so. _(Section 2, 5.)_ **audit** (the bundle is present only with the run workspace).

---

## Decisions

Every silent choice, with the reasoning, so an implementer needs no interpretation.

- **D1. One trailer key, `OpenADLC-Provenance`, repeated per phase.** Git natively allows a repeated trailer key, so one family of lines carries the whole chain with one parser. The `v=` field versions the format without a new key. A minimal single family beats a per-phase key set (`OpenADLC-Plan`, `OpenADLC-Implement`, ...) that would multiply the parse surface for no gain.

- **D2. Value is a single-line `field=value` list in fixed order.** A git trailer is a single `Key: value` line, so the value has to fit on one line. A fixed-order, `"; "`-joined field list stays legible to a human, canonicalizes to bytes trivially (needed for hashing), and avoids the whitespace and quoting ambiguity of embedding JSON in a trailer. The field-value grammar (no space around `=`, no `"; "` inside a value) is pinned in Section 2 so two stampers produce identical bytes.

- **D3. The hash-link is a per-phase chain, not standalone per-artifact hashes.** A chain (each record's `id` hashes its own fields including `prev`; the next `prev` points back) gives artifact integrity (`art`) **and** phase-order integrity (a dropped, reordered, or forged earlier phase breaks a later link) for the same cost. Standalone hashes would prove each artifact but say nothing about the sequence. Honest limit: a chain is tamper-**evident** relative to itself, not tamper-**proof**. Anyone with write access can regenerate a fresh consistent chain. Non-repudiation across an org is the separate per-seat cryptographic audit chain (a backend concern), explicitly out of scope here. These trailers make a change legible and locally tamper-evident; they do not sign it.

- **D4. The implement artifact is the git tree id (`tree:<full-oid>`), not a diff or a commit id.** The tree id survives a squash and a clean rebase (both preserve the final tree), it is reproducible from git alone (`git rev-parse <tip>^{tree}`), and it needs no run workspace. That is exactly what lets the dashboard verify implement integrity from the pull request and repository with nothing else. A diff hash is fragile (rename detection, context, binaries); a commit id changes on every squash or rebase and would break on the very operations we need to survive. The oid is stored and compared full-length, so no short-prefix collision can slip through.

- **D5. The pull-request embedding is an HTML-comment-fenced block of identical `OpenADLC-Provenance:` lines.** HTML comments are invisible in rendered markdown, survive copy and edit, and give an unambiguous region to locate. Reusing the exact commit-trailer grammar inside the fence means one parser serves both the commit footer and the body. The block is replaced as a whole (idempotent) so re-runs never accrete duplicates. This block, not the commit trailers, is what survives a squash, which is the whole reason it exists.

- **D6. View-time verification only; no check-run; `openadlc/attested` reserved and unused.** A required check-run would be a host-native gate by another name: it moves the release decision off the local consent checkpoint onto the host provider, which the standard forbids (Law L4; [spec.md](spec.md) section 4). So nothing OpenADLC ships publishes, requires, or blocks on a check-run for provenance. Reserving `openadlc/attested` documents the intent, but the guarantee is scoped honestly: OpenADLC's own tooling publishes none. It cannot promise a third party never published a lookalike under some name, so a reader trusts the view-time recomputation, not a host check-run's presence or absence. Verification stays a read a human or the dashboard runs when they look, never a gate that stops a merge.

- **D7. Data source: CLI reads local git plus the pull request body; the dashboard reads via `readTrailers`; no backend endpoint and no stored verdict.** Provenance is a pure function of the git history and the pull request body, so verification recomputes on every view and there is nothing server-side to trust or to let fall stale. The CLI needs no network. The dashboard needs only the host adapter. **Needs the host adapter spec to agree:** the `readTrailers` signature, its return shape, and the fence markers are fixed there; this spec fixes what `readTrailers` must return (Section 4, the seam) and how the verifier consumes it. Reconcile the two before either ships.

- **D8. `by` (and the git author) is a self-asserted claim.** Git author and committer, and any `by=` string, are set by whoever runs the command; nothing here cryptographically binds a record to a person. Labeling it honestly in the verdict avoids implying an identity guarantee that only the per-seat audit chain provides. Provenance says which phases ran on which artifacts in which order; it does not say who, provably.

- **D9. Records are carried between phases in the run workspace, materialized to git by the two git-writing commands.** Discovery and plan never touch git, so their records accumulate in a local `provenance.jsonl` beside the OKF bundle (per [run-isolation.md](../plugins/adlc-core/references/run-isolation.md)) until `/ai-implement` writes the pull request and `/ai-review` updates it. This reuses the existing run-workspace home rather than inventing a new store. The durable carrier is the fenced block in the pull request body, not `provenance.jsonl`: a command that rewrites the block falls back to the existing body block when the local file is absent (a fresh checkout), so a missing local file never drops earlier records (Section 3).

- **D10. The first present phase carries `prev=none`, not only `discovery`.** The lifecycle lets trivial work collapse phases, so a chain may legally start at `plan` or `implement`. Tying `prev=none` to "the earliest present phase" rather than hardcoding `discovery` lets a collapsed chain verify as thin-but-consistent, while the canonical-order check still catches a genuinely out-of-order or forged sequence. The verifier resolves the chain purely by `prev` links, so it never depends on the order records happen to arrive in.

- **D11. Re-running a phase re-stamps every later present phase; the body block is authoritative.** An `id` hashes `art` and `at`, so a re-run changes it and would dangle later `prev` links. Regenerating the chain forward from the re-run phase keeps it consistent. Because an open pull request that has been iterated (new commits after the last implement stamp) reads `tampered` until re-stamped, the verdict is honest that it cannot tell iteration from tampering (Section 5), and the fix is to re-run `/ai-implement`.

- **D12. Deduping and ordering live in the verifier, not in `readTrailers`.** `readTrailers` stays a dumb, complete extractor (all trailers, both sources, tagged, byte-exact, source order); the verifier filters to the provenance key, dedupes by `id`, and reconstructs order from `prev` links. Keeping the adapter seam dumb lets the provenance vocabulary evolve without changing the host adapter, and puts every provenance-specific rule in one place.

---

Author: OpenADLC standard. Freshness: written for git-trailer provenance v1 against spec 0.1 (2026-07-05). Re-verify the `phase` enum and the `art` per-phase table against the four `/ai-*` commands before extending them; a new provenance-writing phase needs a new `phase` value and an artifact rule here first. The `readTrailers` cross-link tracks the host adapter spec; if that spec changes the fence markers or the trailer grammar, change them here in lockstep.
