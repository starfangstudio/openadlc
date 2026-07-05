---
name: agent-architecture
description: >-
  This skill should be used when the user asks to "design an agentic AI feature", "build a
  tool-using loop", "add function calling to my app", "decide whether I need an agent",
  "wire up multi-step AI reasoning", "design the tool set for an AI agent", "set up a
  human-in-the-loop checkpoint", "add guardrails to my agent", "prevent my agent from
  taking destructive actions", "manage context in a long-running agent", "subagent for
  heavy reads", "evaluate my agent's trajectory", "add evals for agentic behavior",
  "write evals for tool calls", "design tool schemas for Claude", or "compare agent vs
  workflow vs single LLM call". Covers the full design cycle: should-I-build-an-agent
  test, tool design (names, descriptions, typed schemas, least-privilege), the tool-use
  loop (manual vs SDK runner), context management (compaction, subagents), guardrails and
  human-in-the-loop for risky actions, and trajectory evals.
version: 0.1.0
---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# Agent architecture

Design a tool-using agentic feature: decide whether an agent is warranted, design its
tool set, wire the loop, add guardrails, and verify with trajectory evals.

**Boundary:** this skill covers agent architecture and tool design. For retrieval
pipelines use the `rag-pipeline` skill; for LLM API integration use the `llm-integration`
skill. Defer to the built-in `claude-api` skill for current model IDs and pricing -- never
hardcode them here.

## Step 0: Should I build an agent?

An agent is warranted only when ALL of the following hold:

| Test | Pass condition |
|---|---|
| **Complexity** | The next step cannot be determined until a prior step's result is seen; a fixed workflow or single call cannot express this. |
| **Value** | The task is high enough value to justify latency (agents are slower), cost (more tokens), and the engineering overhead of a loop. |
| **Viability** | Clear, measurable success criteria exist; the agent can be evaluated. |
| **Cost of error** | Errors are recoverable via retry or a human checkpoint, or the blast radius is contained. |

If any test fails, use the simplest option instead:

- Single LLM call with a well-crafted prompt + retrieval: covers most tasks.
- Deterministic workflow with LLM nodes (prompt chaining, routing, parallelisation):
  covers decomposable tasks with a known step count.
- Agent: reserve for genuinely open-ended, multi-step tasks where the path is unknown
  upfront.

Stop and document the justification before proceeding to Step 1.

## Step 1: Detect first

Inspect the repo before designing anything. Match existing patterns: framework in use,
existing tool schema format, loop implementation, any HITL checkpoints.

For the exact grep commands, see [references/agent-architecture-detail.md](../../references/agent-architecture-detail.md).

## Step 2: Design the tool set

Key rules for each tool in the agent's allowlist (full rationale in the detail reference):

- **Name**: `service_resource_action` format (e.g., `github_pr_create`). No ambiguous verbs like `update`.
- **Description**: onboarding-level prose; what it does, when NOT to use it, parameter semantics, return shape. Minimum 3-4 sentences. Vague descriptions are the primary cause of agent errors.
- **Schema**: typed JSON Schema; `required` explicit; enums for fixed values; no bare `object` or `any`.
- **Least-privilege**: only the tools the current task needs. Destructive/outbound tools require a HITL approval step (Step 4).
- **Response shaping**: return only high-signal fields; summarize or trim large payloads.
- **Consolidation**: one tool with an `action` enum beats N separate tools for related operations.

For expanded guidance, see [references/agent-architecture-detail.md](../../references/agent-architecture-detail.md).

## Step 3: Wire the loop

Two valid patterns: manual loop (raw SDK, more control) and SDK tool runner (less
boilerplate). Use the manual loop when you need custom error handling, per-tool logging,
rate-limit back-off, or mid-loop HITL checkpoints. The ADLC in-house pattern uses the manual
loop and stops to ask the operator for an explicit yes before any outbound/destructive call;
mirror this for any agent that touches external systems.

For loop pseudocode and SDK call shapes, see [references/agent-architecture-detail.md](../../references/agent-architecture-detail.md).

Pass `budget_tokens` (or equivalent) when the SDK supports it so the agent self-manages
its token usage and finishes gracefully rather than truncating.

## Step 4: Guardrails and human-in-the-loop

Classify every tool by risk tier (read-only / idempotent write / destructive+outbound).
For the full tier table, see [references/agent-architecture-detail.md](../../references/agent-architecture-detail.md).

For destructive/outbound tools: before executing, stop the loop, present exactly what
the tool will do (target, payload, scope), and wait for the operator's explicit "yes".
Wire this as an in-loop confirmation step -- never autonomous.

Additional guardrails:
- Validate tool inputs against the schema before passing to the executor; reject
  malformed calls and return a structured error as a `tool_result`.
- Cap the loop iteration count (e.g., 20 turns) and token budget to bound runaway agents.
- Log every tool call and result for trajectory replay; without logs you cannot debug or
  evaluate.
- For prompt-injection risk (agents that process untrusted text): treat tool-call content
  extracted from external sources as untrusted; validate against expected shapes.

## Step 5: Context management

Long-running agents exhaust the context window. Apply in order:

1. **Return only what the next step needs.** Trim tool results aggressively; summarize
   large payloads (e.g., a 500-line file) before inserting into the thread.
2. **Compaction**: use the SDK's built-in compaction where available. For manual loops,
   periodically summarize the conversation history into a compressed system-level summary
   and drop intermediate turns.
3. **Subagents for heavy reads**: spawn a read-only subagent (Haiku-class, cheap) to scan
   large corpora and return a summary. The main agent sees only the summary, not the raw
   content. This is the ADLC pattern for architecture review and code analysis.
4. **Progress file**: for multi-session agents, write a `<task>-progress.md` at the repo
   root after each milestone (completed steps, next step, blockers). The next session
   reads this first instead of re-discovering state.

## Step 6: Evaluate agent trajectories

Do not ship an agent without a repeatable eval. Minimum two signals:

**Outcome metric**: did the agent achieve the intended goal? Define a deterministic
pass/fail oracle (test suite green, file diff matches expected, API response correct).

**Trajectory metric**: did the agent take a reasonable path? For each golden test case,
log the sequence of tool calls and check:
- No unnecessary or redundant tool calls (efficiency).
- No destructive tool called without prior read of the target (safety).
- Tool inputs conform to schema (correctness).
- Loop terminates within budget (liveness).

For the eval harness code template, see [references/agent-architecture-detail.md](../../references/agent-architecture-detail.md).

## Outbound checkpoint

Local work needs no approval. Anything outbound (publish, push, post) needs the operator's explicit per-action "yes"; see the global consent law.

## References

- Anthropic, "Building effective agents": https://www.anthropic.com/research/building-effective-agents
- Anthropic, "Writing tools for agents": https://www.anthropic.com/engineering/writing-tools-for-agents
- Anthropic, "Effective harnesses for long-running agents": https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents
- Anthropic, "Define tools -- tool use API": https://platform.claude.com/docs/en/docs/agents-and-tools/tool-use/implement-tool-use
- Anthropic, "Demystifying evals for AI agents": https://www.anthropic.com/engineering/evaluating-ai-agents
- Detail reference (grep commands, loop pseudocode, tier table, eval harness): [references/agent-architecture-detail.md](../../references/agent-architecture-detail.md)
