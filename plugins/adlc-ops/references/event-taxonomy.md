<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
# Event taxonomy: naming, schema, and core metrics

Reference for the `product-analytics` skill. Keep this file alongside the skill and update it when the naming convention or metric definitions change.

---

## Naming convention

```
<feature>_<object>_<action>
```

- All lowercase, `snake_case`, past tense for user-initiated events.
- Feature prefix scopes the event to a product area; prevents collision as the product grows.
- Object is the thing acted on; action is what happened.

| Good | Bad | Why |
|---|---|---|
| `onboarding_tutorial_completed` | `tutorialDone` | no feature prefix, camelCase |
| `store_item_purchased` | `purchase` | too vague; not scoped |
| `game_level_failed` | `level_fail_2025-06-20` | dynamic data in the name |
| `settings_notifications_toggled` | `notificationsToggle` | camelCase, no feature |

**Global properties** (send on every event, set by the SDK layer, never by callsite):

| Property | Type | Notes |
|---|---|---|
| `schema_version` | int | bump on any meaning change to the event |
| `app_version` | string | semver string, e.g. `"1.4.2"` |
| `platform` | enum | `ios`, `android`, `pc`, `webgl` |
| `session_id` | string | short-lived random ID for session grouping; NOT a user identifier; rotate each session |
| `pii` | literal `"none"` | explicit per-event assertion |

Never put `user_id`, `device_id`, `advertising_id`, email, or any persistent cross-session join key in an event property. Cross-reference the telemetry skill and adlc-privacy for the full ban list.

---

## Typed event schema template

Document every event before instrumenting it. Store schemas in code comments (KDoc / Swift doc), a tracking plan doc, or a registry file. Either format is fine; what matters is that the schema is reviewable.

```yaml
event:   <feature>_<object>_<action>
trigger: <one sentence: when exactly this fires>
params:
  <param_name>:
    type:    enum | bucket | bool | literal
    values:  [<exhaustive list>]            # enum: include an "other"/"unknown" tail
    # OR
    buckets: [<0, 1-5, 6-10, 11+>]         # numeric: always bucketed, suffix _b
    notes:   <optional context>
schema_version: 1
pii: none
```

Evolve additively: add new params with a new `schema_version`; never redefine an existing param in place. To rename, emit both names for one release, then drop the old one.

---

## Core product metrics

### Universal (apps + games)

| Metric | Definition | Instrumentation source |
|---|---|---|
| DAU | Unique sessions in a calendar day | count distinct `session_id` per day |
| MAU | Unique sessions in a calendar month | same, monthly window |
| DAU/MAU ratio | Stickiness; healthy range: 20-30% for games | derived |
| Session length | Time from session start to end event | `session_started` + `session_ended` events, bucketed |
| Retention D1/D7/D30 | % users who return on day 1/7/30 after first open | cohort query on `app_opened` events |
| Feature funnel | % users completing each step of a flow | ordered sequence of step events |
| Conversion | % users who reach a target action (purchase, upgrade) | target event / cohort |

### Game-specific

| Metric | Definition | 2025 industry benchmark (GameAnalytics) |
|---|---|---|
| D1 retention | % who return day after install | top 25%: 31-33% iOS, 25-27% Android; average: ~27% |
| D7 retention | % who return 7 days after install | top 25%: 7-8%; average: ~4% |
| D30 retention | % who return 30 days after install | average: <3%; top 25%: ~5-7% |
| ARPDAU | Average revenue per daily active user | varies heavily by genre/monetisation model |
| Session frequency | Sessions per active user per day | median: ~4; mid-core: 6-7 |
| Level/chapter completion rate | % players reaching each milestone | per-level `game_level_completed` events |
| IAP conversion | % DAU who make an in-app purchase | `store_item_purchased` / DAU |

Instrument D-retention via a cohort query: first `app_opened` per user defines the install cohort date; returning opens on D+1, D+7, D+30 define retention. No need for a dedicated "retention event" -- `app_opened` with `session_id` rotation is sufficient.

---

## Schema validation (recommended tooling)

For solo-scale, a lightweight approach is sufficient:

1. Keep a `tracking-plan.yaml` (or markdown table) in the repo documenting every event + schema.
2. Write a CI lint step that confirms every `track()` call in source matches a schema entry (a simple grep/ast check is enough to start).
3. If using Amplitude: use the Data (formerly Govern) feature to lock event schemas and flag unplanned events.
4. If using Mixpanel: use Lexicon to document and lock property types.
5. If using a custom backend or Snowplow: use Iglu-style JSON Schema versioning (SchemaVer MAJOR.MINOR.PATCH).

The validation loop: new event -> add to tracking plan -> PR review of schema entry -> instrument -> CI check passes.

---

## References

- Amplitude, "Event taxonomy": https://amplitude.com/explore/data/event-taxonomy
- GameAnalytics, "2025 Mobile Gaming Benchmarks": https://www.gameanalytics.com/reports/2025-mobile-gaming-benchmarks
- Snowplow, "Versioning your schemas" (SchemaVer): https://docs.snowplow.io/docs/fundamentals/schemas/versioning/
- Amplitude, "Measurement vs. Metrics": https://amplitude.com/blog/measurement-metrics
- Digital Applied, "Product Analytics: An Event Taxonomy That Won't Rot": https://www.digitalapplied.com/blog/product-analytics-event-taxonomy-tracking-plan-2026
