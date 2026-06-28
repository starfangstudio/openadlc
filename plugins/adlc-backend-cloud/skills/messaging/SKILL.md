---
name: messaging
description: >-
  This skill should be used when the user asks to "add async messaging", "publish events", "set up a
  message queue", "produce/consume Kafka", "consume from a topic", "add a stream processor", "make a
  consumer idempotent", "dedupe messages", "handle duplicate deliveries", "guarantee ordering", "add a
  partition key", "add backpressure", "add a dead-letter queue", "handle poison messages", "implement
  the transactional outbox", "get exactly-once effects", "publish events atomically with a DB write",
  "stop double-charging on retries", or wires any broker (Kafka, Pulsar, SQS, RabbitMQ, NATS JetStream)
  for events or streaming. Detect-first across brokers. Designs at-least-once delivery with idempotent
  consumers (dedupe keys), ordering via partition keys, backpressure, dead-letter queues, and the
  transactional outbox for exactly-once effect. Routes observability/alerting to adlc-ops, broker auth
  and payload signing to adlc-security, and event/table schema modeling to adlc-database.
version: 0.1.0
---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# messaging

Async messaging and streaming for a team/scale backend: pick the broker the project already uses, accept
at-least-once delivery as the default, and make every consumer idempotent. Ordering rides partition keys,
overload is handled with backpressure, failures go to a dead-letter queue, and atomic "DB write + publish"
uses the transactional outbox. Exactly-once delivery does not exist end-to-end; exactly-once *effect*
does, and it is built on the consumer side.

## Step 1: Detect the broker first -- never impose

Inspect the project before adding anything. Name the broker, the client library, and where producers and
consumers already live. If a broker is already present, extend it; do NOT introduce a second one.

```bash
# Broker + client library
grep -rn "kafka\|KafkaProducer\|KafkaConsumer\|confluent\|rdkafka\|sarama\|kafkajs" \
    . --include="*.kt" --include="*.java" --include="*.go" --include="*.ts" \
    --include="*.py" --include="*.gradle*" --include="*.toml" --include="package.json" 2>/dev/null | head
grep -rn "pulsar\|PulsarClient" . --include="*.*" 2>/dev/null | head
grep -rn "sqs\|SendMessage\|ReceiveMessage\|@aws-sdk/client-sqs\|boto3.*sqs" . --include="*.*" 2>/dev/null | head
grep -rn "amqp\|rabbitmq\|RabbitTemplate\|pika\|amqplib" . --include="*.*" 2>/dev/null | head
grep -rn "nats\|jetstream\|JetStream" . --include="*.*" 2>/dev/null | head

# Existing producers / consumers / topic names
grep -rn "produce\|publish\|subscribe\|consume\|@KafkaListener\|@RabbitListener" . 2>/dev/null | head

# Is there already an outbox?
grep -rn "outbox\|transactional_outbox\|relay\|debezium" . --include="*.sql" --include="*.kt" \
    --include="*.ts" --include="*.go" 2>/dev/null | head
```

Record: broker (name it), client library, language/runtime, existing topics/queues, whether an outbox or
CDC (Debezium) pipeline already exists. Mark anything unclear `unknown` and ask before guessing.

## Step 2: Pick delivery semantics honestly

Default to **at-least-once**: the broker may deliver a message more than once (consumer crash before ack,
rebalance, retry). The cheaper alternative, at-most-once, drops messages on failure and is almost never
what a business event wants.

Do not promise end-to-end "exactly-once". What you can deliver:
- **Exactly-once *effect*** = at-least-once delivery + an idempotent consumer (Step 3). This is the target.
- **Kafka exactly-once *semantics* (EOS)** exists only for the Kafka-to-Kafka read-process-write loop
  (idempotent producer + transactions, `isolation.level=read_committed`). It does NOT extend to an
  external DB or a third-party API call. The moment a side effect leaves Kafka, you are back to
  idempotent-consumer territory. Use the outbox (Step 6), not a claim of EOS.

State the chosen semantics in the code/PR. "Looks fine in a happy-path test" is not a delivery guarantee.

## Step 3: Make the consumer idempotent (dedupe keys)

Redelivery is not an error case, it is the contract. Every consumer MUST produce the same outcome when it
sees the same message twice.

1. **Stable message id.** Use a producer-set business id (e.g. `order_id`, `payment_id`) or the broker
   message id. Do NOT key on arrival time or a random per-delivery id.
2. **Dedupe store.** Keep a `processed_messages(message_id PRIMARY KEY, processed_at)` table. Process and
   record the id in the **same DB transaction** as the side effect, then ack the broker. Order:
   begin tx -> apply effect -> `INSERT ... ON CONFLICT (message_id) DO NOTHING` -> commit -> ack.
   On a duplicate, the insert is a no-op and the effect is skipped.
3. **Or natural idempotency.** When the effect is itself a guarded write (`UPDATE ... WHERE status =
   'pending'`, an upsert, a `DO NOTHING`), you may not need a separate dedupe table. Prefer this when it
   fits; it is one fewer moving part.

Ack only after the effect is durable. Acking before the work commits turns a crash into a lost message.
Never ack-then-process.

## Step 4: Ordering via partition keys

Ordering is per partition/group, never global, and only holds when one consumer owns that key at a time.

- **Kafka / Pulsar:** set the partition key to the entity whose order matters (`userId`, `accountId`).
  Same key -> same partition -> in-order. Different keys parallelize freely. Do not over-key (one global
  key serializes the whole topic and kills throughput); do not under-key (per-event random keys give zero
  ordering).
- **SQS FIFO:** `MessageGroupId` is the ordering+parallelism unit; one group is processed in order.
  `MessageDeduplicationId` (or `ContentBasedDeduplication`) gives broker-side dedupe within a 5-minute
  window. Still keep the Step 3 consumer dedupe: the 5-minute window is not a durable guarantee.
- **RabbitMQ:** ordering holds only on a single queue with a single consumer and `prefetch=1`. Concurrency
  and requeue-to-tail both break order; if you truly need ordering, shard by routing key into per-entity
  queues.
- **NATS JetStream:** ordering is per subject within a stream; an ordered consumer or per-subject
  partitioning preserves it.

If a feature does not actually need ordering, do not pay for it. Most event consumers only need
idempotency, not order.

## Step 5: Backpressure and dead-letter queues

**Backpressure** keeps a slow consumer from being buried or OOM-killed:
- Bound in-flight work: Kafka `max.poll.records` + manual commit, SQS long-poll with a small batch,
  RabbitMQ `prefetch` (QoS), Pulsar `receiverQueueSize`, NATS `MaxAckPending`. Tune so one poll's worth of
  work finishes inside the visibility/ack window.
- Pause/resume (or stop polling) when a downstream dependency is failing or rate-limiting, rather than
  spinning retries that amplify the outage.
- Make the ack/visibility timeout longer than the realistic processing time, or the broker redelivers
  in-flight messages and you create your own duplicate storm.

**Dead-letter queue (DLQ)** quarantines poison messages (a malformed or permanently-failing message that
would otherwise block the partition forever) after a bounded number of attempts:
- **SQS:** redrive policy on the source queue, `maxReceiveCount` (e.g. 5) -> DLQ. A FIFO queue's DLQ must
  also be FIFO.
- **Kafka:** no native DLQ; on terminal failure publish the record (plus failure metadata) to a
  `<topic>.DLT` topic and commit the offset so the partition advances. Kafka Connect and Spring Kafka
  provide this out of the box.
- **RabbitMQ:** set `x-delivery-limit` on a quorum queue (poison-message handling) plus a dead-letter
  exchange; `nack`/`reject` with `requeue=false` routes to the DLX.
- **Pulsar:** `DeadLetterPolicy(maxRedeliverCount=N, deadLetterTopic=...)` on a Shared/Key_Shared
  subscription; use `reconsumeLater` with retry enabled so the redelivery count is persisted and the DLQ
  is actually reached.
- **NATS JetStream:** cap with `MaxDeliver`; on `AckTerm` or max-deliveries, capture the
  `$JS.EVENT.ADVISORY.CONSUMER.MAX_DELIVERIES.*` / `MSG_TERMINATED` advisory and republish to a DLQ
  stream.

A DLQ is a parking lot, not a fix. Pair it with a redrive/replay path and route DLQ-depth alerting to
adlc-ops. Never silently `catch` and drop a failed message; that is a Blocking finding.

## Step 6: Transactional outbox for atomic write-and-publish

Do NOT write to the DB and publish to the broker as two independent calls. Either can fail after the
other succeeds (no shared transaction), which silently drops or duplicates events ("dual-write" problem).

The outbox pattern makes it atomic:
1. In the **same DB transaction** as the business write, insert a row into an `outbox` table
   (`id`, `aggregate_id`, `event_type`, `payload`, `created_at`, `published_at NULL`). One transaction,
   both rows commit or neither does.
2. A separate **relay** publishes unpublished rows to the broker and marks them published. Either poll the
   table (`SELECT ... WHERE published_at IS NULL ORDER BY created_at FOR UPDATE SKIP LOCKED`) or use CDC
   (Debezium tailing the WAL). Partition by `aggregate_id` so per-aggregate order is preserved.
3. The relay is **at-least-once** (it may publish then crash before marking the row), so the publish step
   re-emits on restart. That is fine precisely because Step 3 made consumers idempotent. The dedupe key is
   the outbox row id / event id.

Outbox gives exactly-once *effect* across a DB and a broker without distributed transactions (2PC).
Use it whenever an event must reflect a committed state change. Event payload and table schema design
(columns, indexes, partitioning, migrations) belong to adlc-database, not here.

## Step 7: Verify (pass/fail)

The failable check is a **consumer test**, not a happy-path smoke. Do not mark done without all of these
passing (use an in-memory/embedded broker or a Testcontainers/localstack instance):

1. **Happy path:** publish one message; consumer applies the effect once; offset/message is acked.
2. **Idempotency under redelivery:** deliver the *same* message id twice (simulate a pre-ack crash or
   replay); assert the side effect ran exactly once (one row / one charge / one email), the dedupe insert
   on the second pass is a no-op, and no error is thrown.
3. **Poison message -> DLQ:** feed a message that always fails; assert it is retried up to the limit, then
   lands in the DLQ (or `.DLT` topic) with failure metadata, and that it does NOT block subsequent good
   messages on the same partition/group.
4. **Outbox (if used):** roll back the business transaction; assert no outbox row and therefore no
   published event (no orphan event from a rolled-back write).

A messaging consumer with no idempotency-under-redelivery test and no poison-message-DLQ test is not done.

## Outbound checkpoint

Local work (writing producers/consumers, running an embedded or Testcontainers broker, local tests) is
unrestricted. Outbound here -- creating a topic/queue/DLQ in a managed broker (MSK, Confluent Cloud, SQS,
RabbitMQ/Pulsar cloud), publishing to a shared/staging/production broker, registering a schema in a
shared registry, or deploying a relay/consumer -- stops and asks the operator for an explicit yes: present
exactly what would go out and wait for the "yes" (global consent law).

## Stay in lane (route the rest)

- **Observability** (consumer-lag metrics, DLQ-depth alerts, tracing across producer/consumer,
  dashboards): `adlc-ops`. This skill names *what* to alert on, not the alerting stack.
- **Security** (broker authn/authz and ACLs, TLS/mTLS, payload signing/encryption, secret handling,
  untrusted-payload validation): `adlc-security`.
- **Data modeling** (event/outbox table schema, indexes, partitioning strategy, migrations, query depth):
  `adlc-database`.
- **Background jobs / cron / IAP webhooks** at solo scale: `adlc-backend` (`background-jobs`). This skill
  is the team/scale broker step up, not the default.

## References

- Confluent: Exactly-Once Semantics in Apache Kafka --
  https://www.confluent.io/blog/exactly-once-semantics-are-possible-heres-how-kafka-does-it/
- Kafka docs: idempotent producer + transactions (`enable.idempotence`, `transactional.id`,
  `isolation.level`) -- https://kafka.apache.org/documentation/#semantics
- microservices.io: Transactional Outbox pattern --
  https://microservices.io/patterns/data/transactional-outbox.html
- Debezium: Outbox Event Router --
  https://debezium.io/documentation/reference/stable/transformations/outbox-event-router.html
- AWS: Amazon SQS dead-letter queues + `maxReceiveCount` redrive --
  https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-dead-letter-queues.html
- AWS: SQS FIFO `MessageGroupId` and `MessageDeduplicationId` --
  https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/using-messagededuplicationid-property.html
- RabbitMQ: Dead Letter Exchanges + quorum-queue `x-delivery-limit` (poison handling) --
  https://www.rabbitmq.com/docs/dlx
- Apache Pulsar: dead letter topic + `DeadLetterPolicy(maxRedeliverCount)` and negative acknowledgement --
  https://pulsar.apache.org/docs/next/concepts-messaging/
- NATS JetStream: consumers, `MaxDeliver`, `MaxAckPending`, and `MAX_DELIVERIES` advisory for DLQ --
  https://docs.nats.io/nats-concepts/jetstream/consumers
