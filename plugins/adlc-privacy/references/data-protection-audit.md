<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
# Data-protection audit: quick reference

Loaded on-demand by the `data-protection-audit` skill. Do not inline this into the skill body.

---

## GDPR legal-basis options (Art 6)

| Basis | When to use in a mobile app | Pitfall |
|---|---|---|
| Consent (Art 6.1.a) | Advertising, behavioural analytics, marketing, non-essential cookies/SDKs | Must be freely given, specific, informed, unambiguous; can be withdrawn; record the consent event |
| Contract (Art 6.1.b) | Data strictly required to perform a feature the user explicitly requested (e.g. storing a username to log in) | Cannot stretch to "useful" or "improves the app"; must be objectively necessary |
| Legitimate interest (Art 6.1.f) | Fraud detection, security logs, basic aggregate crash telemetry | Requires a documented balancing test; not available for children's data or high-risk profiling |
| Legal obligation (Art 6.1.c) | Retaining transaction records for tax/accounting | Narrow; confirm with counsel for the specific jurisdiction |

For special-category data (health, biometric, precise location used for profiling) Art 9 applies; explicit consent is the practical default. Flag every row with Art 9 data for counsel.

---

## Personal data type taxonomy (DATA MAP row values)

Use these canonical names in the DATA MAP to keep the ROPA and store declarations consistent.

| Data type | GDPR category | CCPA category | COPPA personal info? | Notes |
|---|---|---|---|---|
| Device ID (Android ID, IDFV) | Identifiers | Unique identifiers | Yes if linked to child | Resets on factory reset; not IDFA |
| Advertising ID (GAID / IDFA) | Identifiers | Unique identifiers | Yes | Requires ATT on iOS; requires consent under GDPR |
| IP address | Identifiers | Geolocation data (inferred) | Yes | Dynamic IP = personal data under GDPR |
| Precise location (GPS) | Location data (special care) | Precise geolocation | Yes | Requires explicit consent; never background-collect without disclosure |
| Coarse location (network/cell) | Location data | Geolocation | Yes | Lower risk but still personal data |
| Email address | Contact info | Personal identifiers | Yes | Standard PII |
| Display name / username | Profile data | Personal identifiers | Yes | |
| Purchase history | Financial / transactional | Commercial information | Yes | F2P: every IAP event; triggers loot-box data obligations |
| In-app spend amount | Financial | Commercial information | Yes | |
| Crash logs (symbolicated) | Diagnostics | Inferences | Potentially | If they include device ID or user context |
| Analytics events (session, funnel) | Usage data | Internet/network activity | Potentially | Depends on what fields are included; no PII in events |
| Biometric data | Special category (Art 9) | Sensitive personal information (CPRA) | Yes (2025 amendment) | Face ID / Touch ID local only is not a data-collection event; server-side biometric processing is high-risk |
| Age / date of birth | Profile data | Personal identifiers | Yes | Required for COPPA age gate; store securely |
| Payment token (not full PAN) | Financial | Commercial information | Yes | PCI DSS scope; never log or transmit raw card data |

---

## CCPA / CPRA 2026 obligations (California)

Thresholds: annual gross revenue > $25M, OR buys/sells/receives/shares personal info of 100,000+ consumers/households, OR derives 50%+ revenue from selling/sharing personal info.

| Obligation | What it means for a mobile app |
|---|---|
| Right to know / access | In-app DSAR flow or email-based; respond within 45 days |
| Right to delete | Delete account + instruct service providers; 45 days |
| Right to opt out of sale/sharing | "Do Not Sell or Share My Personal Information" link; Global Privacy Control (GPC) signal must be honoured |
| Sensitive data (CPRA) | Precise geolocation, health, biometric, SSN, financial account: requires opt-in consent to use for targeted ads |
| Risk assessment (eff. Jan 1, 2026) | Required before deploying automated decision-making technology (ADMT) that has significant effects on consumers; document and retain |
| Cybersecurity audit (eff. Jan 1, 2026) | Required for businesses meeting risk thresholds; 18-category assessment covering data inventory |

---

## COPPA scope test (US, under-13)

COPPA applies if the app is "directed to children" OR if the operator has actual knowledge it is collecting from a child under 13.

Directed-to-children test factors:
- Subject matter (games, cartoons, child-friendly characters)
- Music or celebrities that appeal to children
- Animated characters or child actors
- Age of users in ads/marketing
- Empirical evidence of user age from analytics

If any factor applies: implement an age gate before any data collection, get verifiable parental consent before collecting personal info from under-13 users, and honour the 2025 COPPA amendments (effective April 22, 2026): no targeted ads to children, no conditioning participation on data collection beyond what is necessary, stricter retention limits, and data security requirements.

F2P games with bright colours, cartoon characters, or simple mechanics are high-risk for COPPA scope. Flag for counsel.

---

## Loot-box / IAP jurisdiction flags

| Jurisdiction | Status (as of June 2026) | Data implications |
|---|---|---|
| Belgium | Paid loot boxes banned as illegal gambling (2018, upheld) | Log-free: no purchase-of-chance records needed; IAP must use cosmetic/fixed items only |
| Netherlands | Paid loot boxes banned for games with minors (2022 court) | Same as Belgium for minors |
| Poland | Draft law (late 2025): gambling licence required for chance-based purchases | Confirm with counsel; may require odds data retention for regulatory reporting |
| France | Minors cannot buy loot boxes without parental consent + adult account verification | Age-gate flow; consent event must be recorded with timestamp |
| EU Digital Fairness Act (DFA) | Expected 2026; likely ban for under-18, odds disclosure, spending caps | Monitor; build odds-disclosure infrastructure proactively |
| US | No federal ban; FTC scrutiny on dark patterns; COPPA applies to under-13 | Odds disclosure is best practice; some states drafting bills |
| UK | Voluntary odds disclosure (2023 industry code); no ban yet | Disclose odds in-game; monitor government review |

Confirm all jurisdiction-specific status with counsel before shipping; this table reflects publicly available information as of June 2026 and can be outdated.

---

## Encryption checklist

| Layer | Requirement | Verify |
|---|---|---|
| In transit | TLS 1.2+ for all network calls | Check `OkHttpClient` / `URLSession` config; no plain HTTP; certificate pinning is additive security, not a replacement for TLS |
| At rest (sensitive data: health, financial, credentials) | Android Keystore / iOS Data Protection class `NSFileProtectionComplete` | Grep for `EncryptedSharedPreferences`, `EncryptedFile`, `kSecAttrAccessible` |
| At rest (non-sensitive local data) | Platform default file encryption (enabled by default on modern Android/iOS) | No action needed unless disabling device encryption is a risk model concern |
| Logs | No PII in logcat / os_log / crash reporters | Grep for PII fields in log calls; strip before shipping |

---

## References

- GDPR Art 30 full text: https://gdpr-info.eu/art-30-gdpr/
- EDPB Art 30 position paper (derogations): https://www.edpb.europa.eu/our-work-tools/our-documents/guidelines/position-paper-derogations-obligation-maintain-records_en
- ICO ROPA documentation guide: https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/accountability-and-governance/documentation/what-do-we-need-to-document-under-article-30-of-the-gdpr/
- CPPA 2026 risk assessment regulations: https://cppa.ca.gov/regulations/
- FTC COPPA Rule (2025 amendments, effective April 22, 2026): https://www.ftc.gov/legal-library/browse/rules/childrens-online-privacy-protection-rule-coppa
- EGDF loot-box documentation (2025): https://www.egdf.eu/documentation/7-balanced-protection-of-vulnerable-players/consumer-protection/lootboxes/
