---
name: static-code-scanner
version: 0.1.0
description: >-
  This skill should be used when the user asks to "run a static scan", "run SAST", "scan for
  secrets", "check for leaked credentials", "run semgrep", "run gitleaks", "run detekt", "lint
  for security issues", "secret scan before push", or wants a security pass over the local code
  before committing/pushing. Runs semgrep (multi-language SAST), gitleaks (secret detection), and
  detekt (Kotlin) locally and produces an approval-ready report including a "Secret scan:" line.
---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# Static Code Scanner

Run local static analysis with three layered tools and produce one consolidated, approval-ready
report. **Your code never leaves the machine.** Be precise about the network, though: semgrep rules are
fetched from the semgrep registry on first run (the `p/*` packs), and semgrep sends anonymous metrics by
default, so always pass `--metrics=off`. Code is never uploaded; only rule metadata and (without the flag)
metrics would be. To go fully offline, vendor the packs locally and point `--config` at the local copy.
Never use `--config auto` against changed code without consent. Findings stay local until the operator
approves any outbound action.

## Install / bootstrap
The scanners are often not installed. The operator decides whether to install them; the skill degrades
honestly to `unknown (not installed)` for any absent tool (see step 0).
```bash
brew install semgrep gitleaks        # macOS, the two cross-language tools
brew install detekt                  # detekt CLI; OR prefer the Gradle plugin (./gradlew detekt)
```
detekt is usually wired as a Gradle plugin in Android repos, run via `./gradlew detekt`; the `brew`
CLI is only the fallback for non-Gradle use.

## When to run
- Before a commit or push (push needs the operator's explicit yes), as the security pass in the ADLC verify step.
- On demand: "scan this", "secret scan", "run SAST", "any leaked keys?".

## Tooling map (pick by domain, this skill is general-purpose)
| Tool | Scope | Speed |
|---|---|---|
| `gitleaks` | secrets / credentials (git history + working tree), **every language** | sub-second on diffs |
| `semgrep` | multi-language SAST baseline (injection, authz, crypto, taint), the cross-language workhorse | seconds–minutes |
| language linter (by detected stack) | **Kotlin/Android** → detekt + Android Lint · **Python** → bandit · **JS/TS** → eslint (security plugins) · **Go** → gosec · **Ruby** → brakeman · **Rust** → cargo-audit/clippy · **PHP** → psalm/phpstan | seconds |

Always run gitleaks + semgrep; add the language linter(s) for whatever the repo actually contains. If a domain tool isn't installed, report `unknown (not installed)`: don't silently skip.

## Procedure

### 0. Detect what applies
Run only the relevant scanners. Check for tools and languages first:
```bash
command -v gitleaks semgrep 2>/dev/null
ls **/*.kt 2>/dev/null | head -1      # Kotlin present -> detekt applies
# detekt may be a Gradle plugin OR a CLI; check BOTH before reporting it missing:
command -v detekt 2>/dev/null || ./gradlew tasks --all 2>/dev/null | grep -qi '^detekt' \
  && echo "detekt available" || echo "detekt: unknown (not installed)"
```
A bare `command -v detekt` misses the Gradle-plugin case (the one this skill actually prefers), so a
`detekt` Gradle task counts as installed. If a tool is missing by both checks, report it as
`unknown (not installed)` in that section, do NOT silently skip; the operator decides whether to install
(see the Install / bootstrap section).

### 1. Secret scan (gitleaks), ALWAYS run this mode
Two modes; run both when committing:
```bash
# Working tree + uncommitted changes (no git history needed)
gitleaks dir . --report-format json --report-path /tmp/gitleaks-dir.json --redact --no-banner --exit-code 0

# Full git history (catches secrets in past commits)
gitleaks git . --report-format json --report-path /tmp/gitleaks-git.json --redact --no-banner --exit-code 0
```
- `--redact` masks the secret value so it never lands in the report or terminal.
- `--exit-code 0` lets the scan complete so the report is always produced; severity is judged from the JSON, not the exit code.
- Count findings: `jq 'length' /tmp/gitleaks-dir.json`.

### 2. SAST (semgrep), pinned rule packs
Use curated packs, not `auto`, to keep scans deterministic. The `p/*` packs are fetched from the registry
on first run; `--metrics=off` stops semgrep sending anonymous usage metrics (code is never uploaded either
way):
```bash
semgrep scan --metrics=off \
  --config p/security-audit --config p/secrets --config p/owasp-top-ten \
  --severity ERROR --severity WARNING \
  --sarif-output /tmp/semgrep.sarif --json-output /tmp/semgrep.json
```
- Scan only changed code in CI/pre-push: add `--baseline-commit <BASE_SHA>` (shows only new findings).
- Add language packs as relevant: `--config p/java`, `--config p/kotlin`, `--config p/javascript`.
- Count: `jq '.results | length' /tmp/semgrep.json`.

### 3. Language linter(s), by detected stack
Run the linter for each language present (see the tooling map); skip the rest:
```bash
./gradlew detekt                            # Kotlin/Android (or: detekt --input src --report sarif:/tmp/detekt.sarif)
bandit -r . -f json -o /tmp/bandit.json     # Python
npx eslint . -f json -o /tmp/eslint.json    # JS/TS (with eslint-plugin-security)
gosec -fmt sarif -out /tmp/gosec.sarif ./... # Go
```
Prefer the project's configured task (Gradle/npm/make) over a bare CLI invocation.

### 4. Triage
- Treat as BLOCKING: any gitleaks finding (real secret), any semgrep `ERROR`, any detekt security-rule finding.
- Treat as REVIEW: semgrep `WARNING`, style/maintainability findings.
- For each suspected false positive, note the rule id and the line, do not edit configs to suppress without operator sign-off.

## Report format (paste this into the report the operator reviews)
Produce exactly this block. The `Secret scan:` line is mandatory and feeds the operator's
approval decision: a downstream consumer can surface it verbatim in that report, and it satisfies the
deployment-readiness "no secret committed" check. Emit it in this stable, greppable format
(the literal prefix `Secret scan: ` at line start) so a consumer can parse it without guessing.

```
## Static scan: <repo> @ <short-sha>
Secret scan: <PASS | N finding(s)> (gitleaks: tree <a>, history <b>)
SAST:        <PASS | N ERROR / M WARNING> (semgrep packs: security-audit, secrets, owasp-top-ten)
Kotlin:      <PASS | N finding(s) | n/a> (detekt)

Top findings (max 10):
1. [BLOCK] <tool> <rule-id>, <file>:<line>, <one-line what/why>
...
Artifacts: /tmp/gitleaks-*.json, /tmp/semgrep.{sarif,json}, /tmp/detekt.sarif
```

## CRITICAL: outbound needs the operator's explicit yes
- If ANY scanner found a secret, STOP. Do not push, open a PR, or post anywhere until the operator
  has seen the `Secret scan:` line and explicitly approved. A leaked secret may already be live, recommend rotation, not just removal from the diff.
- Running the scanners and writing local report files needs no approval. Any step that sends results or
  code to the internet (push, PR, issue comment, uploading SARIF to a remote) needs the operator's
  explicit yes first: present the report, wait for an explicit "yes".

## References
- gitleaks CLI (v8, `git`/`dir`/`stdin`, `--report-format`, `--redact`, `--baseline-path`): https://github.com/gitleaks/gitleaks
- Semgrep CLI reference (`scan`, `--config`, `--severity`, `--sarif-output`, `--baseline-commit`, exit codes): https://docs.semgrep.dev/cli-reference
- Semgrep registry packs (`p/security-audit`, `p/owasp-top-ten`, `p/secrets`): https://semgrep.dev/explore
- detekt user guide (Gradle task + CLI, SARIF report): https://detekt.dev/docs/gettingstarted/gradle
