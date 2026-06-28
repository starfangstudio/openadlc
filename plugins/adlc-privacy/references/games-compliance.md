<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
# Games compliance reference

Companion to `skills/games-compliance/SKILL.md`. Confirm all legal conclusions with counsel.

---

## 1. Loot-box / paid-random-item law by jurisdiction

| Jurisdiction | Status (as of June 2026) | Action required |
|---|---|---|
| **Belgium** | **Banned.** Paid loot boxes classified as illegal gambling; criminal fines up to EUR 800,000 + prison. Free-to-open cosmetic crates may survive, confirm with counsel. | Disable paid random items for BE users. Geo-gate at IP + store. |
| **Netherlands** | **Effectively banned in practice.** Court overturned EUR 10m EA fine, but Dutch Gambling Authority still treats many paid loot-box models as gambling; legal uncertainty high. | Treat as high-risk; geo-gate or remove paid random items; confirm with local counsel. |
| **China** | **Odds disclosure + monthly spend caps mandated.** Must publish item probabilities in-game before purchase; tightened 2024. | In-game odds display in Simplified Chinese; cap enforcement in Mainland SKU. |
| **South Korea** | **Odds disclosure legally required.** Mandatory in-game probability disclosure from March 2024. | Display item odds in Korean before purchase. |
| **Japan** "Kompu Gacha" | **Banned** (2012 JOGA/METI guidance). Complete-gacha (collect a set for a prize) prohibited; regular gacha with disclosed odds permitted. | No complete-gacha mechanic for JP users; disclose odds. |
| **United Kingdom** | **No legal ban; disclosure + parental-consent model.** PEGI "Paid Random Items" label required since April 2020; Ukie principles recommend parental consent for under-18 purchases; formal legislation possible post-2026. | Apply PEGI label; implement parental consent UX for under-18 IAP. |
| **EU (other member states)** | **No harmonised ban yet.** Digital Fairness Act expected Q3-Q4 2026 proposal; EP IMCO voted Oct 2025 to recommend banning gambling-like mechanics accessible to minors; formal law likely 2027-2028. Watch per-member-state gambling law (Germany, Austria vary). | Monitor DFA; apply PEGI 16 minimum (see section 3); seek per-market counsel. |
| **United States** | **No federal ban; FTC dark-pattern risk + state variation.** Missouri, Hawaii, Minnesota introduced bills; none enacted federally as of June 2026. ESRB "Loot Boxes" descriptor voluntary. | Disclose odds (App Store + Play require it); avoid dark patterns; consult counsel on state exposure. |
| **Australia** | **No ban; Classification Board + ACCC monitoring.** Senate committee recommended industry reform; no legislation as of June 2026. | Disclose odds; IARC/Australian Classification rating. |
| **Canada** | **No federal ban; province-level gambling oversight.** No enforcement action yet. | Disclose odds; monitor. |

> Legal positions shift quickly. Verify with counsel before launch in any new market.

---

## 2. Odds disclosure format (Apple + Google)

Both platforms require disclosure **before** the player commits to a purchase.

### Apple App Store (Guideline 3.1.1)

- Publish the probability (percentage or ratio) for **each item type** that can be received.
- Link must be reachable **from the IAP purchase screen** before payment.
- Acceptable formats: in-app dedicated screen, popover before confirm, or a linked webpage.
- Do NOT disclose only aggregate tiers; disclose per-item type.

### Google Play (Policy: Payments > In-app purchases)

- Must disclose item odds **prior to purchase**.
- Disclosure must be **in-app** (a linked webpage alone is insufficient per Play policy).
- Cover every distinct item and rarity tier.

### Minimal compliant format

```
Gacha pull odds (per 1 pull):
  SSR character: 0.6%
  SR character: 5.4%
  R character: 94.0%
Rate-up banner: featured SSR 0.3% (50% of SSR pool)
Pity: guaranteed SSR at pull 90; soft pity begins at pull 75.
```

Disclose pity/guarantee mechanics as well; omitting them has triggered store policy violations.

---

## 3. PEGI 2026 interactive risk categories (effective June 2026)

Announced March 12, 2026; applies to all newly submitted titles from June 2026.

| Mechanic | Minimum PEGI rating |
|---|---|
| Paid random items (loot boxes) | **PEGI 16** (PEGI 18 for social-casino / simulated gambling) |
| In-game purchases with time/quantity limits | **PEGI 12** |
| NFTs / blockchain | **PEGI 18** |
| Play-by-appointment (daily quests only) | **PEGI 7** |
| Play-by-appointment that punishes absence (content/progress loss) | **PEGI 12** |

Existing rated titles are not re-rated unless updated. Any F2P title with paid loot boxes submitted after June 2026 must carry PEGI 16 minimum.

---

## 4. COPPA 2025 amendments -- games checklist

Compliance deadline: **April 22, 2026**. Applies to operators of child-directed services and mixed-audience services where operators have actual knowledge of child users.

```
[ ] No behavioral/targeted advertising to users under 13 without express verifiable parental consent.
[ ] Persistent identifiers (device ID, advertising ID) not used for behavioral profiling of children without opt-in.
[ ] Parental consent obtained before collecting any personal information from under-13 users.
[ ] Consent flow: separate, granular consent for targeted ads vs. core app functionality.
[ ] Written data retention policy created; children's data not retained beyond operational need.
[ ] Biometric data (face, voice, fingerprints) now in scope; no collection without consent.
[ ] Age screen is neutral: no design that nudges children to misrepresent their age.
[ ] Mixed-audience services: apply COPPA protections wherever actual knowledge of under-13 exists.
[ ] Privacy policy updated to reflect COPPA 2025 scope (biometrics, retention limits, ad-targeting prohibition).
[ ] COPPA Safe Harbor: if using a Safe Harbor program, confirm it covers the 2025 amendments.
```

Legal calls (flag for counsel):
- Whether your game is "directed to children" under the revised FTC standard.
- Whether a neutral age screen is sufficient or whether age verification is required in your market.
- State-level overlay (California AADC, Maryland Kids Code, etc.).

---

## 5. Ads-to-minors limits (games)

| Platform | Restriction |
|---|---|
| **Google Play Families** | No interest-based or remarketing ads; only COPPA-compliant ad networks; no data collection for ad targeting; SDK approved-list only. |
| **Apple App Store (kids category)** | No behavioral advertising; only contextual or house ads; no third-party analytics SDKs that collect data from children without Apple approval. |
| **COPPA (US)** | No targeted/behavioral advertising to under-13 without verifiable parental opt-in; applies to any mixed-audience game with actual knowledge. |
| **GDPR (EU)** | Minors under 16 (member-state opt-down to 13) cannot provide valid data consent; their data cannot be used for behavioral profiling. |

---

## References (external)

- FTC COPPA 2025 final rule: https://www.ftc.gov/news-events/news/press-releases/2025/01/ftc-finalizes-changes-childrens-privacy-rule-limiting-companies-ability-monetize-kids-data
- FTC COPPA rule Federal Register (Apr 22, 2025): https://www.federalregister.gov/documents/2025/04/22/2025-05904/childrens-online-privacy-protection-rule
- PEGI 2026 interactive risk categories (Reed Smith): https://www.reedsmith.com/articles/pegi-launches-interactive-risk-categories-overhauls-age-ratings-for-loot-boxes-in-game-spending-and-communication-features/
- Apple App Store Review Guidelines 3.1.1: https://developer.apple.com/app-store/review/guidelines/#in-app-purchase
- Google Play Payments policy (loot box odds): https://support.google.com/googleplay/android-developer/answer/9901712
- EU Digital Fairness Act -- EP IMCO recommendation (Oct 2025): https://www.europarl.europa.eu/news/en/press-room/20251013IPR30892/new-eu-measures-needed-to-make-online-services-safer-for-minors
- Belgium loot-box gambling ruling overview: https://blog.promise.legal/loot-box-laws-game-developers/
- Loot-box regulation global overview 2026: https://programminginsider.com/loot-boxes-regulation-and-where-the-line-sits-in-2026/
- PEGI 2026 compliance guide (Esports Legal News): https://esportslegal.news/2026/03/30/pegi-2026-new-risk-ratings/
