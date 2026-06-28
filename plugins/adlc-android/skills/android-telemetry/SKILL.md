---
name: android-telemetry
description: >-
  This skill should be used when adding, editing, or reviewing any Android
  analytics / pixel / telemetry / event call: no PII, no URLs or domains, bucket
  numerics, bound enums, version and document every event schema. Triggers
  include "add a pixel", "log an event", "analytics call", "telemetry", "wide
  event", "is this event privacy-safe", "review this pixel", or wiring up any
  analytics/metrics SDK that sends data off device.
version: 0.1.0
---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# Android telemetry privacy

For the platform-neutral doctrine (hard bans, bucketing, versioned schema, the
review gate), use the `telemetry-privacy` skill (adlc-core). This skill adds
only the Android specifics.

## KDoc and pixel registry

Document each pixel with KDoc on the pixel definition class or object. The
project's pixel registry is the source of truth for event names, param types,
and schema versions. Reviewers check the registry entry before approving any
new or changed pixel.

```kotlin
/**
 * Fired when the user completes the VPN connection flow.
 *
 * @param result    Outcome of the attempt.
 * @param count_b   Number of prior attempts in the session, bucketed.
 * @param source    Entry point from which the flow was triggered.
 * @schema_version  2
 * @pii             none
 */
object VpnConnectResultPixel : Pixel(
    name = "vpn_connect_result",
    params = listOf(RESULT, COUNT_B, SOURCE),
)
```

## Sealed class or enum for every dimension

Every bounded dimension must be a sealed class or enum in the production code,
not a raw string constant. This makes the type system enforce the closed set and
prevents typos from creating unplanned cardinality.

```kotlin
enum class VpnConnectResult(val value: String) {
    SUCCESS("success"),
    FAILURE("failure"),
    CANCELLED("cancelled"),
    OTHER("other"),        // tail bucket required
}
```

## Anonymous-metrics reference implementation

An anonymous-metrics model is the reference implementation for this approach:
one-pixel requests to a dedicated metrics host, an A/B bucket parameter,
short-lived random `journey.id`/`journey.name` for multi-step flows, and
`perf_id` performance buckets, with no unique cookies, no stored IP addresses,
and no PII embedded in any request. The bar: you cannot ever tell what individual
people are doing, since everyone is anonymous. Match that bar; do not add raw
values "just for debugging".

## Outbound checkpoint

Local work needs no approval. Outbound here (enabling a new collection endpoint, flipping telemetry on, shipping a new pixel/event to a live production endpoint): stop, present exactly what fields would leave the device, and wait for an explicit "yes" (global consent law).

## References

- Google Analytics, "Best practices to avoid sending Personally Identifiable
  Information (PII)", https://support.google.com/analytics/answer/6366371
