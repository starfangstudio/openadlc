---
name: ios-build-commands
description: >-
  Scheme-scoped xcodebuild, SPM, formatting, and fastlane command reference for iOS.
  Triggers: "build the iOS app", "run the iOS tests", "test a single XCTest", "build with
  xcodebuild", "run swift test", "run swift build", "lint the Swift code", "format Swift
  files", "run SwiftLint", "run SwiftFormat", "clean the iOS build", "what xcodebuild
  command runs the tests", "pipe through xcbeautify", "run the fastlane lane", "upload to
  TestFlight". Covers xcodebuild test/build/clean, SPM swift build/swift test, xcbeautify
  piping, SwiftLint and SwiftFormat as the Spotless analog, fastlane gym/upload_to_testflight,
  and the outbound checkpoint: local build/test/lint needs no approval; TestFlight and App Store
  Connect submission IS outbound.
version: 0.1.0
---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# iOS build commands

Drive iOS builds and tests with `xcodebuild` (workspace/project-scoped) or `swift build` /
`swift test` for pure SPM packages. Default to **scheme-scoped** invocations; building the
entire workspace is slow and rarely needed to verify one change. Pipe through `xcbeautify`
for readable output.

## Detect first

Run from the repo root. Before issuing any command, inspect what exists:

```bash
# Workspace, project, or pure SPM package?
find . -maxdepth 3 \( -name "*.xcworkspace" -o -name "*.xcodeproj" -o -name "Package.swift" \) \
  -not -path "*/build/*" | sort

# Available schemes (workspace takes priority over project if both exist)
xcodebuild -workspace <Name>.xcworkspace -list 2>/dev/null \
  || xcodebuild -project <Name>.xcodeproj -list

# Available simulators
xcrun simctl list devices available | grep iPhone | head -20

# Formatting tools present?
which swiftlint 2>/dev/null || echo "swiftlint: unknown"
which swiftformat 2>/dev/null || echo "swiftformat: unknown"
which xcbeautify 2>/dev/null || echo "xcbeautify: unknown"

# Fastfile present?
find . -maxdepth 4 -name "Fastfile" | head -5
```

Record: workspace vs. project vs. pure-SPM, the real scheme name, the available simulator
name, and which formatting tools are installed. Mark anything not found `unknown`; never
invent scheme names or simulator names.

## xcodebuild command reference

For the full command table and verify-a-change shortcuts, see
[references/ios-build-commands-detail.md](references/ios-build-commands-detail.md).

Key conventions: substitute `<W>` (workspace), `<S>` (scheme), `<T>` (test target) from
the Detect step; always use `set -o pipefail` and pipe through `xcbeautify`. Replace
`-workspace <W>.xcworkspace` with `-project <W>.xcodeproj` for non-workspace repos.

## SPM package commands

Use these for targets backed by a `Package.swift` with no Xcode workspace:

```bash
swift build                           # build all targets
swift build -c release                # release configuration
swift test                            # run all tests
swift test --filter SuiteName/testMethodName   # single test
swift package clean                   # clean build artifacts
```

## Formatting (Spotless analog)

SwiftLint enforces style rules; SwiftFormat auto-formats. Both read config from the repo
root (`.swiftlint.yml` / `.swiftformat`). If neither tool is installed, mark the step
`unknown` and ask the operator which tool the project uses.

For exact CLI flags and CI usage, see
[references/ios-build-commands-detail.md](references/ios-build-commands-detail.md).

## Fastlane lanes

Read the `Fastfile` first to discover actual lane names before invoking anything:
`cat fastlane/Fastfile | grep "lane :"`. For common lane patterns, see
[references/ios-build-commands-detail.md](references/ios-build-commands-detail.md).

## Rules

- **Scope every invocation to a scheme.** Running the full workspace with no scheme filter
  is a last resort.
- **Verify with a pass/fail command.** A green `xcodebuild test` is the proof a change
  works; reading the code is not.
- **Check `xcrun simctl list devices available`** before running simulator tests; a missing
  simulator produces a misleading "could not find destination" error, not a build error.
- **Local builds and tests need no approval.** Running `xcodebuild`, `swift test`, `swiftlint`,
  `swiftformat`, or a `fastlane test`/`fastlane build` lane is a local operation.

## Outbound checkpoint

Local work needs no approval. Outbound here (`upload_to_testflight`, `deliver`, any `fastlane` lane submitting to App Store Connect, signing uploads, posting to Apple's servers or any third party): stop, present exactly what would go out, and wait for an explicit "yes" (global consent law).

## References

- Apple, xcodebuild(1) man page: https://developer.apple.com/library/archive/technotes/tn2339/_index.html
- Apple, Automating the test process (xcodebuild test, -only-testing, -destination): https://developer.apple.com/library/archive/documentation/DeveloperTools/Conceptual/testing_with_xcode/chapters/08-automation.html
- xcbeautify (cpisciotta/xcbeautify), pipe usage and CI renderers: https://github.com/cpisciotta/xcbeautify
- SwiftLint (realm/SwiftLint), --strict and --fix flags: https://github.com/realm/SwiftLint
- SwiftFormat (nicklockwood/SwiftFormat), command-line usage: https://github.com/nicklockwood/SwiftFormat
- fastlane gym (build action): https://docs.fastlane.tools/actions/gym/
- fastlane upload_to_testflight: https://docs.fastlane.tools/actions/upload_to_testflight/
- fastlane deliver (App Store submission): https://docs.fastlane.tools/actions/deliver/
- Detail (command tables, shortcuts, formatting flags, fastlane patterns): [references/ios-build-commands-detail.md](references/ios-build-commands-detail.md)
