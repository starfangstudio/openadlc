---
name: validate-scenario
description: "This command should be used when the user types \"/validate-scenario\", or asks to \"validate a scenario\", \"run this scenario and check it works\", \"walk through the user flow\", \"verify the feature end to end by using it\", or \"confirm the change behaves correctly when I do X\". Wraps the built-in `verify` skill to run one concrete scenario against the live app and report observed behavior vs. expected."
version: 0.1.0
disable-model-invocation: true
allowed-tools:
  - Bash
  - Read
  - Skill
---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# /validate-scenario

Drive the running app through ONE concrete scenario and report what actually
happened against what was expected. This **wraps the built-in `verify` skill**: that skill owns launching the app and observing behavior. This command adds the
ADLC delta: a written scenario contract up front, an evidence-backed pass/fail
verdict, and a stop-and-ask for the operator's explicit yes on anything outbound.

Scenario to validate (free text, or a path to a scenario/test spec): $ARGUMENTS

## Pipeline: what this loads, start → finish
1. pin the scenario contract (this command) → 2. built-in **`verify`** skill launches and drives the app → 3. observe against `Then` + capture evidence → 4. print the verdict → stop and ask the operator for an explicit yes if anything goes outbound.
- **Models:** Sonnet. Never Haiku.
- **Outbound:** none unless you post the result.

## What to do

1. **Pin the scenario contract (local).** Before running anything, write down the
   contract in the format below. The input is normally ONE Given-When-Then scenario
   from a `validation-contracts` contract (in the run's `spec.md` or
   `~/.openadlc/runs/<workspace>/<run-id>/plan/contract.md`), this command runs that single scenario
   against the live app. If `$ARGUMENTS` is vague or empty, ask for the missing pieces,
   do not guess preconditions or success criteria.
   ```
   Scenario:   <one line, what the user does>
   Given:      <preconditions / starting state>
   When:       <the exact steps, in order>
   Then:       <observable expected outcome, UI state, log line, response, side effect>
   ```

2. **Invoke the built-in `verify` skill to run it.** Call the `verify` skill to
   launch the app and execute the `When` steps. `verify` chooses how to drive the
   app (CLI, server, browser, emulator, screenshot). Do not reimplement launching
   here, defer to it. For Android, prefer the module-scoped path the project rules
   define (`./gradlew :<module>:testDebugUnitTest`, Maestro `.maestro/<feature>`,
   or a Roborazzi/Compose state) over manual clicking when one already covers the
   scenario.

3. **Observe against `Then`, not against vibes.** Capture concrete evidence for the
   expected outcome: the screenshot, the log line, the HTTP status/body, the asserted
   state. One scenario, one verdict. If the outcome only *looks* right but you could
   not observe the specific `Then` signal, the result is **unknown**, not pass.

4. **Probe one boundary if it's cheap.** After the happy path, try the single most
   likely failure variant the scenario implies (empty input, error state, the
   off-by-one). Skip if it would need new setup, note it as not-checked rather than
   claiming coverage you don't have.

5. **Print the report (local, no approval needed).** Use the format below. **Stop here.**

## Outbound checkpoint

Local work (edits, builds, tests, observing the app) needs no approval. Anything outbound (push, PR comment, deploy, ticket update, API write) stops here: present the report, ask plainly what would go out, and wait for the operator's explicit "yes" before sending anything.

## Report format

```
Scenario: <one line>
Verdict:  PASS | FAIL | UNKNOWN

  Given:    <preconditions>
  When:     <steps run>
  Then:     <expected>
  Observed: <what actually happened>
  Evidence: <screenshot path | log line | status code | assertion>

Boundary checked: <variant + result, or "not checked, <reason>">

[FAIL only] Likely cause: <one line, or "unknown, needs investigation">
Outbound if approved: <none | push <branch> | post to PR #<n> | …>
```

## Guardrails

- Run and observe locally; the only outbound step is the checkpoint section above, which needs the operator's explicit yes.
- A verdict requires observed evidence. No evidence → **UNKNOWN**, never PASS.
- Validate the scenario as written. If the code is wrong, report it, do not edit
  the app to make the scenario pass.
- Mark anything you could not observe `unknown`. Never invent a log line or result.

## References

- Built-in skill wrapped: `verify` (run the app, observe behavior).
- Claude Code: verifying changes by running the app: https://code.claude.com/docs/en/skills
- Behavior framing (Given/When/Then): https://cucumber.io/docs/gherkin/reference/
