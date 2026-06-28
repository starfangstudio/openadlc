<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
# Android performance rules

Measure first, change second. Never claim a perf win without a before/after number from a
real benchmark on a real device. Optimize Critical User Journeys (CUJs): cold start, the first
scrollable list, and any flow where latency is user-visible.

## Baseline Profiles (the default win)
Baseline Profiles pre-compile (AOT) hot code paths via ART, giving ~30% faster execution from
first launch, no Play-store wait. Add one before micro-optimizing.

- Create the profile with a dedicated Baseline Profile module (Android Studio template, AGP 8.0+)
  containing a `BaselineProfileRule` test that drives the CUJ via UiAutomator/Compose test tags.
- Generate: `./gradlew :app:generateBaselineProfile`. The output ships in the AAB at
  `assets/dexopt/baseline.prof`.
- Add a **Startup Profile** too (`startup-prof.txt`) for DEX layout, ~15% extra startup gain.
- The generation (`benchmark`) variant runs with `isMinifyEnabled = false`; the release build keeps
  R8 on, AGP 8.2+ rewrites profile rules to match obfuscated names automatically.

## Macrobenchmark (the measurement)
Macrobenchmark lives in a separate `com.android.test` module and measures a release-like build.

- Use `MacrobenchmarkRule.measureRepeated(...)` with `StartupTimingMetric()` for launch,
  `FrameTimingMetric()` for jank/scroll.
- Compare `CompilationMode` to prove the profile works:
  | Mode | Meaning | Use |
  |---|---|---|
  | `None()` | interpreted/JIT, no AOT | worst-case / first-run floor |
  | `Partial()` | AOT via Baseline Profile | realistic shipped performance |
  | `Full()` | whole app AOT | best-case ceiling |
- Run `Partial()` vs `None()`; the delta is the Baseline Profile win. `iterations = 5+`, run on a
  physical device (emulator numbers are noise), close other apps.

## App-startup tracing
- TTID (time to initial display) is logged automatically, grep Logcat for `Displayed`.
- For TTFD (fully usable), call `Activity.reportFullyDrawn()` once the screen is truly ready;
  ART prioritizes work before that call.
- Profile cold start with system traces (Perfetto / Macrobenchmark trace output), not guesswork.
  Move work off the main thread and out of `Application.onCreate`; lazy-init with App Startup.

## Compose recomposition & strong skipping
- Enable **strong skipping mode** (default in Compose compiler 1.5.4+ / Kotlin 2.x): it skips
  composables with unstable params when the same instance is passed, and auto-remembers lambdas
  capturing unstable values. Confirm it is on rather than hand-annotating everything `@Stable`.
- Diagnose with the compiler stability report and the Layout Inspector recomposition counts:
  ```
  -Pandroidx.compose.compiler.plugins.kotlin.reportsDestination=<dir>
  ```
  Read the `*-composables.txt` report to see which composables are `skippable`/`restartable`.
- Fix causes, not symptoms: hoist state, pass stable types (or `ImmutableList` from
  kotlinx-collections-immutable), defer reads with lambdas (`Modifier.offset { }`), key `LazyColumn`
  items. Avoid unstable params (raw `List`, lambdas recreated each recomposition) on hot paths.

## R8 / keep rules
- Ship release with `isMinifyEnabled = true` and `isShrinkResources = true`; R8 shrinks, optimizes,
  and obfuscates. Smaller DEX + fewer methods = faster load.
- Keep rules are a scalpel, not a hammer. Add `-keep` only for what reflection/JNI/serialization
  reaches; over-keeping defeats shrinking. Most libraries ship `consumer-rules.pro`: do not
  duplicate them.
- Verify the shrunk build actually runs the CUJ before trusting numbers; a missing keep rule fails
  at runtime, not compile time. Inspect `mapping.txt` / `usage.txt` under `build/outputs/mapping/`.

## Stop-and-verify gate
Before claiming any perf change is done: state the metric, the device, the before number, and the
after number from a Macrobenchmark run. No number, not done.

## ADLC delta
Macrobenchmark runs are local and need no approval. Committing a regenerated `baseline.prof` is a local
commit. Publishing benchmark results, pushing the profile branch, or opening a PR is outbound: get the operator's explicit yes first (see the consent law in CLAUDE.md).

## References
- Baseline Profiles overview: https://developer.android.com/topic/performance/baselineprofiles/overview
- Benchmark Baseline Profiles with Macrobenchmark, https://developer.android.com/topic/performance/baselineprofiles/measure-baselineprofile
- Strong skipping mode: https://developer.android.com/develop/ui/compose/performance/stability/strongskipping
- App startup analysis & optimization: https://developer.android.com/topic/performance/appstartup/analysis-optimization
