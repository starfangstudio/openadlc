---
name: product-analytics
description: >-
  This skill should be used when the user asks to "design analytics", "set up
  event tracking", "add product metrics", "build a funnel", "measure retention",
  "track DAU/MAU", "instrument a feature", "design an event schema", "name
  analytics events", "track game retention", "measure D1/D7/D30", "measure
  ARPDAU", "build a tracking plan", "set up Amplitude", "set up Mixpanel",
  "set up GameAnalytics", "validate analytics events", or "what events should
  I track". Covers event taxonomy design, typed event schemas with versioning,
  privacy-safe instrumentation (no PII), core product and game metrics
  (funnels, retention cohorts, DAU/MAU, D1/D7/D30, ARPDAU, conversion), and
  a deliberate "measure decisions, not everything" philosophy. Defers emission
  privacy doctrine to the telemetry-privacy skill (adlc-core); defers test
  strategy to adlc-testing; defers the deploy gate to adlc-quality-gates.
version: 0.1.0
---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# Product analytics

Analytics is an engineering discipline: a deliberate decision about what to
measure, expressed as a typed, versioned schema, implemented with the minimum
events needed to answer the questions you will actually act on.

## Detect first

Inspect the project before designing anything:

```bash
# Is an analytics SDK already wired?
grep -r "Amplitude\|Mixpanel\|GameAnalytics\|Firebase\|Snowplow\|Segment" \
  --include="*.swift" --include="*.kt" --include="*.cs" -l

# Is a tracking plan / event registry already present?
find . -name "tracking-plan*" -o -name "events.*" -o -name "*analytics*schema*" | head -10
```

Record: SDK in use (or `unknown`), existing event names, and whether a
tracking plan exists. Mark anything not found `unknown`. Never invent event
names or assume an SDK is configured.

## Design before you instrument

Start with the decisions, not the data:

1. Write the question you need to answer ("Is the tutorial too hard?").
2. Identify the decision you will make based on the answer ("Shorten step 3 if
   completion rate <40%").
3. Derive the minimum event(s) that answer it (`onboarding_tutorial_step_completed`,
   `onboarding_tutorial_abandoned`).

Do not instrument everything "for later." Uninstrumented events cost nothing;
events you track but never query add schema debt and leak surface area.

## Event taxonomy and schema

Follow the naming convention and schema template in
[references/event-taxonomy.md](references/event-taxonomy.md).

Core rules (non-negotiable):

- Name: `<feature>_<object>_<action>`, lowercase `snake_case`, past tense.
- No dynamic data in event names. Dynamic values go in properties.
- Every numeric property is bucketed (suffix `_b`); never a raw count or
  duration.
- Every enum property is closed (exhaustive list, `other`/`unknown` tail).
- Every event carries `schema_version` (int), `app_version`, `platform`,
  `session_id` (short-lived, non-persistent). Set these in the SDK layer, not
  at each callsite.
- State `pii: none` explicitly on every event definition. This forces review.
- Cross-check every property against the ban list in the `telemetry-privacy` skill
  (adlc-core) before instrumenting.

## Core metrics to instrument (by product type)

For full detail and 2025 game benchmarks, see
[references/event-taxonomy.md](references/event-taxonomy.md).

**Universal (apps + games):**

| Metric | Minimum events needed |
|---|---|
| DAU/MAU | `app_opened` (one per session, with `session_id`) |
| Session length | `session_started` + `session_ended` (timestamp diff, bucketed) |
| D1/D7/D30 retention | `app_opened` cohorted by first-open date |
| Feature funnel | one event per step, same feature prefix |
| Conversion | target event (e.g. `store_item_purchased`) |

**Game-specific (add these when shipping a game):**

| Metric | Minimum events needed |
|---|---|
| Level completion/drop-off | `game_level_started`, `game_level_completed`, `game_level_failed` |
| D1/D7/D30 (game context) | `app_opened` + cohort analysis (no extra event needed) |
| ARPDAU | `store_item_purchased` with `amount_usd_b` (bucketed), divided by DAU |
| IAP conversion | `store_item_purchased` / DAU |
| Session frequency | `session_started` count per user per day |

Instrument `app_opened` early and correctly: first occurrence per user defines
the install-cohort date; all retention cohort math derives from it.

## Schema versioning and validation

Before merging any new or changed event:

1. Add or update the event entry in the tracking plan (a `tracking-plan.yaml`
   or table in the repo).
2. Bump `schema_version` on the event definition.
3. Run the CI lint check (a grep/AST check confirming every `track()` call has
   a matching schema entry).
4. If using Amplitude Data or Mixpanel Lexicon: lock the schema there to flag
   unplanned events.

Validator loop: schema entry added -> PR reviewed -> `track()` call merged ->
CI lint passes. If CI lint fails, fix the schema entry or remove the
uninstrumented call; do not skip.

## Defer these to other skills

- **Emission privacy / PII ban list:** `telemetry-privacy` skill (adlc-core).
  Do not re-derive the privacy rules here; cross-check against it.
- **Mobile build / store delivery:** `android-build-commands`,
  `ios-build-commands`, and the store skills.
- **Test strategy:** `adlc-testing`.
- **Deploy readiness gate:** `adlc-quality-gates` (`gate-deployment-readiness`).

## Outbound approval

Local work needs no approval. Outbound here (enabling a new collection endpoint, configuring an SDK to send data to a live remote service, provisioning a paid analytics plan, or shipping an app build that fires events to a production backend): stop and ask the operator for an explicit yes. Present exactly what would go out and wait for the yes before doing it (global consent law).

## References

- [references/event-taxonomy.md](references/event-taxonomy.md) -- naming convention,
  typed schema template, core game/app metric definitions, 2025 benchmarks.
- Amplitude, "Event taxonomy": https://amplitude.com/explore/data/event-taxonomy
- Amplitude, "Measurement vs. Metrics": https://amplitude.com/blog/measurement-metrics
- GameAnalytics, "2025 Mobile Gaming Benchmarks":
  https://www.gameanalytics.com/reports/2025-mobile-gaming-benchmarks
- Snowplow, "Versioning your schemas" (SchemaVer):
  https://docs.snowplow.io/docs/fundamentals/schemas/versioning/
- Digital Applied, "Event Taxonomy That Won't Rot":
  https://www.digitalapplied.com/blog/product-analytics-event-taxonomy-tracking-plan-2026
