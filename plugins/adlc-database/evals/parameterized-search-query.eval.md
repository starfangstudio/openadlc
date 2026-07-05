---
id: parameterized-search-query
pack: adlc-database
targets: data-access
baseline: no-pack
---
# Data access: a user-driven search query is parameterized, never string-built

## Scenario
```text
Add a search endpoint to our repository layer: given a `name` string from the request query params, return matching customers. We use raw SQL through the `pg` driver in Node. Keep it simple.
```

## Baseline trap
A no-pack agent hears "raw SQL" plus "keep it simple" and builds the query by interpolating the request value straight into the SQL text (a template literal or "... WHERE name LIKE '%" + name + "%'"), which is a textbook SQL injection hole. It ships the concatenated path because it reads as the shortest working code, with no bound parameter and no note that the value came from outside.

## Assertions
```json
[
  {
    "id": "bound_parameter",
    "type": "must",
    "points": 2,
    "target": "data-access",
    "signal": "Agent passes the request value as a bound parameter (a $1 placeholder with a params array, or a tagged-template that binds it) rather than concatenating or interpolating it into the SQL text."
  },
  {
    "id": "names_injection_boundary",
    "type": "must",
    "points": 1,
    "target": "data-access",
    "signal": "Agent explicitly states that outside input must reach SQL as a parameter and never as string-built text (the injection boundary), rather than silently choosing the safe form."
  },
  {
    "id": "behind_repository",
    "type": "must",
    "points": 1,
    "target": "data-access",
    "signal": "Agent places the query behind a repository / data module with an intent-named method returning domain rows, rather than exposing a raw query(sql) call to the caller."
  },
  {
    "id": "ships_string_built_sql",
    "type": "must_not",
    "points": 0,
    "target": "data-access",
    "signal": "Agent ships a query where the request-supplied name is concatenated or interpolated into the SQL string (an unsafe / string-built path) instead of bound as a parameter."
  }
]
```

## Notes
Verified against data-access Step 3: 'User input reaches the database as a bound parameter, never as concatenated or interpolated text. This is the injection boundary and it ties directly to adlc-security'; it names the safe forms ($1 placeholder, tagged-template) and the banned ones ($queryRawUnsafe, string concatenation, f-strings), and states 'The rule is absolute: if a value came from outside, it is a parameter.' Step 2 keeps queries behind a typed repository with intent-named methods (findActiveUsersByTeam, not query(sql) from a service). The must_not is the injection safety floor the skill itself ties to adlc-security, guarding the unsafe surface per eval-format self-test bullet 4. Baseline is honest: a bare agent asked for raw SQL with 'keep it simple' commonly emits the interpolated form.
