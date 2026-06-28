<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
# GDPR/CCPA engineering reference

Supplement to `skills/gdpr-engineering/SKILL.md`. Contains the rights-as-code
checklist, retention patterns, a ROPA template, and CCPA/CPRA deltas.

---

## 1. Data-subject rights as code

### 1a. DSAR export endpoint (Art. 15 / CCPA §1798.110)

Deadline: 30 days (GDPR), 45 days (CCPA, extendable once to 90).

```
GET /api/privacy/export?userId=<id>
  Auth: re-authenticate the requester (not just a session cookie)
  Returns: JSON/ZIP of every record tied to userId across:
    - primary DB (profile, events, game state, purchases)
    - analytics store (if user-level rows are kept)
    - push-notification tokens / device IDs
    - support tickets
    - any processor copy (see §4)
  Format: machine-readable (JSON) per GDPR Rec. 68; human-readable preferred too
```

Implementation checklist:
- [ ] User identity verified before export is generated (re-auth or email OTP)
- [ ] Export covers ALL data stores; a unit test lists every store and asserts each is queried
- [ ] Export generated in a temp location, URL is time-limited (< 48 h), then deleted
- [ ] Request logged in an audit trail with timestamp and outcome
- [ ] Response time monitored; alert if approaching deadline

### 1b. Right-to-erasure pipeline (Art. 17 / CCPA §1798.105)

Deadline: 30 days (GDPR, with possible extension for complex cases); CCPA same.

Pipeline pattern (event-driven, async):

```
1. POST /api/privacy/delete?userId=<id>   ← re-auth required
2. Emit DeleteRequested event to internal queue (Kafka / SQS / PubSub)
3. Each service subscribes → deletes/anonymises its own records → emits DeleteConfirmed
4. Orchestrator waits for all confirmations (timeout = 72 h), then:
   a. Soft-delete primary user record (replace PII with "deleted_<hash>")
   b. Notify each third-party processor (see §4)
   c. Schedule backup purge at next retention cycle (see §2)
   d. Write deletion certificate to audit log (immutable)
5. Confirm to user within legal deadline
```

What must be reached:
- [ ] Primary DB (all tables with userId FK)
- [ ] Analytics / data warehouse (delete or anonymise rows)
- [ ] Push token store
- [ ] Support / CRM copy
- [ ] CDN / object storage (avatars, attachments)
- [ ] Backups (schedule overwrite; document the lag, usually 30 days)
- [ ] Each third-party processor notified in writing (email + record kept)
- [ ] Logs: pseudonymise or expunge PII in logs on the same schedule

Exceptions to erasure (must document in the request response):
- Legal obligation to retain (e.g. financial records, tax law)
- Legitimate interest in fraud prevention (time-limited)
- Never invent an exception; flag "confirm with counsel" for borderline cases

### 1c. Right to rectification (Art. 16)
Expose a user settings / profile-edit flow that writes through to all stores. Same scope as the export: every data store that holds the field.

### 1d. Right to restriction / objection (Art. 18, 21)
Flag the user record with `processing_restricted = true`. All downstream consumers must check this flag before processing. Build a system test that verifies a restricted user's data is excluded from analytics queries and marketing pipelines.

---

## 2. Retention + minimisation patterns

| Data category | Retention trigger | Max period (suggested) | Action on expiry |
|---|---|---|---|
| Account / profile PII | Account deletion | 0 days (immediate) | Delete or anonymise |
| Gameplay events (non-PII) | Collection | 24 months | Aggregate, then delete |
| Purchase records | Last transaction | 7 years (tax law; confirm with counsel per jurisdiction) | Archive, no PII |
| Support tickets | Ticket close | 3 years | Anonymise user fields |
| Server / app logs (with IP) | Log creation | 90 days | Delete or pseudonymise |
| Analytics (user-level) | Session | 12 months | Aggregate, delete rows |
| Crash reports (with device ID) | Report date | 90 days | Delete after fix |
| Push tokens | Account active | Account deletion | Delete immediately |

Implementation:
- Run a scheduled job (daily/weekly) against each store with a `created_at < NOW() - retention_period` predicate.
- Log every purge run with row counts.
- Do NOT apply retention periods to anonymised/aggregated data; they no longer contain personal data.

---

## 3. ROPA template (Art. 30)

One row per processing activity. Keep in a version-controlled file (`ropa.csv` or `ropa.md`); update every time a new SDK or data flow is added.

| Field | Example |
|---|---|
| Activity name | User account registration |
| Controller | <Company name, address> |
| DPO contact (if applicable) | dpo@example.com |
| Purpose | Creating and managing user account |
| Lawful basis | Art. 6(1)(b): performance of contract |
| Data categories | Name, email, hashed password, country |
| Data subjects | App users (age 13+) |
| Recipients | Auth service (internal), email delivery processor |
| Third-country transfers | None / Standard Contractual Clauses to <country> |
| Retention | Account active + 30 days |
| Security measures | TLS in transit, AES-256 at rest, access-controlled DB |
| DPA reference | DataProcessor Inc. DPA v2, signed 2025-01-10 |

Maintain one row for each distinct purpose: analytics, purchases, push notifications,
ads attribution, support, crash reporting, etc.

---

## 4. DPA checklist per processor/SDK

A Data Processing Agreement is required for every processor that touches personal data (Art. 28). Processors include: Firebase / Crashlytics, Amplitude, Adjust, AppsFlyer, Braze, Stripe, customer-support SaaS, cloud provider.

For each processor:
- [ ] DPA signed and on file (controller terms or processor's standard DPA)
- [ ] DPA covers: subject matter, duration, nature/purpose, data type, data-subject categories
- [ ] Sub-processors listed and change-notification clause included
- [ ] Transfer mechanism documented (adequacy decision / SCCs / BCRs) for non-EU processors
- [ ] Processor provides deletion/export on your request (test this)
- [ ] DPA reference added to the ROPA row for that activity

---

## 5. CCPA/CPRA deltas (California, effective 2023-01-01, updated regs Jan 2026)

| Delta | Engineering requirement |
|---|---|
| Do-Not-Sell / Do-Not-Share | Honor Global Privacy Control (GPC) signal automatically; cease sale/sharing within 15 business days of any valid request |
| Opt-out UI parity | "Do Not Sell or Share" link/button must require same steps or fewer than opt-in; enforce in iOS/Android settings screen |
| Sensitive personal information | SPI (precise geolocation, health data, financial data, race/ethnicity, communications content) requires a separate "Limit Use of My Sensitive PI" control |
| Contractor/service-provider contracts | Equivalent of DPA; must prohibit selling/retaining beyond the service |
| Right to correct | Same as GDPR Art. 16; expose a profile-edit flow |
| Response time | 45 days (extendable once to 90 days) for DSAR/erasure |
| Opt-out confirmation | From Jan 1 2026: visibly confirm in app/site that opt-out was processed |
| Thresholds | Applies to businesses: (a) >$25M annual gross revenue, OR (b) buy/sell/receive/share PI of 100,000+ consumers/households, OR (c) derive 50%+ revenue from selling PI. Confirm applicability with counsel. |

GPC implementation (mobile): detect `navigator.globalPrivacyControl` (web views) or an equivalent signal. For native apps, treat an in-app "Do Not Sell" toggle as the signal; wire it to a flag that blocks all ad-attribution SDK initialisation and any sale/share of PI.

---

## 6. Lawful basis quick-reference (GDPR Art. 6)

| Basis | When to use | Trap |
|---|---|---|
| Art. 6(1)(a) Consent | Marketing, optional analytics, ads targeting | Must be freely given, specific, informed, unambiguous; withdrawable at any time |
| Art. 6(1)(b) Contract | Processing needed to deliver the service the user signed up for | Cannot stretch to cover analytics or marketing |
| Art. 6(1)(c) Legal obligation | Tax records, fraud reporting | Narrow; confirm legal obligation exists in the specific jurisdiction |
| Art. 6(1)(f) Legitimate interests | Security logging, fraud prevention, product improvement (without profiling) | Must pass LIA (Legitimate Interest Assessment); privacy right can override; do not use as a catch-all |

For each processing activity in the ROPA, record the lawful basis. "Legitimate interests" as a blanket basis is an enforcement red flag; flag it for counsel review.

---

## References

- GDPR full text, EUR-Lex: https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX%3A32016R0679
- EDPB Guidelines on the right of access (Art. 15): https://edpb.europa.eu/our-work-tools/our-documents/guidelines/guidelines-012022-data-subject-rights-right-access_en
- EDPB 2025 coordinated erasure enforcement report (2026): https://edpb.europa.eu
- ICO: Guide to the right of erasure: https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/individual-rights/individual-rights/right-to-erasure/
- CPRA / CCPA text: https://oag.ca.gov/privacy/ccpa
- Greenberg Traurig: Revised CCPA Regulations Jan 1 2026: https://www.gtlaw.com/en/insights/2025/9/revised-and-new-ccpa-regulations-set-to-take-effect-on-jan-1-2026-summary-of-near-term-action-items
- DPC Ireland: ROPA guidance (Art. 30): https://www.dataprotection.ie/en/dpc-guidance/records-of-processing-article-30-guidance
- GDPR deletion pipeline engineering (Medium): https://medium.com/@sohail_saifii/gdpr-implementation-building-data-deletion-and-export-apis-that-actually-work-833b34eb09f6
