<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
# Android testing

Favor many fast tests low in the pyramid and few slow ones at the top: unit (JVM) » screenshot/Robolectric » e2e (Maestro/instrumentation).

## Commands (run module-scoped: not the whole suite)
- Unit: `./gradlew :<module>:testDebugUnitTest --stacktrace`
- Format/lint gate: `./gradlew spotlessApply && ./gradlew spotlessCheck` (+ project `lint`)
- e2e (Maestro): `maestro test .maestro/<feature>`: requires the app installed (`installInternalRelease` / `installPlayRelease`); group flows by feature, run by tag.

## Unit tests
- Test ViewModel **state transitions**, mappers, and interactors, assert observable state/behavior, not implementation details.
- Prefer fakes over mocks where practical. Use a test coroutine dispatcher; assert `Flow` emissions with Turbine.
- Tests are first-class, written before or right after the change: every behavior change ships with a test. Fix the **root cause**. Never disable/ignore a test to go green.

## Screenshot tests
- Use Roborazzi / Compose Preview screenshot tests for each UI state (content/loading/empty/error). Commit baselines; review diffs as part of review.

## What to test
- Behavior and real edge cases (empty, error, loading, boundary inputs). **Do not** test framework internals or write defensive tests for impossible states, over-testing is noise, not coverage.

## Evidence
- Capture test/build output (and screenshots for UI) so review and the operator's go/no-go on outbound steps can rely on evidence instead of re-running everything.
