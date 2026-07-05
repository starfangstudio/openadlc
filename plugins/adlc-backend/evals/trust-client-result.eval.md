---
id: trust-client-result
pack: adlc-backend
targets: game-backend
baseline: no-pack
---
# Server re-validates match results; never trusts the client-reported score

## Scenario
```text
We have a Ktor + Postgres backend for our mobile game. When a match ends, the client POSTs the final score and outcome to the server. Add a /match/submit endpoint that records the result and updates the player's leaderboard entry. The client already knows the score, so keep it simple.
```

## Baseline trap
A no-pack agent reads "the client already knows the score, keep it simple" as license to write the client-supplied score straight into the scores/leaderboard table. It builds a POST handler that deserializes score and outcome from the request body and INSERTs them with no server-side re-validation, making the leaderboard trivially cheatable: any tampered client can submit an arbitrary score. This is the exact anti-pattern game-backend Step 4 and Step 5 exist to stop.

## Assertions
```json
[
  {
    "id": "revalidates",
    "type": "must",
    "points": 2,
    "target": "game-backend",
    "signal": "Agent designs the submit path to re-validate the result server-side (replay the seeded deterministic sim over the submitted seed and inputs and compare to the client result, or explicitly require the endpoint accept seed and inputs so the server can re-validate) rather than storing the client-reported score directly."
  },
  {
    "id": "rejects_mismatch",
    "type": "must",
    "points": 1,
    "target": "game-backend",
    "signal": "Agent states that a mismatch, or a client result that cannot be re-validated, is rejected (for example 409, flag, no score written) so a tampered score never reaches the leaderboard."
  },
  {
    "id": "writes_client_score",
    "type": "must_not",
    "points": 0,
    "target": "game-backend",
    "signal": "Agent credits or persists the client-supplied score/outcome to the leaderboard as authoritative without any server-side re-validation of that result."
  }
]
```

## Notes
Traces to game-backend SKILL Step 4 ("The server replays { seed, inputs[], clientResult } through the sim and rejects any mismatch"; "serverState != result -> 409, flag, no score") and Step 5 ("No client-supplied delta is ever applied directly"). The scenario deliberately omits seed and inputs; the correct pack behavior is to insist those be submitted so the server can replay and re-validate, so the revalidates signal allows either designing the replay or requiring the seed/inputs. The must_not was retargeted from backend-reviewer to game-backend because the banned behavior is the implementing agent persisting a client score, and this is an implementation scenario in which the read-only reviewer agent (which runs on a git diff) would not fire. Baseline trap is honest: "keep it simple, the client already knows the score" is a realistic operator framing that pushes a bare agent to trust the client. Maps to the pack manifest headline ("authoritative sim re-validation") and server-authoritative integrity. The must_not is the safety floor for a cheatable leaderboard.
