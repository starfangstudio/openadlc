<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
Consumed by the `games-compliance` skill. Load on demand; do not load independently.

---

## COPPA 2025 compliance checklist

Apply when the game is directed to children or when you have actual knowledge of under-13 users.
Compliance deadline: April 22, 2026.

```
[ ] Age screen is neutral: no design that nudges children to misrepresent age.
[ ] No behavioral / targeted advertising to under-13 without verifiable parental opt-in.
[ ] Device/advertising ID not used for behavioral profiling of children without parental consent.
[ ] Parental consent collected before any personal information (name, email, device ID, location).
[ ] Consent is separate + granular: targeted ads require an explicit opt-in beyond core-app consent.
[ ] Children's data retention policy written and enforced; no retention beyond operational need.
[ ] Biometric data (face, voice, fingerprint) now in scope; no collection without parental consent.
[ ] Mixed-audience flow: COPPA protections activate on any signal of a user being under 13.
[ ] Privacy policy updated for 2025 scope (biometrics, retention limits, ad-targeting prohibition).
```

Flag for counsel: whether your game triggers "directed to children" under the revised FTC
standard; whether a neutral age screen suffices or age verification is required per market;
state-level overlays (California AADC, Maryland Kids Code).

---

## Geo-soften implementation pattern

When full mechanics cannot be shipped to a restricted market, implement in this order:

1. **Server-side (required):** resolve the store country code from the purchase receipt at the
   time of any random-item IAP; reject the purchase for banned jurisdictions server-side.
2. **Client-side:** hide the paid-random-item UI for the geo-blocked country code.
3. **Alternative offer:** provide a deterministic-purchase path (select the item, fixed price)
   for markets where that is commercially viable.
4. **Never rely on client-side geo-gate alone:** server enforcement is required. A client-only
   gate is bypassable and does not satisfy the legal requirement in Belgium.
