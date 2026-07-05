---
id: measure-before-index-and-paginate
pack: adlc-database
targets: query-optimization
baseline: no-pack
---
# Query optimization: read the plan before indexing and use keyset over deep OFFSET

## Scenario
```text
Our GET /orders endpoint is slow. It runs `SELECT * FROM orders WHERE customer_id = $1 ORDER BY created_at DESC LIMIT 20 OFFSET $2` on Postgres and users report it crawls on later pages. Speed it up.
```

## Baseline trap
A no-pack agent guesses at the fix without ever getting the query plan: it slaps an index on `customer_id` (or blindly CREATE INDEX several columns), keeps the deep OFFSET pagination that is the actual cause of the late-page slowness, and declares it faster with no before/after measurement. It optimizes on intuition, not on EXPLAIN, and never addresses that OFFSET reads and discards N rows.

## Assertions
```json
[
  {
    "id": "reads_explain_first",
    "type": "must",
    "points": 2,
    "target": "query-optimization",
    "signal": "Agent gets and reads the query plan (EXPLAIN / EXPLAIN ANALYZE) to locate the real cost before proposing an index, rather than guessing an index from the column names."
  },
  {
    "id": "keyset_pagination",
    "type": "must",
    "points": 2,
    "target": "query-optimization",
    "signal": "Agent replaces deep OFFSET with keyset/seek pagination (carry the last row's created_at,id and filter past it) as the fix for the slow later pages, not just an added index."
  },
  {
    "id": "before_after_measure",
    "type": "must",
    "points": 1,
    "target": "query-optimization",
    "signal": "Agent captures a before/after measurement or a plan assertion (a latency number or Seq Scan to Index/Index-Only Scan) as the evidence the change worked, rather than asserting it is faster."
  },
  {
    "id": "index_matches_pattern",
    "type": "must",
    "points": 1,
    "target": "query-optimization",
    "signal": "Any index the agent adds is a composite ordered for the real access pattern (equality on customer_id then the created_at,id sort), not a single-column guess on an unrelated column."
  }
]
```

## Notes
Verified against query-optimization Step 2 ('Read the plan, do not guess': get EXPLAIN (ANALYZE, BUFFERS) and read it for the Seq Scan tell), Step 5 ('Paginate large sets with keyset, not OFFSET': OFFSET reads and discards n rows so deep pages degrade to O(n); carry the last row's sort key, with the exact (created_at DESC, id DESC) tuple-comparison example), Step 3 (composite column order: equality first then the sort column), and Step 6 ('Measure before and after, prove the win': record both numbers, for example 'p95 420ms to 18ms, Seq Scan to Index Only Scan'). Read-only optimization work with no destructive or outbound surface, so must assertions only, consistent with eval-format self-test bullet 4 which requires a must_not only where the pack touches that surface. Baseline is honest: a bare agent commonly adds an index and leaves OFFSET in place, missing the real cause and shipping without a number.
