---
name: gdpr-engineering
description: >-
  This skill should be used when the user asks to "implement GDPR", "add DSAR
  endpoint", "build a right-to-erasure pipeline", "wire up data deletion", "set up
  data retention and deletion schedules", "create our ROPA", "add a DPA for this SDK",
  "implement do-not-sell for CCPA", "make the app CPRA-compliant", "audit what personal
  data we collect", "implement privacy by design", "add a data minimisation policy",
  "wire CCPA opt-out to our ad SDKs", "build a consent withdrawal flow", or "implement
  GDPR rights as code". Covers lawful basis per processing purpose, rights-as-code
  (DSAR export, erasure pipeline reaching all stores and processors), data retention
  and minimisation, ROPA from the real data map, privacy-by-design and by-default,
  DPA per processor/SDK, and CCPA/CPRA deltas. DEFERS store-submission mechanics to
  android-compliance / ios-store-compliance; consent banner UI to the consent-management
  skill; monetisation design to adlc-monetization; security (injection/authz) to
  adlc-security; analytics emission doctrine to the telemetry skill.
version: 0.1.0
---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# GDPR/CCPA engineering

This is engineering, not legal advice. Flag every borderline legal call as "confirm
with counsel for jurisdiction X". Mark any data flow you cannot verify as `unknown`;
never invent a "no collection" answer or assert a lawful basis without evidence.

## Detect first

Map what personal data the app actually processes before proposing any control. Run these
three patterns against the codebase root:

```bash
# Network calls that may send personal data off-device
grep -rEn "HttpURLConnection|OkHttpClient|Retrofit|URLSession|Alamofire|fetch\(" \
  --include="*.kt" --include="*.swift" --include="*.js" . | head -40

# SDK initialisations (analytics, ads, attribution, crash)
grep -rEn "Firebase|Amplitude|Segment|Braze|Adjust|AppsFlyer|AppLovin|ironSource|Crashlytics" \
  --include="*.kt" --include="*.swift" . | head -30

# User identifiers stored or transmitted
grep -rEn "userId|deviceId|IDFA|advertisingId|email|phone|ipAddress" \
  --include="*.kt" --include="*.swift" . | head -30
```

For each SDK found, look up its published data-collection disclosure. Mark any SDK whose
collection scope is unclear as `unknown`; resolve before shipping.

## Step 1: Assign lawful basis per processing purpose

For each row added to the ROPA, choose exactly one basis under GDPR Art. 6. Quick guide:
contract (Art. 6(1)(b)) for features the user signed up for; consent (Art. 6(1)(a)) for
optional analytics and ad targeting; legitimate interest (Art. 6(1)(f)) for security
logging with a Legitimate Interest Assessment; legal obligation (Art. 6(1)(c)) for tax
records, confirmed per jurisdiction. Never use "legitimate interest" as a catch-all; a
mismatch between stated basis and actual processing is a DPA inspection red flag. Full
basis table in [references/gdpr-engineering-detail.md](references/gdpr-engineering-detail.md) §B.

## Step 2: Data subject rights as code

Implement each right as a tested, audited endpoint. Full checklists and pipeline
patterns are in [references/gdpr-engineering.md](references/gdpr-engineering.md) §1.

**DSAR export (Art. 15 / CCPA §1798.110)**
- `POST /api/privacy/export` re-authenticates the requester, then queries every data
  store (primary DB, analytics, push tokens, support tickets, processor copies).
- Time-box the download URL (< 48 h). Log the request with timestamp and outcome.
- Deadline: 30 days GDPR / 45 days CCPA (extendable once to 90).

**Right to erasure (Art. 17 / CCPA §1798.105)**
- Emit a `DeleteRequested` event to an internal queue; each service subscribes,
  deletes/anonymises its records, and emits `DeleteConfirmed`.
- Orchestrator waits for all confirmations, then notifies each third-party processor
  and schedules a backup purge on the next retention cycle.
- Write an immutable deletion certificate to the audit log.
- Deadline: 30 days GDPR / 45 days CCPA. Confirm exceptions (legal obligation, fraud
  prevention) with counsel; never invent an exception to avoid deletion.

**Right to rectification (Art. 16)**: profile-edit flow that writes through to all
stores holding the field.

**Right to restriction/objection (Art. 18, 21)**: `processing_restricted` flag on the
user record; all analytics and marketing consumers must check it before processing.

## Step 3: Data minimisation + retention schedules

Collect less. Delete on schedule. Retain only what a documented purpose requires.

Retention patterns (see full table in [references/gdpr-engineering.md](references/gdpr-engineering.md) §2):
- Account PII: delete immediately on account deletion.
- Server logs with IP: 90 days, then delete/pseudonymise.
- Purchase records: 7 years (tax law; confirm jurisdiction with counsel).
- Analytics (user-level rows): 12 months, then aggregate and delete rows.

Run a scheduled purge job per data store. Log every run with row counts. Do not
apply retention periods to anonymised/aggregated data; it is no longer personal data.

## Step 4: ROPA, keep it current, not theoretical

The ROPA (Art. 30) is the first document a DPA requests on inspection. Build it from
the actual data map produced in Detect first, not from assumptions.

One row per processing purpose. Required fields per row (full template in
[references/gdpr-engineering.md](references/gdpr-engineering.md) §3):
purpose / lawful basis / data categories / data subjects / recipients / third-country
transfer mechanism / retention / security measures / DPA reference.

Update the ROPA every time a new SDK is added or a data flow changes. Version-control it.

## Step 5: DPA per processor/SDK

A Data Processing Agreement is required for every processor that receives personal
data (Art. 28): Firebase, Amplitude, Adjust, Stripe, cloud provider, support SaaS.

For each processor (full checklist in [references/gdpr-engineering.md](references/gdpr-engineering.md) §4):
- DPA signed and on file; covers sub-processors and change notification.
- Transfer mechanism for non-EU processors (SCCs / adequacy decision / BCRs).
- Processor contractually obligated to delete/export data on your request; test this.
- Reference added to the ROPA row for the activity.

## Step 6: Privacy by design + by default (Art. 25)

- Default settings must be the most privacy-preserving. Opt-in to analytics/ads; never
  opt-in by default.
- Collect the minimum data a feature needs at the point it is needed; no speculative
  collection for a future use case.
- Do not log or transmit personal data in debug builds; add lint rules / CI gates.
- Encrypt personal data at rest (AES-256) and in transit (TLS 1.2+). No PII in URLs
  (query params are logged by every CDN); use POST bodies or headers.

## Step 7: CCPA/CPRA deltas

Applies if the business meets any California threshold (confirm with counsel). For the
full threshold criteria, engineering requirements table, and GPC implementation detail,
see [references/gdpr-engineering-detail.md](references/gdpr-engineering-detail.md) §D.

Key controls to implement: honor the GPC signal automatically; block ad-attribution SDK
initialisation until Do-Not-Sell/Share signal is resolved; add a "Do Not Sell or Share"
control with no more steps than opt-in; add a separate "Limit Use of Sensitive PI"
control; visibly confirm opt-out was processed (required from Jan 1 2026); cease
sale/sharing within 15 business days of any valid opt-out request.

## Stop-and-verify checklist

Before calling a data flow GDPR/CCPA-ready, run the full checklist in
[references/gdpr-engineering-detail.md](references/gdpr-engineering-detail.md) §C. Every item must be
PASS; no FAIL or UNKNOWN may remain unresolved. Escalate to counsel before shipping.

## Outbound: get the operator's yes first

Local work is fine to do without asking. Outbound here (submitting a DSAR response or deletion confirmation to a data subject, publishing an updated privacy policy, responding to a supervisory authority inquiry, enabling an SDK that sends personal data off-device, opening a DPA with a new processor): stop, present exactly what would go out, and get the operator's explicit "yes" first.

## References

- [references/gdpr-engineering-detail.md](references/gdpr-engineering-detail.md) -- grep patterns (§A),
  lawful basis table (§B), stop-and-verify checklist (§C), CCPA/CPRA thresholds and
  requirements table (§D).
- [references/gdpr-engineering.md](references/gdpr-engineering.md) -- rights-as-code checklists, retention table, ROPA template, DPA checklist, CCPA/CPRA deltas; external regulatory links collected there.
