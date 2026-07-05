---
name: maestro-ui-testing
description: "This skill should be used when writing, organizing, running, or debugging Maestro end-to-end UI tests for a mobile app, when the user mentions \"Maestro\", \"UI test\", \"e2e flow\", \"maestro test\", \".maestro\", \"flow yaml\", \"smoke test\", \"test by tag\", \"flaky UI test\", \"Maestro timeout\", \"test passes locally fails in CI\", \"Maestro Cloud\", or driving the installed app like a user. Covers flow structure, shared subflows, tags, selectors, flakiness and timeout tuning, local vs cloud runs, and CI failure triage."
version: 0.2.0
---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# Maestro UI testing

Maestro drives the *installed* app through YAML flows, as a user would. Flows are declarative, tolerant of minor timing, and meant to be isolated. Maestro is the top of the test pyramid (see `../../references/android-testing.md`): slow, high-signal, few of them.

## When NOT to use Maestro (check first)
Reach for a cheaper, faster, more stable test before writing a flow:
- **Logic or state assertions** (a mapper output, a computed total, a ViewModel state transition): unit test on the JVM. Faster and never flaky. See `../../references/android-testing.md`.
- **A single screen's rendering across states** (content / loading / empty / error): Compose UI test or a Roborazzi screenshot test, not a device flow.
- **Fast inner-loop feedback while coding**: unit/instrumented tests, not Maestro.

Use Maestro only for **cross-screen user journeys and smoke flows**: does login-to-home work end to end, does the paywall gate purchases, does onboarding complete. If an assertion fits in a unit test, it does not belong in a flow.

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
- Prefer **stable identifiers** (accessibility id / `testTag`) over visible text or index; text breaks on copy changes and localization. (See the `android-automation-tags` skill for wiring `testTag` through to Maestro.)

## Flakiness and timeouts (the #1 real-world pain)
A flaky flow is worse than no flow: it trains the team to ignore red. Fix the root cause, do not paper over it with sleeps.
- **Wait on a condition, never on a clock.** Do not `sleep`. Use waited assertions so Maestro proceeds the instant the UI is ready and fails only when it truly is not. Prefer `assertVisible` (which waits up to a default timeout) and `extendedWaitUntil` for a longer, explicit condition wait on slow screens.
- **Tune timeouts per step, not globally.** Bump the timeout on the specific slow step (network fetch, animation, cold start) rather than inflating a global wait that hides regressions. Set the value to a real p95 plus margin, not a guess.
- **Kill animations on the test device.** Set the emulator/device animator scales to 0 (window, transition, animator duration) before a run; animation mid-transition is the most common source of "element found then gone". Do this in device setup, not in the flow.
- **Idle before asserting.** After a tap that triggers navigation or a load, assert on the *destination's* stable element before the next action, so the flow self-synchronizes instead of racing.
- **Retry the flaky flow, not the whole suite, and treat retries as a smell.** Configure a small retry count (flow-level config or the CI `--retry` mechanism) so an infra blip does not fail the build, but a flow that only passes on retry is a bug to fix, not a config to keep. Track which flows retry.
- **Isolate to de-flake**: reset app state at flow start (`clearState`) so leftover data from a prior run cannot cause an intermittent failure.

Shape of a self-synchronizing, de-flaked flow (assert the destination, do not sleep):
```yaml
appId: com.example.app
---
- clearState            # start from a known state
- launchApp
- tapOn: { id: "loginEmailField" }
- inputText: "user@example.com"
- tapOn: { id: "loginSubmitButton" }
- extendedWaitUntil:    # wait on the condition, with an explicit ceiling
    visible: { id: "homeScreenRoot" }
    timeout: 10000
- assertVisible: { id: "homeGreeting" }
```

## Local vs cloud: decide deliberately
Default to **local** for authoring and PR-gate smoke flows; use **cloud** for breadth and device coverage you cannot reproduce locally.

| Factor | Prefer local | Prefer cloud |
| --- | --- | --- |
| Feedback loop | Authoring, debugging, inner loop | Full nightly / release suite |
| Device matrix | Your one emulator is enough | Many OS versions / real devices needed |
| Cost | Free (your machine) | Paid per run/minute; budget it |
| CI flakiness | Your CI runner has a stable emulator | Runner emulators are flaky; offload to managed devices |
| Debug artifacts | Immediate local screenshots/hierarchy | Web dashboard artifacts, slower to pull |

Do not run the entire suite in cloud on every PR (slow and costly); gate PRs on the local `smokeTest` subset, run the full matrix in cloud nightly and pre-release.

## Commands
```bash
maestro test .maestro/bookmarks/add_bookmark.yaml    # one flow
maestro test .maestro/bookmarks                        # a feature folder
maestro test .maestro --include-tags smokeTest         # by tag
maestro test --format junit --output report.xml .maestro   # CI report
maestro test --retry 1 .maestro/onboarding             # infra-blip guard (retries are a smell)
maestro hierarchy                                       # dump live view tree to find a selector
```
- Requires the app installed on a device/emulator first: `./gradlew installPlayRelease` (or `installInternalRelease` for more test affordances). See `../../references/android-build-gradle.md`.

## CI failure triage: app bug or test flake?
When a flow goes red in CI, do not blindly re-run. Pull Maestro's artifacts and read them:
1. **Screenshot at failure**: Maestro captures the screen at the failing step. Look first: wrong screen (navigation/timing bug), spinner still up (waited too little, raise that step's timeout), or a real error state (app bug).
2. **View hierarchy dump**: if a selector was not found, check the dumped tree (`maestro hierarchy` locally against the same build) for whether the element is absent (app bug or missing `testTag`) versus present-but-off-screen (scroll first) versus present-under-a-different-id (selector drift).
3. **Command log**: which step failed and how long it waited. A timeout at a network step points at slowness or a backend blip, not a UI defect.
4. **Reproduce locally on the same build** before filing a bug. **App bug** = fails deterministically on a clean device, artifacts show a real error/wrong state. **Test flake** = passes on retry, artifacts show a race or animation mid-frame; fix the flow (waited assertion, disabled animations), do not just re-run.

## Verify
Run the exact flow (or tag subset) and confirm a green result on a clean device before calling it done:
```bash
maestro test --format junit --output report.xml .maestro/bookmarks/add_bookmark.yaml
# exit code 0 and report.xml showing 0 failures == pass
```
Capture the run output (report and/or the failure screenshot) as evidence for review and the operator's go/no-go on any outbound step. Local work needs no approval; anything outbound (push, publish, post) needs an explicit per-action "yes" per the global consent law.

## References
- Maestro documentation: https://docs.maestro.dev/
- Structuring your test suite: https://maestro.dev/blog/maestro-best-practices-structuring-your-test-suite
- Test suites & reports (CI): https://docs.maestro.dev/cli/test-suites-and-reports
- Pack: `../../references/android-testing.md` (test pyramid, when each tier applies), `../../references/android-build-gradle.md` (install tasks).
