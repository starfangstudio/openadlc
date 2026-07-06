---
name: unity-testing
description: >-
  This skill should be used when the user asks to "add tests to a Unity project",
  "write a unit test for the sim", "test the deterministic simulation", "add a golden
  replay test", "set up EditMode tests", "add PlayMode tests", "run the Unity test
  suite in CI", "verify determinism with replays", "create a test assembly", "add NUnit
  tests to Unity", "test the battle sim logic", "run Unity tests from the command line",
  or "wire up Unity Test Framework". Covers the full pyramid: EditMode unit tests for
  pure C# sim/logic, PlayMode scene integration tests, and golden-replay determinism
  tests for the lockstep sim. Specializes the adlc-testing strategy for Unity 6.x.
version: 0.1.0
---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# unity-testing

Test a Unity project with a pyramid shape: many fast EditMode tests, fewer PlayMode
tests, and targeted golden-replay determinism tests for the lockstep sim.

**Boundary:** this skill covers the test pyramid and CI mechanics (EditMode/PlayMode,
running suites, asserting pass/fail). Building the deterministic sim itself (fixed-point
math, seeded RNG, lockstep, the golden-replay harness) is `unity-deterministic-sim`;
this skill tests that sim once it exists.

## Step 1: Detect first

Never invent assembly names or test paths. Inspect what exists:

```bash
# Locate existing test assemblies
find . -name "*.asmdef" | xargs grep -l "TestAssemblies" 2>/dev/null

# List existing test directories and their mode (Editor = EditMode)
find . -path "*/Tests/*.asmdef" -exec cat {} \; | grep -E '"name"|"includePlatforms"'

# Check Unity Test Framework package version
grep -A1 '"com.unity.test-framework"' Packages/manifest.json
```

Record: existing assembly names, test paths, whether PlayMode or EditMode assemblies
exist, and the UTF version. Mark anything you cannot determine `unknown`; never invent
assembly names or namespace paths.

## Step 2: Assembly definition layout

Unity requires separate `.asmdef` files to declare test assemblies. Match the pattern
of any existing test assembly. EditMode assemblies must set `"includePlatforms": ["Editor"]`;
PlayMode assemblies use `"includePlatforms": []`. Both need `"optionalUnityReferences": ["TestAssemblies"]`.
Use `[Test]` in EditMode; use `[UnityTest]` with `yield return` in PlayMode only when frame timing is required.

For the folder layout and minimum `.asmdef` JSON for both modes, see [references/unity-testing-detail.md](../../references/unity-testing-detail.md).

## Step 3: The pyramid -- what goes where

| Layer | Mode | Volume | What to test |
|---|---|---|---|
| Sim / logic unit tests | EditMode | High | Deterministic sim, pure C# rule evaluators, stat formulas, targeting logic, income curves |
| Integration / scene tests | PlayMode | Low | Scene load, MonoBehaviour lifecycle, input routing, UI state |
| Golden-replay determinism | EditMode | Critical | Full sim run from a seed; compare output hash to a committed golden file |

**Do NOT test** rendering, physics fidelity, or audio in automated tests -- those are
human-review territory.

## Step 4: Deterministic sim -- golden-replay tests (highest-value target)

The lockstep sim must produce identical output given identical input across Unity
versions and platform targets. Load the golden input (commands + seed), run the sim
(pure C#, no MonoBehaviour, no Unity physics), hash the output state, and assert it
equals the committed hash. An unexpected hash change is a blocking regression; an
intentional sim change requires regenerating and committing the golden file.

For the full C# test sample and golden-file conventions, see [references/unity-testing-detail.md](../../references/unity-testing-detail.md).

## Step 5: Run tests

**Local (Unity Editor UI):** Window > General > Test Runner.

**CLI (CI / batchmode):** use `-batchmode -runTests -testPlatform <EditMode|PlayMode>
-projectPath -testResults -logFile`. Always pass `-logFile`; batchmode suppresses console
output by default. Exit code 0 = all pass, non-zero = failures; parse `test-results-*.xml`
(NUnit format) in CI.

For the full CLI invocation with all flags and filter options, see [references/unity-testing-detail.md](../../references/unity-testing-detail.md).

## Step 6: Validator loop

```
Run batchmode -> exit 0? -> done.
                exit non-0? -> open test-results.xml, find <test-case result="Failed">,
                               fix the failing assertion or production code,
                               re-run until exit 0.
```

Do not claim done without an exit-0 run. A passing test file with zero assertions is
not a passing test.

## Guardrails

- EditMode test assemblies must set `"includePlatforms": ["Editor"]` or tests will
  attempt to compile for device targets and fail.
- The deterministic sim must be in a pure C# assembly with **no** `UnityEngine.Physics`
  or frame-dependent APIs -- if it is, it cannot be reliably tested in EditMode.
- Never assert on floating-point frame timing or rendering output in automated tests.
- Keep PlayMode tests sparse: each one requires scene load overhead and a Play-mode
  domain reload. Prefer EditMode for all logic that can be isolated.

## Outbound checkpoint

Local work needs no approval. Anything outbound (publish, push, post) needs the operator's explicit per-action "yes" first; see the global consent law.

## References

- unity-testing detail (assembly layout, golden-replay code sample, full CLI flags):
  [references/unity-testing-detail.md](../../references/unity-testing-detail.md)
- Unity 6 Manual -- Edit mode and Play mode tests:
  https://docs.unity3d.com/6000.4/Documentation/Manual/test-framework/edit-mode-vs-play-mode-tests.html
- Unity Test Framework -- Running tests from the command line (flags: `-runTests`,
  `-testPlatform`, `-testResults`, `-assemblyNames`, `-testFilter`):
  https://docs.unity3d.com/Packages/com.unity.test-framework@1.1/manual/reference-command-line.html
- Unity Test Framework -- Workflow: create a new test assembly (`.asmdef` setup):
  https://docs.unity3d.com/Packages/com.unity.test-framework@1.1/manual/workflow-create-test-assembly.html
