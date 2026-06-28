<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
Consumed by the `ios-build-commands` skill. Load on demand; do not load independently.

## xcodebuild command table

Substitute `<W>` (workspace file), `<S>` (scheme), `<T>` (test target), and simulator name
from the Detect step. Use `set -o pipefail` so xcodebuild's exit code propagates through
the xcbeautify pipe.

| Goal | Command |
|---|---|
| Build (debug) | `set -o pipefail && xcodebuild build -workspace <W>.xcworkspace -scheme <S> -configuration Debug \| xcbeautify` |
| Build (release) | `set -o pipefail && xcodebuild build -workspace <W>.xcworkspace -scheme <S> -configuration Release \| xcbeautify` |
| Run all tests on simulator | `set -o pipefail && xcodebuild test -workspace <W>.xcworkspace -scheme <S> -destination "platform=iOS Simulator,name=iPhone 16,OS=latest" \| xcbeautify` |
| Single test suite or method | `set -o pipefail && xcodebuild test -workspace <W>.xcworkspace -scheme <S> -destination "platform=iOS Simulator,name=iPhone 16,OS=latest" -only-testing:<T>/SuiteName/testMethodName \| xcbeautify` |
| Build for generic device (no simulator) | `set -o pipefail && xcodebuild build -workspace <W>.xcworkspace -scheme <S> -destination "generic/platform=iOS" \| xcbeautify` |
| Clean derived data | `xcodebuild clean -workspace <W>.xcworkspace -scheme <S>` |

Replace `-workspace <W>.xcworkspace` with `-project <W>.xcodeproj` for non-workspace repos.

## Verify-a-change shortcuts

```bash
# Fastest loop: re-run one failed test method after a fix
set -o pipefail && xcodebuild test \
  -workspace <W>.xcworkspace \
  -scheme <S> \
  -destination "platform=iOS Simulator,name=iPhone 16,OS=latest" \
  -only-testing:<T>/SuiteName/testMethodName | xcbeautify

# Parallel testing across device types (CI)
set -o pipefail && xcodebuild test \
  -workspace <W>.xcworkspace \
  -scheme <S> \
  -destination "platform=iOS Simulator,name=iPhone 16,OS=latest" \
  -destination "platform=iOS Simulator,name=iPhone SE (3rd generation),OS=latest" \
  -parallel-testing-enabled YES | xcbeautify

# Debug a build failure
set -o pipefail && xcodebuild build -workspace <W>.xcworkspace -scheme <S> \
  -destination "platform=iOS Simulator,name=iPhone 16,OS=latest" | xcbeautify --report junit
```

If a simulator is not found, run `xcrun simctl list devices available` and substitute the
exact simulator name. If derived data is stale after an Xcode upgrade, wipe it:
`rm -rf ~/Library/Developer/Xcode/DerivedData`.

## Formatting commands

SwiftLint enforces style rules; SwiftFormat auto-formats. Both read config from the repo
root (`.swiftlint.yml` / `.swiftformat`). Check for the config files before running.

```bash
# Lint (warnings treated as errors with --strict)
swiftlint lint --strict

# Auto-fix safe violations
swiftlint --fix

# Auto-format all Swift files under current directory
swiftformat .

# Format + verify no diff remains (useful in CI)
swiftformat . && git diff --exit-code
```

If neither tool is installed, mark the formatting step `unknown` and ask the operator
which tool (if any) the project uses before running anything.

## Fastlane lane commands

Read the `Fastfile` first to discover actual lane names before invoking anything:

```bash
cat fastlane/Fastfile | grep "lane :"
```

Common lane patterns (substitute the project's real lane names):

```bash
fastlane test          # wraps xcodebuild test
fastlane build         # wraps gym (xcodebuild archive)
fastlane beta          # builds + uploads to TestFlight via upload_to_testflight
fastlane release       # builds + submits to App Store via deliver
```
