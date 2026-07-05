---
id: exact-money-and-time-types
pack: adlc-database
targets: schema-design
baseline: no-pack
---
# Schema design: money is NUMERIC and time is TIMESTAMPTZ, with constraints in the schema

## Scenario
```text
Design the `payments` table for our Postgres app: it needs an amount, a currency, a status (one of pending, settled, refunded), the customer it belongs to, and when it was created. Give me the CREATE TABLE.
```

## Baseline trap
A no-pack agent reaches for convenient-looking types: `amount FLOAT` (or REAL / double precision, which loses cents on binary rounding), `created_at TIMESTAMP` without a zone (drops the offset and breaks across regions), `status TEXT` with no constraint, and often no foreign key or CHECK. It produces a table that compiles but silently corrupts money and admits invalid rows, because those types are the first ones that come to mind.

## Assertions
```json
[
  {
    "id": "numeric_money",
    "type": "must",
    "points": 2,
    "target": "schema-design",
    "signal": "The amount column is NUMERIC / DECIMAL (not float / double / real), stated as the money type."
  },
  {
    "id": "timestamptz",
    "type": "must",
    "points": 1,
    "target": "schema-design",
    "signal": "The created-at column is TIMESTAMPTZ (timezone-aware) rather than a plain zone-less TIMESTAMP."
  },
  {
    "id": "constraints_in_schema",
    "type": "must",
    "points": 2,
    "target": "schema-design",
    "signal": "The schema pushes invariants into the table: a primary key, a foreign key to customer with an explicit ON DELETE rule, and a CHECK or lookup constraining status to the allowed set, rather than leaving them to application code."
  },
  {
    "id": "verify_constraint_bites",
    "type": "must",
    "points": 1,
    "target": "schema-design",
    "signal": "Agent proposes applying the schema to a real/test DB and proving a constraint bites (inserting a bad row and asserting rejection) as the failable check, not just returning DDL."
  }
]
```

## Notes
Verified against schema-design Step 4 (money is NUMERIC/DECIMAL, 'Never float or double for money; binary floats lose cents'; Postgres timestamps use TIMESTAMPTZ, 'plain TIMESTAMP drops the zone and breaks across regions'; bounded categories via 'CHECK ... IN (...)' or a lookup table), Step 3 ('Push every invariant you can into the schema': NOT NULL, UNIQUE, FOREIGN KEY 'with an explicit ON DELETE rule', CHECK, 'PRIMARY KEY on every table, always'), and Step 6 (the failable check: apply the schema and 'prove one constraint bites: insert a row that violates... and assert the database rejects it'). Read-only design work returning DDL, with no outbound or destructive surface, so must assertions only, per eval-format self-test bullet 4. Baseline is honest: a bare agent routinely defaults amount to FLOAT and created_at to zone-less TIMESTAMP and omits the CHECK/FK, exactly the silently-wrong shape the skill exists to prevent; the FK + status-CHECK + TIMESTAMPTZ combination keeps the delta honest even if a strong bare agent happens to pick NUMERIC.
