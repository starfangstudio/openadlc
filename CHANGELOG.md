<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
# Changelog

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Versioning follows [SemVer](https://semver.org/).

## [Unreleased]

### Added
- Lifecycle checkpoints: the harness stops and asks the operator for an explicit yes before anything leaves the machine (push, PR, post). Outbound is a human decision, not a default; reading and local work are never stopped.
- The four-command harness: `/agentic-intake`, `/agentic-plan`, `/agentic-implement`, `/agentic-review`.
- Claude Code plugin manifest and hook wiring.
- The `/O` brand mark assets.
- Community docs: contributing, security, code of conduct, support.

### Changed
- Licensing reframed to a dual model: the ADLC standard (the `standard/` tree) stays CC-BY-4.0 as a genuine open standard; the implementation (`plugins/`, hooks, adapters, the harness, the four `/agentic-*` commands) moves to the OpenADLC source-available license (see the `LICENSE` file), publicly viewable and free for individuals and the public, with a commercial seat license required for use by or on behalf of an organization. "Open" now means open standard plus publicly viewable source plus free for individuals, not OSI open source. Framing: open standard, commercial reference implementation.
- Contributions now use a Contributor License Agreement (CLA, checked on every pull request) instead of the Developer Certificate of Origin (DCO).

Pre-release. Nothing here is stable yet; expect breaking changes.
