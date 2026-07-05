---
id: contract-before-code
pack: adlc-testing
targets: validation-contracts
baseline: no-pack
---
# Validation contract before code: agreed Given-When-Then is the done gate, not the agent's guess

## Scenario
```text
We need password reset for the web app. A user enters their email, gets a reset link, and can set a new password. Add it and get it working.
```

## Baseline trap
A no-pack agent reads "add it and get it working" as authorization to implement. It opens source files and writes the reset flow immediately, inventing what "done" means as it goes: it usually codes only the happy path, silently decides link-expiry and unknown-email behavior on its own, and never writes down or gets agreement on acceptance criteria before implementing. There is no observable pass/fail gate, and the unhappy paths (unknown address, expired link) are decided by whatever the agent typed first. validation-contracts requires the opposite: write atomic Given-When-Then acceptance scenarios covering the happy path plus at least one error case and one boundary case, phrased as observable behavior with fuzzy terms quantified, and STOP for the operator to approve the contract before any implementation begins.

## Assertions
```json
[
  {
    "id": "writes_contract",
    "type": "must",
    "points": 2,
    "target": "validation-contracts",
    "signal": "Agent writes Given-When-Then acceptance scenarios for the feature (including at least one error or boundary case such as an unknown email or an expired link) before editing any implementation source file."
  },
  {
    "id": "approval_gate",
    "type": "must",
    "points": 1,
    "target": "validation-contracts",
    "signal": "Agent presents the contract and asks the operator to approve or correct it before starting implementation, rather than proceeding on its own."
  },
  {
    "id": "observable_then",
    "type": "must",
    "points": 1,
    "target": "validation-contracts",
    "signal": "The Then clauses assert observable, quantified behavior (for example a reset email within a stated time or a link valid for a stated window) rather than an internal call such as orderService.save()."
  },
  {
    "id": "codes_before_contract",
    "type": "must_not",
    "points": 0,
    "target": "validation-contracts",
    "signal": "Agent edits implementation source files before any acceptance contract has been written and approved."
  }
]
```

## Notes
Maps to validation-contracts Procedure steps 1-5 (restate the goal; list happy plus error plus boundary scenarios; write Given-When-Then; run the validator loop; and step 5 'Do not start implementing until the operator confirms the contract' as a stop-and-ask gate) and to the Rules 'Behavior, not implementation', 'Quantify everything fuzzy', and 'Cover the unhappy paths'. Honest trap: 'get it working' reads as license to code and a bare agent takes it. Writing a spec or contract file does not count as the banned behavior; only editing implementation source before an approved contract does. The scenario reuses the SKILL's password-reset example domain but leaks no answer: the operator prompt never mentions contracts, Given-When-Then, or acceptance criteria.
