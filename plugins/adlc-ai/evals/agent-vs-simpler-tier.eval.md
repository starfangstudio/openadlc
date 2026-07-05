---
id: agent-vs-simpler-tier
pack: adlc-ai
targets: agent-architecture, ai-architect
baseline: no-pack
---
# Pick the minimum tier: no agent loop when a single call suffices

## Scenario
```text
Build me an AI agent that reads each incoming support ticket and tags it with one of our five categories. Set up the agent loop and the tools it needs.
```

## Baseline trap
A no-pack agent takes the word 'agent' literally and scaffolds a full tool-using loop: a tool registry, an iterate-until-done control loop, and tool schemas, all to perform what is a single-shot classification with a fixed set of five labels. The next step never depends on a prior tool result, so the loop, the tools, and the iteration budget are pure over-engineering that add latency, cost, and failure modes. The pack's agent-architecture Step 0 gates an agent on the Complexity test (an agent is warranted only when the next step cannot be determined until a prior step's result is seen) and directs a single LLM call otherwise, and ai-architect Step 2 biases toward the lowest tier, naming reaching for agents when a chain or single call would work as the most common mistake.

## Assertions
```json
[
  {
    "id": "runs_the_gate",
    "type": "must",
    "points": 2,
    "target": "agent-architecture",
    "signal": "Agent applies the should-I-build-an-agent test (Step 0 complexity gate) and concludes an agent is not warranted for a fixed single-shot classification, rather than scaffolding a loop on request."
  },
  {
    "id": "recommends_lower_tier",
    "type": "must",
    "points": 1,
    "target": "ai-architect",
    "signal": "Agent recommends the minimum tier (a single LLM call or classification prompt) for the categorization task and explains why the agent loop is unnecessary."
  },
  {
    "id": "builds_needless_loop",
    "type": "must_not",
    "points": 0,
    "target": "agent-architecture",
    "signal": "Agent scaffolds a tool-using agent loop with a tool registry and iteration budget for the single-shot classification without ever questioning whether an agent is warranted."
  }
]
```

## Notes
Maps to agent-architecture Step 0 (an agent is warranted only when ALL tests hold, chiefly Complexity: the next step cannot be determined until a prior step's result is seen; otherwise use a single LLM call, and 'Stop and document the justification') and ai-architect Step 2 tier table plus 'Bias toward the lower tier. The most common mistake is reaching for agents when a three-prompt chain would work.' Trap is honest because the prompt literally says 'build an agent', and a bare agent complies and scaffolds a loop; the pack's value is stopping to run the gate and downgrading to a single call. The scenario names the wrong tier ('agent') but does not spell out the correct answer (don't build one), so it is not leading. This scenario touches a design/scaffold surface, not an outbound or destructive action, so the anti-over-engineering must_not is the correct floor here rather than a consent floor. The must_not is trajectory-observable: a loop and tool registry are scaffolded, or they are not.
