<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
# Third-party notices

Foreign code, techniques, and tools OpenADLC depends on or adapts. Each entry records the source, the license, what we use, and how we stay current. Update this file whenever a third-party dependency is added or adapted.

## Caveman (token-compression technique)
- **Source:** https://github.com/JuliusBrussee/caveman
- **License:** MIT
- **What we use:** the token-compression *technique* (terse, filler-dropping agent output). OpenADLC's `native` compression provider (`plugins/adlc-core/references/token-compression.md`) is our OWN lightweight doctrine, adapted from this technique. We did not copy Caveman's code or prompts.
- **Referenced version:** Caveman v1.9.0 (June 2026), concept snapshot.
- **Currency:** the `native` provider is a frozen, stable baseline (the "be terse" doctrine changes rarely); it does NOT auto-update with upstream. For the live, versioned Caveman (its full mode set and ongoing improvements), set `compression.provider: caveman` in `openadlc.yaml` and install Caveman via its own channel; OpenADLC then defers to it. Review this snapshot against upstream periodically.
- **Attribution:** technique by Julius Brussee, used under MIT.
