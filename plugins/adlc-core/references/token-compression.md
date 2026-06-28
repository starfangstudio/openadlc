<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
# Token compression

Cut agent output tokens without dulling the human-in-the-loop: drop filler, prefer fragments and direct statements, lead with substance.

Two providers (`compression.provider` in `openadlc.yaml`):
- **`native`** (default): OpenADLC's own lightweight doctrine, this file. Zero install, always works; a stable, frozen baseline adapted from Caveman's technique (credited, see `THIRD-PARTY.md`).
- **`caveman`**: defer to the full, versioned, up-to-date Caveman (MIT) when the user installs it. Use this to stay current with upstream's modes and improvements.

Either way OpenADLC scopes compression so the operator never reads compressed mush.

Controlled by `compression` in `openadlc.yaml` (on by default):
- `enabled`: true
- `level`: lite | full | ultra (default `lite`, trims filler but stays readable)
- `provider`: native (default) | caveman (the full upstream, if installed)
- `protect_human_facing`: true

## Compress this (AI-internal, no human reads it)
- subagent -> orchestrator returns, inter-agent messages
- scratch reasoning, tool-call narration, internal notes
- the AI-face context of a story or plan (the full machine context, not the human summary)

This is where the savings live (Caveman benchmarks ~65% average). Use the configured level here.

## Never compress this (the human reads and approves it)
The human-facing artifacts stay full and clear (the KISS law + the two-faces law):
- the story's human summary
- the development plan summary
- the review verdict and report
- the pre-outbound consent report (what would go outbound)
- anything shown to the operator at a checkpoint

Terse machine output here would defeat the human-in-the-loop centerpiece. For anything a person must act on, readability wins over tokens.

## Levels
- **lite** (default): drop filler and hedging, keep full sentences where they aid clarity. Safe for all AI-internal output.
- **full**: fragments, minimal connectives, symbols over words.
- **ultra**: maximal compression. AI-internal only, never near a human artifact.

## Provenance and currency
The `native` provider is OUR OWN lightweight doctrine, adapted from Caveman's technique (Julius Brussee, MIT, https://github.com/JuliusBrussee/caveman); we did not copy its code or prompts. Because it is adapted, not a versioned dependency, it is a frozen snapshot: it does not auto-update with upstream. For the live, current Caveman, set `provider: caveman` and install it. The full record (referenced version, license, staying-current note) is in `THIRD-PARTY.md` at the repo root.
