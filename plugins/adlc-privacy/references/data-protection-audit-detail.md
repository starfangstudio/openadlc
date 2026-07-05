<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
Consumed by the `data-protection-audit` skill. Load on demand; do not load independently.

## DATA MAP table schema

Full column set for each personal-data type found in the codebase:

| Data type | Legal basis (GDPR) | Collected by | Stored where | Sent to (3rd party / SDK) | Retention | Encrypted in transit | Encrypted at rest | COPPA flag |
|---|---|---|---|---|---|---|---|---|
| Device ID | Legitimate interest / Consent | First-party code | Local DB | Firebase Analytics | Session | TLS (unknown if pinned) | unknown | Flag if under-13 possible |
| Email address | Contract | First-party code | Remote DB | Auth provider | Account lifetime | TLS | Yes (server-side) | Flag if under-13 possible |
| Location (lat/lon) | Consent | GPS API | None (in-memory) | Maps SDK | None | TLS | N/A | HIGH flag |

Fill every column from grep evidence; mark `unknown` for anything not determinable from code. Never fill "no collection" without code evidence.

## GDPR legal-basis options

- **Consent**: advertising, analytics, behavioural profiling. Requires opt-in before data flows.
- **Contract**: data strictly needed to provide a feature the user explicitly requested. Narrow; do not use for analytics.
- **Legitimate interest**: requires a documented balancing test. Flag every LI basis for counsel review.
- **Legal obligation**: compliance with a statutory requirement (tax records, CSAM detection).
- **Vital interests / Public task**: rare; confirm with counsel.

## CCPA categories (for "Sold or Shared" column)

- Identifiers (name, email, IP, device ID, GAID/IDFA)
- Commercial information (purchase history, spend)
- Internet/network activity (browsing, search, app usage)
- Geolocation
- Biometric information
- Professional/employment information
- Inferences drawn from any of the above

CPRA 2026 risk-assessment requirement: flag any automated decision-making that produces legal or similarly significant effects on California consumers.

## COPPA scope test

Flag a data type as COPPA-exposed when ALL of the following apply:

1. The app has no age gate (or a non-compliant "enter your birthday" gate).
2. The content could plausibly attract users under 13 (F2P games, cartoon themes, education apps).
3. The data type falls within COPPA "personal information": name, address, email, phone, geolocation, photos/video/audio containing the child, persistent identifiers (device ID, GAID/IDFA), biometric identifiers (added by 2025 amendments, effective April 22, 2026), mobile numbers (added by 2025 amendments).

If flagged: confirm with counsel; the required remediation is either a COPPA-compliant consent flow (verifiable parental consent) or removing the data collection entirely for that user segment.

## Loot-box / F2P jurisdiction flags

Surface the data footprint here; jurisdiction-specific law is in [references/data-protection-audit.md](data-protection-audit.md).

Flag these data types when the app has IAP with randomised rewards:

- Purchase history and spend (Belgium/Netherlands ban on paid loot-boxes; Digital Fairness Act odds disclosure)
- User ID linked to spend (supports cross-game profiling, relevant to GDPR Art 22 automated decisions)
- Age-related inferences (under-18 / under-13 triggers stricter rules in most jurisdictions)

## Findings table: severity definitions and example rows

| Finding | Severity | Evidence | Action |
|---|---|---|---|
| Over-collection: field X not needed for any declared feature | HIGH | grep hit (file:line) | Remove field or document a specific purpose and legal basis |
| Undisclosed SDK egress: SDK Y sends Z, not declared | HIGH | SDK init call | Add to ROPA row + store data-safety declaration |
| Missing encryption in transit | HIGH | HTTP URL in code | Enforce TLS; confirm no plain-HTTP fallback |
| Retention gap: data type has no deletion path | MEDIUM | DB schema / no TTL found | Add TTL or deletion API; "indefinite" is a finding |
| Legal-basis unknown | MEDIUM | data-map row | Flag for counsel; do not ship unresolved |
| COPPA exposure: no age gate, under-13 content possible | HIGH | app-type context | Age gate or COPPA-compliant verifiable parental consent |
| CCPA "Sold or Shared" not answered | MEDIUM | data-map row | Confirm with counsel; default to "yes" if shared with ad networks |

HIGH = must fix before launch. MEDIUM = fix before public release or document accepted risk with an owner.

## Downstream artifact mapping

### GDPR Art 30 ROPA

Each DATA MAP row maps to one processing activity. Fields: purpose, legal basis, data subjects, data types, recipients, retention, security measures, transfers outside EEA. Do not duplicate the map in the ROPA; reference the DATA MAP and note the row.

### Privacy policy

List each data type, purpose, retention period, and sharing partner from the DATA MAP. Do not invent categories absent from the map. Required disclosures (GDPR Art 13/14): identity of controller, DPO contact, legal basis, retention, rights (access, erasure, portability, objection), right to lodge a complaint with the supervisory authority.

### Android Data safety form

The "Collected / Shared" answers come directly from the DATA MAP "Sent to" and "Collected by" columns. Cross-check with the `android-compliance` skill; do not re-audit permissions here. Required when any SDK collects data, even if first-party code does not.

### iOS nutrition labels

`NSPrivacyCollectedDataTypes` entries must match this DATA MAP. Cross-check with `ios-store-compliance`; do not re-audit manifests here. Apple requires disclosure of SDK-collected data even when the developer does not directly access it.

## Verify checklist: full item definitions

Run after completing the DATA MAP. Mark each PASS / FAIL / UNKNOWN.

- **Manifest permissions**: every permission in the merged Android manifest has a DATA MAP row, or is documented as "no personal data collected via this permission".
- **SDK disclosures**: every SDK in the dependency list has its vendor data-collection disclosure reviewed (vendor page read, or explicitly marked `unknown`). An `unknown` here is a MEDIUM finding.
- **Network hostnames**: every hostname found by grep maps to a known DATA MAP entry or is marked `unknown` with a follow-up owner.
- **Encryption in transit**: TLS confirmed for every egress row. `unknown` is not acceptable for a shipped app; treat as HIGH finding.
- **Retention**: at least one retention value filled per data type. "Indefinite" is a MEDIUM finding; must have an owner.
- **COPPA**: if any row is flagged, confirm with counsel before launch. Not a developer-only decision.
- **CCPA / CPRA 2026**: if app serves California users, confirm each "Sold or Shared" answer. Flag any automated decision-making in scope of CPRA risk-assessment requirement.

Do not call the audit complete with any FAIL or UNKNOWN item that has no owner assigned.
