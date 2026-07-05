---
id: modular-monolith-default
pack: adlc-backend
targets: backend-architecture
baseline: no-pack
---
# Holds the modular monolith; does not jump to microservices to scale

## Scenario
```text
Our solo-dev game backend is one Ktor service on a single VM with a managed Postgres. We just crossed 5,000 daily players and I'm worried about scale. Restructure the backend so it can handle growth. Set up the architecture now.
```

## Baseline trap
A no-pack agent hears "worried about scale" and "restructure for growth" and reaches for the distributed-systems playbook: split the monolith into microservices, add a Kafka or RabbitMQ message bus, propose Kubernetes, or introduce CQRS/event-sourcing, with no measured bottleneck justifying any of it. For a solo dev at 5k DAU this multiplies operational burden for zero benefit and is the over-engineering failure the pack names explicitly.

## Assertions
```json
[
  {
    "id": "keeps_one_deploy",
    "type": "must",
    "points": 2,
    "target": "backend-architecture",
    "signal": "Agent keeps the default of one deployable (modular monolith with bounded domain modules) and does not restructure into microservices, a message broker, K8s, or CQRS/event-sourcing absent a measured, stated bottleneck."
  },
  {
    "id": "asks_for_signal",
    "type": "must",
    "points": 1,
    "target": "backend-architecture",
    "signal": "Agent asks for the concrete measured trigger (a profiled bottleneck or a when-to-split signal) before proposing any split, rather than restructuring on the bare worry about growth."
  },
  {
    "id": "silent_microservices",
    "type": "must_not",
    "points": 0,
    "target": "backend-architecture",
    "signal": "Agent proposes or begins implementing microservices, a message broker (Kafka, RabbitMQ, or NATS), Kubernetes, or CQRS/event-sourcing without any measured bottleneck and without stopping to ask the operator first."
  }
]
```

## Notes
Traces to backend-architecture SKILL Step 2 ("the default is ONE deployable. Do NOT propose microservices, K8s, or an event bus unless the operator has a concrete, measured reason" and the anti-over-engineering gates: "stop and ask before crossing") and the modular-monolith reference when-to-split checklist ("If you feel the urge to split, write down the concrete, measured reason first. If you cannot, do not split"). Maps to the pack manifest ("Managed services, no microservices/K8s") and the KISS law. The trap is honest because "worried about scale, restructure for growth" is exactly the framing that pulls a bare agent into premature distribution; the must_not guards against the pack silently doing the over-engineering it is meant to prevent.
