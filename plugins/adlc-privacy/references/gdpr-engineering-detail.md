<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
Consumed by the `gdpr-engineering` skill. Load on demand; do not load independently.

---

## A. Detect-first: grep patterns

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

For each SDK found, look up its published data-collection disclosure (its privacy policy
or DPA template). Mark SDKs with unknown collection as `unknown`; resolve before shipping.

---

## B. Lawful basis quick-reference (GDPR Art. 6)

| Basis | When to use | Trap |
|---|---|---|
| Art. 6(1)(a) Consent | Marketing, optional analytics, ad targeting | Freely given, specific, informed, unambiguous; withdrawable at any time via same UI |
| Art. 6(1)(b) Contract | Processing strictly needed to deliver the feature the user signed up for | Cannot stretch to analytics or marketing |
| Art. 6(1)(c) Legal obligation | Tax records, fraud reporting | Narrow; confirm the legal obligation exists in the specific jurisdiction |
| Art. 6(1)(f) Legitimate interests | Security logging, fraud prevention | Must pass a Legitimate Interest Assessment (LIA); do not use as a catch-all |

For each processing activity in the ROPA, record exactly one lawful basis. "Legitimate
interests" as a blanket basis is a DPA enforcement red flag; flag it for counsel review.

---

## C. Stop-and-verify checklist

Before calling a data flow GDPR/CCPA-ready, each item must be PASS / FAIL / UNKNOWN:

```
[ ] Every data store and SDK in scope is listed in the ROPA
[ ] Each processing activity has exactly one documented lawful basis
[ ] DSAR export endpoint verified: re-auth, all stores queried, time-limited URL, logged
[ ] Erasure pipeline verified: all stores + processors reached, deletion certificate written
[ ] Retention schedules implemented and purge job running with row-count logs
[ ] DPA on file for every processor; transfer mechanism documented for non-EU processors
[ ] Privacy-by-default confirmed: analytics/ads off by default; opt-in required
[ ] PII not present in URLs, debug logs, or crash reports
[ ] CCPA opt-out controls implemented if California thresholds met (confirmed with counsel)
[ ] GPC signal honored automatically (if applicable)
```

Do not mark a flow compliant with any FAIL or UNKNOWN unresolved. Resolve or escalate
to counsel first.

---

## D. CCPA/CPRA thresholds and engineering requirements

Applies if the business meets any California threshold (confirm with counsel): >$25M
annual gross revenue, OR buy/sell/receive/share PI of 100k+ consumers/households, OR
derive 50%+ revenue from selling PI.

| Delta | Engineering requirement |
|---|---|
| Do-Not-Sell / Do-Not-Share | Honor Global Privacy Control (GPC) signal automatically; cease sale/sharing within 15 business days of any valid request |
| Opt-out UI parity | "Do Not Sell or Share" link/button must require same steps or fewer than opt-in |
| Sensitive PI | Separate "Limit Use of My Sensitive PI" control for precise geolocation, health, financial data, etc. |
| Opt-out confirmation | From Jan 1 2026: visibly confirm in-app that opt-out was processed |
| Response time | 45 days (extendable once to 90) for DSAR/erasure |
| Contractor contracts | Equivalent of DPA; must prohibit selling/retaining beyond the service |

GPC implementation (mobile): detect `navigator.globalPrivacyControl` in web views. For
native apps, treat an in-app "Do Not Sell" toggle as the signal; wire it to a flag that
blocks all ad-attribution SDK initialisation before consent is confirmed.

---

## References

See also [references/gdpr-engineering.md](references/gdpr-engineering.md) for the full rights-as-code
checklists (DSAR pipeline, erasure pipeline), retention table, ROPA template, DPA checklist,
and additional CCPA/CPRA detail.
