<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
Consumed by the `agent-architecture` skill. Load on demand; do not load independently.

## Step 2: Tool design rules (expanded)

**Name**: `service_resource_action` format (e.g., `github_pr_create`, `calendar_event_list`).
Prefix by service when tools span multiple systems. No ambiguous names like `update`.

**Description**: treat it as onboarding documentation. Include: what it does, when to use
it (and when NOT to), what each parameter means, caveats, and what it returns.
Minimum 3-4 sentences. Vague descriptions are the primary cause of agent errors.

**Schema**: typed JSON Schema, `required` array explicit, enums for fixed-value params,
UUIDs/slugs over opaque internal IDs. Never accept arbitrary `object` or `any`.

**Least-privilege**: give the agent only the tools its current task requires. Destructive
or outbound tools (write, delete, post, push, send) require a separate HITL approval step (Step 4).
Read-only tools need no approval step.

**Response shaping**: return only high-signal fields. Bloated responses consume context
and force the model to extract what matters. Add an optional `verbosity` param if the
agent sometimes needs full detail.

**Consolidation**: group related operations under one tool with an `action` enum
(e.g., `issue_manage` with `action: create|update|close`) rather than N separate tools.
Fewer, clearer tools outperform large, ambiguous tool surfaces.

## Step 1: Detect-first grep commands

Run these before designing anything. Record: framework, existing tool schema format, loop
implementation, any HITL checkpoints. Mark anything you cannot determine `unknown`; ask
before inventing.

```bash
# Existing tool/function definitions
grep -rIln --include="*.py" --include="*.ts" --include="*.kt" \
  -e 'tool_use' -e 'function_call' -e '"tools"' -e 'ToolDefinition' . | head

# Existing agent loop or SDK runner
grep -rIln --include="*.py" --include="*.ts" \
  -e 'while.*stop_reason' -e 'tool_runner' -e 'AgentLoop' \
  -e 'run_agent' -e 'agentic_loop' . | head

# Framework in use (LangChain, LlamaIndex, raw SDK, etc.)
grep -rIl --include="*.py" --include="*.ts" \
  -e 'from langchain' -e 'from llama_index' -e 'anthropic' -e '@anthropic-ai' . | head

# Human-in-the-loop or approval checkpoints
grep -rIln --include="*.py" --include="*.ts" \
  -e 'human_approval' -e 'require_confirmation' -e 'interrupt' . | head
```

## Step 3: Loop patterns

**Manual loop** (raw SDK, more control):

```
send message + tools ->
  response.stop_reason == "tool_use" ?
    execute each tool_use block ->
    append tool_result blocks ->
    repeat
  : done
```

Use when you need custom error handling, per-tool logging, rate-limit back-off, or
mid-loop HITL gates.

**SDK tool runner** (Anthropic SDK `tool_runner` / similar):

```
client.messages.run_with_tools(messages, tools, executor)
```

Use when the loop is straightforward and you want less boilerplate. Check the `claude-api`
skill for the current SDK API surface.

**ADLC in-house pattern**: the ADLC orchestration uses the manual loop and stops to ask
the operator for an explicit yes before any outbound/destructive call. Mirror this pattern
for any agent that touches external systems.

## Step 4: Tool risk tier table

| Tier | Examples | Control |
|---|---|---|
| Read-only | search, read, list, get | None; run freely |
| Idempotent write | upsert, set preference | Log; surface to user after |
| Destructive / outbound | delete, push, send, post, publish | Stop; require explicit approval before execution |

## Step 6: Eval harness shape

```python
golden_cases = [
  { "task": "...", "expected_outcome": ..., "forbidden_tools": [...], "max_turns": 10 }
]
for case in golden_cases:
    trajectory = run_agent(case["task"], log=True)
    assert outcome_oracle(trajectory.final_output, case["expected_outcome"])
    assert trajectory.turns <= case["max_turns"]
    assert not any(t in trajectory.tool_calls for t in case["forbidden_tools"])
```

Build at least 10 golden cases before shipping. Re-run on every prompt, tool schema, or
loop logic change. An agent that passes outcome but not trajectory is brittle.
