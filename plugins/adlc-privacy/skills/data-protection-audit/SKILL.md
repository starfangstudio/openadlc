---
name: data-protection-audit
description: >-
  This skill should be used when the user asks to "map our data flows", "audit
  what data the app collects", "build our ROPA", "fill in the GDPR records of
  processing", "check what SDKs send off device", "generate the privacy policy
  data inventory", "what personal data do we collect and share", "audit data
  retention", "check encryption in transit and at rest", "feed the Data safety
  form from code", "feed the App Store nutrition labels from code", "is our data
  collection GDPR compliant", "check CCPA data inventory", "do we need COPPA
  compliance", "privacy audit before launch", or "data map for compliance".
  Produces a DATA MAP (personal-data type, storage, third-party egress, retention,
  encryption) that is the source of truth for GDPR Art 30 ROPA, the privacy
  policy, and store declarations. Cross-references android-compliance (Data safety)
  and ios-store-compliance (nutrition labels) without duplicating them. Output
  includes a findings table: over-collection, undisclosed SDK egress, missing
  encryption, retention gaps. Read-only audit only.
version: 0.1.0
---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# Data-protection audit

This skill maps the app's actual data flows from code evidence and produces a
DATA MAP: the single source of truth that feeds GDPR Art 30 ROPA, the privacy
policy, and store data declarations. It does not replace legal counsel; it
eliminates the guesswork before counsel reviews.

## Detect first

Never assume. Read the code before writing any answer.

```bash
# 1. Merged Android manifest (what Play actually sees, including SDK permissions)
./gradlew :app:processReleaseManifest 2>/dev/null
cat app/build/intermediates/merged_manifests/release/AndroidManifest.xml \
  | grep -E "uses-permission|uses-feature"

# 2. SDK declarations: Gradle + SPM + Podfile
grep -rEn "implementation |api " app/build.gradle* gradle/libs.versions.toml 2>/dev/null | head -40
grep -rn "\.package(" Package.swift 2>/dev/null | head -20

# 3. Network egress: all hostnames and SDK init calls
grep -rEn "https?://|OkHttpClient|URLSession|Retrofit|Volley|Alamofire|fetch\(" \
  --include="*.kt" --include="*.swift" --include="*.java" . | grep -v "test\|Test" | head -60

# 4. Identifiers and PII field names leaving the device
grep -rEn "userId|deviceId|email|phone|ipAddress|advertisingId|IDFA|GAID|latitude|longitude" \
  --include="*.kt" --include="*.swift" --include="*.java" . | grep -v "test\|Test" | head -40

# 5. Local storage: databases, SharedPreferences, NSUserDefaults, Keychain, files
grep -rEn "Room|SQLite|SharedPreferences|DataStore|NSUserDefaults|UserDefaults|Keychain|FileOutputStream" \
  --include="*.kt" --include="*.swift" --include="*.java" . | grep -v "test\|Test" | head -30

# 6. Known analytics/ads SDK markers
grep -rEin "firebase|amplitude|mixpanel|braze|adjust|appsflyer|branch|facebook|meta|admob|applovin|ironSource|unity\s*ads" \
  --include="*.kt" --include="*.swift" --include="*.java" --include="*.gradle" . | grep -v "test\|Test" | head -30
```

Mark every value you cannot determine `unknown`. Never invent "no collection" to
clear a form.

## Produce the DATA MAP

For each personal-data type found, fill one row:

| Data type | Legal basis (GDPR) | Collected by | Stored where | Sent to (3rd party / SDK) | Retention | Encrypted in transit | Encrypted at rest | COPPA flag |
|---|---|---|---|---|---|---|---|---|

For the full column schema with example rows, GDPR legal-basis options, CCPA
categories, COPPA scope test, and loot-box jurisdiction flags, see
[references/data-protection-audit-detail.md](../../references/data-protection-audit-detail.md).

**Filling rules:**
- Build from grep evidence, not memory or SDK marketing copy.
- For each SDK, read the vendor's published data-collection disclosure; mark
  `unknown` if absent or ambiguous.
- GDPR legal basis: see the lawful-basis quick-reference in [references/gdpr-engineering-detail.md](../../references/gdpr-engineering-detail.md) (section B).
- COPPA: flag any data type where the app has no age gate and content could
  plausibly attract users under 13. The 2025 amendments (effective April 22,
  2026) expand personal information to include biometric identifiers and mobile
  numbers. Confirm with counsel.

## Findings table

After the DATA MAP, emit a findings table with columns: Finding, Severity,
Evidence (file:line or SDK name), Action. For severity definitions and example
rows, see [references/data-protection-audit-detail.md](../../references/data-protection-audit-detail.md).

HIGH = must fix before launch. MEDIUM = fix before public release or document
accepted risk with an owner.

## How this feeds downstream artifacts

The DATA MAP is the single input for GDPR Art 30 ROPA (one row per processing
activity), the privacy policy (each data type, purpose, retention, sharing
partner), the Android Data safety form (cross-check with `android-compliance`),
and iOS nutrition labels (cross-check with `ios-store-compliance`). For the
exact field mappings and required disclosure language per artifact, see
[references/data-protection-audit-detail.md](../../references/data-protection-audit-detail.md).

## Verify the map

Run the verification checklist in
[references/data-protection-audit-detail.md](../../references/data-protection-audit-detail.md) before
calling the audit complete. Mark each item PASS / FAIL / UNKNOWN. Do not call
the audit complete with any FAIL or UNKNOWN item that has no owner assigned.

## Scope boundaries

Store submission: `android-compliance` / `ios-store-compliance`. Consent UI:
consent-management skill. Security: `adlc-security`. Analytics emission:
telemetry skill. This audit maps flows only.

## Outbound: get the operator's yes first

Local work is fine to do without asking. Outbound here (submitting a GDPR ROPA to the DPA, responding to a DSAR, publishing a privacy policy, enabling an SDK that sends data off device, saving a Data safety declaration, filing App Store nutrition labels): stop, present exactly what would go out, and get the operator's explicit "yes" first.

## References

- [references/data-protection-audit-detail.md](../../references/data-protection-audit-detail.md) -- DATA MAP
  schema, example rows, GDPR legal-basis options, CCPA categories, COPPA scope
  test, loot-box flags, findings severity table, downstream artifact field
  mappings, and the full verify checklist.
- [references/data-protection-audit.md](../../references/data-protection-audit.md) -- data-type
  taxonomy and per-jurisdiction flags.
- GDPR Art 30 (Records of processing activities): https://gdpr-info.eu/art-30-gdpr/
- EDPB Art 30 guidance: https://www.edpb.europa.eu/gdpr-articles/article-30-records-processing-activities_en
- ICO Art 30 documentation guide: https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/accountability-and-governance/documentation/what-do-we-need-to-document-under-article-30-of-the-gdpr/
- CCPA/CPRA 2026 risk assessment rules: https://cppa.ca.gov/regulations/
- FTC COPPA 2025 amendments (effective April 22, 2026): https://www.ftc.gov/legal-library/browse/rules/childrens-online-privacy-protection-rule-coppa
- Google Play Data safety requirements: https://support.google.com/googleplay/android-developer/answer/10787469
- Apple App Privacy details: https://developer.apple.com/app-store/app-privacy-details/
