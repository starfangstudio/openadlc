<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
# adlc-android · assets

## `project-settings.example.json`
Copy into a real Android project's `.claude/settings.json` to turn on the ADLC verification-loop automation (this is the automation the plan calls for, it belongs in your Android project, not in the OpenADLC repository itself, which is not an Android project (no Gradle)):
- **Permission allowlist**: pre-approves only local/read-only commands (module tests, spotless, lint, assemble, `git` read, `gh pr` read). It pre-approves **no** outbound command; push/PR/etc. still require the operator's explicit yes first. *Invariant: an allowlist must never auto-approve an outbound action.*
- **PostToolUse**: runs `./gradlew spotlessApply` after a Kotlin edit, so formatting never breaks CI.

### Optional: a Stop hook that blocks turn-end until tests pass
Aggressive (re-runs on every stop); enable once the suite is fast enough. Add to `hooks`:
```json
"Stop": [ { "hooks": [ { "type": "command",
  "command": "./gradlew :app:testDebugUnitTest -q >/dev/null 2>&1 || { echo 'unit tests failing, fix before stopping' >&2; exit 2; }" } ] } ]
```
Tune the module/task to the project.
