---
name: maestro-ui-testing
description: "This skill should be used when writing, organizing, or running Maestro end-to-end UI tests for a mobile app, when the user mentions \"Maestro\", \"UI test\", \"e2e flow\", \"maestro test\", \".maestro\", \"flow yaml\", \"smoke test\", \"test by tag\", or driving the installed app like a user. Covers flow structure, shared subflows, tags, selectors, and local/cloud runs."
version: 0.1.0
---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# Maestro UI testing

Maestro drives the *installed* app through YAML flows, as a user would. Flows are declarative, tolerant of minor timing, and meant to be isolated.

## One flow = one user intent
- A flow tests a single intent ("log in", "add bookmark", "clear data"). If it spans more than one, split it. Smaller flows debug faster and run in parallel.
- **Flows must be isolated**: each must pass on a freshly reset device, with no dependence on a previous flow's state. Reset/skip onboarding at the start via a shared subflow.

## Layout
- Flows live under `.maestro/`, grouped by feature in subdirectories (`.maestro/onboarding/`, `.maestro/bookmarks/`).
- Reusable steps go in `.maestro/shared/` and are called with `runFlow` (path relative to the calling flow): `- runFlow: ../shared/skip_all_onboarding.yaml`.
- Use `config.yaml` to define execution order when flows must run in sequence.

## Tags (run subsets)
- Each flow may carry a `tags:` block (a YAML list, each tag on its own line). Tag smoke tests `smokeTest`, release gates `releaseTest`, etc.
- Run by tag: `maestro test .maestro --include-tags smokeTest` (or `--exclude-tags`).

## Selectors
- Prefer **stable identifiers** (accessibility id / `testTag`) over visible text or index, text breaks on copy changes and localization. (See `android-automation-tags` for tagging conventions.)

## Commands
```bash
maestro test .maestro/bookmarks/add_bookmark.yaml   # one flow
maestro test .maestro/bookmarks                       # a feature folder
maestro test .maestro --include-tags releaseTest      # by tag
maestro test --format junit .maestro                  # CI report
```
- Requires the app installed on a device/emulator first (a release-type build is typical for UI testing).

## Verify
- A flow is done when it passes on a clean device locally. Capture the run output (or a recording) as evidence for review and the operator's go/no-go on outbound steps.

## References
- Maestro documentation: https://docs.maestro.dev/
- Structuring your test suite: https://maestro.dev/blog/maestro-best-practices-structuring-your-test-suite
- Test suites & reports (CI): https://docs.maestro.dev/cli/test-suites-and-reports

## Example layout note
A typical modular project keeps flows in `PROJECT_DIR/.maestro/` grouped by feature, with a `shared/` dir for common subflows, and tags flows for selective runs. Build for UI testing with `./gradlew installPlayRelease` (or `installInternalRelease` for more test affordances) before running Maestro. Runs locally or on Maestro Cloud.
