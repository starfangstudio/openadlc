---
name: telemetry-privacy
description: >-
  This skill should be used when the user asks to add a pixel, log an event,
  wire an analytics call, add telemetry, add a wide event, review a pixel for
  privacy, instrument a feature, or wire any analytics or metrics SDK that sends
  data off device -- on ANY platform (Android, iOS, Unity, backend, web). Also
  triggers on "is this event privacy-safe", "add a tracking call", "instrument
  this with telemetry", or "analytics SDK setup". Enforces hard bans on PII and
  identifiers, bucketing rules for numerics, bounded enums with tail buckets,
  versioned schemas with an explicit pii:none assertion, and the ADLC outbound
  consent checkpoint (an explicit operator yes) for any new collection endpoint going to production.
version: 0.1.0
---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# Telemetry privacy

**If a field could, alone or joined with others, single out one user or session: it does not ship.**

Analytics events (pixels, wide events, telemetry) leave the device. Treat every
parameter as something a stranger will read.

## Detect first

Inspect before changing anything:

```bash
# Find the analytics SDK already in use
grep -r "Amplitude\|Mixpanel\|Firebase\|Snowplow\|Segment\|GameAnalytics" \
  --include="*.kt" --include="*.swift" --include="*.cs" \
  --include="*.ts" --include="*.py" -l

# Find the event or pixel registry
find . -name "tracking-plan*" -o -name "events.*" \
       -o -name "*analytics*schema*" -o -name "*pixel*registry*" | head -10
```

Record: SDK in use (or `unknown`), registry location (or `unknown`), existing
event names. Mark anything not found `unknown`. Never invent event names or
assume the SDK is configured.

## Hard bans: never put these in an event

- **PII and identifiers.** No email, phone, name, account or user id, device id,
  advertising id, IP address, or precise location (nothing finer than coarse
  region).
- **Free text.** No user input, search queries, form field values, error
  messages, exception messages, or stack traces. Send a bounded error code
  instead.
- **URLs, domains, hostnames, paths, or content package names.** A domain is an
  identifier; it reveals what the user browsed. Send a category or a boolean
  (`had_tracker: true`), never `example.com`.
- **High-cardinality raw values.** No timestamps to the second, no raw counts,
  no raw durations, no full version strings as free dimensions. Bucket them.
- **Cookies or any cross-request join key** that lets two events be tied to one
  user or session across requests.

## Required shape for what does ship

- **Bucket every numeric.** Map counts, durations, and sizes into a small fixed
  set of ranges, not the raw number. Example: `1-5`, `6-10`, `11-20`, `21+`.
  Latency: `<100ms`, `100-500ms`, `500ms-2s`, `2s+`. Bucket boundaries are part
  of the schema and must be documented. Use a `_b` suffix to signal bucketed.
- **Bound every enum.** A dimension has a closed, enumerated set of values
  defined in code (a typed or enumerated definition in the project's
  event/pixel registry). No open string dimensions; they leak free text and
  explode cardinality. Add an explicit `other`/`unknown` tail bucket.
- **Coarsen time and place.** Day granularity at most for dates; coarse region
  (country/locale), never a precise location, for place.
- **No unique-per-event values.** No request ids, UUIDs, or sequence numbers as
  parameters unless they are deliberately short-lived and documented as
  non-joinable.

## Every event needs a documented, versioned schema

Before adding an event, write its schema in the project's event/pixel registry:

```
event:  feature_action_result          // lowercase, stable, namespaced by feature
params:
  result:   enum { success, failure, cancelled }   // bounded
  count_b:  bucket  { 0, 1-5, 6-10, 11+ }           // bucketed numeric, _b suffix
  source:   enum { onboarding, settings, other }    // bounded, has tail bucket
schema_version: 2                                    // bump on any meaning change
pii: none                                            // explicit assertion, reviewed
```

- Name events stably, namespaced by feature (`vpn_connect_success`), lowercase,
  no spaces.
- Carry a `schema_version` (or equivalent) so downstream pipelines survive
  changes.
- Evolve additively: introduce a new param rather than redefining an existing
  one. To rename, emit both old and new for one release, then drop the old.
- State `pii: none` explicitly on each event; it forces the author and reviewer
  to look.

## Self-check review gate

For each new or changed event, confirm before merging:

1. No banned field (PII, free text, URL/domain, raw high-cardinality value) is
   present.
2. Every numeric is bucketed; every dimension is a bounded enum with a tail
   bucket.
3. Schema is documented and `schema_version` is set or bumped.
4. `pii: none` is asserted and true.

If any answer is no, the event does not merge. When unsure whether a field is
identifying, treat it as identifying; drop or bucket it.

## Outbound consent

Local work needs no approval. Outbound here (enabling a new collection endpoint, flipping telemetry on, shipping a new pixel to production): stop, present exactly what would go out, and wait for an explicit "yes" (global consent law).

## References

- Google Analytics, "Best practices to avoid sending Personally Identifiable
  Information (PII)": https://support.google.com/analytics/answer/6366371
