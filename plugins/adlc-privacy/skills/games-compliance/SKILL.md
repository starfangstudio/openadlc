---
name: games-compliance
description: >-
  This skill should be used when the user asks to "check our game for loot box compliance",
  "are we legal in Belgium / Netherlands / EU with gacha", "do we need to publish drop rates",
  "how do we handle COPPA for our F2P game", "can we show ads to kids", "what age rating will
  we get with paid random items", "is our gacha mechanic banned in Europe", "how do we geo-gate
  loot boxes", "check our age screen for COPPA", "prepare the game for global launch compliance",
  "what markets restrict paid random items", "IARC / PEGI / ESRB rating for our game with loot
  boxes", "are we compliant with the 2025 COPPA amendments", or "what odds disclosure format
  does Apple or Google require". Covers gacha / loot-box odds disclosure (Apple + Google
  platform requirements and per-jurisdiction law), geo-restricted / banned markets (Belgium,
  Netherlands, moving EU picture), PEGI 2026 interactive risk categories, COPPA 2025 amendments
  (kids data + behavioral ad prohibition), age ratings (IARC, PEGI 16 threshold), and
  ads-to-minors limits (Play Families, Apple Kids). Defers store-submission mechanics to
  android-compliance / ios-store-compliance, security to adlc-security, and telemetry emission
  to the telemetry skill.
version: 0.1.0
---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# F2P games compliance

This skill surfaces the compliance surface specific to F2P game monetization at max TAM.
It is an engineering aide, not legal advice. Flag every legal conclusion for counsel
confirmation per market.

## Detect first

Before advising, inspect the actual code and configuration.

```bash
# What monetization mechanics exist?
grep -rn "lootBox\|gacha\|randomItem\|spinWheel\|cardPack\|prize\|purchase" \
  --include="*.kt" --include="*.swift" --include="*.java" . | head -40

# Any age-gate or age-screen?
grep -rn "ageGate\|AgeGate\|birthDate\|ageVerif\|minAge\|COPPA\|coppa" \
  --include="*.kt" --include="*.swift" . | head -20

# Ad SDKs present?
grep -rn "AdMob\|IronSource\|AppLovin\|Unity Ads\|Vungle\|SuperAwesome\|kidoz" \
  --include="*.gradle" --include="Package.swift" --include="*.podspec" . | head -20

# Target age declared in store metadata?
grep -rn "targetAudience\|contentRating\|IARC\|ageRating" . | head -10
```

Mark any mechanic or data flow you cannot determine from source as `unknown`. Never
assume what an SDK collects; read its published data disclosure.

## Step 1: Classify the target audience

Determine before everything else; the entire compliance picture changes.

- **Kids-directed** (primary audience under 13): COPPA applies (US), GDPR Article 8
  applies (EU), no behavioral ads, no unnecessary data collection, neutral age screen only.
- **Mixed-audience**: treat any user where actual knowledge of under-13 exists as COPPA-covered.
- **General / 13+**: standard adult GDPR/CCPA surface; still must geo-handle loot-box law.

If the target audience is `unknown`, stop and ask; do not proceed with compliance analysis.

## Step 2: Loot-box / paid-random-item audit

For each randomized-purchase mechanic (gacha, card pack, spin, prize chest):

1. **Identify the paid-random-item trigger**: any IAP or premium currency spent on a
   random item outcome is in scope.
2. **Geo-gate Belgium and Netherlands** (and treat Netherlands as high-risk): disable the
   mechanic or block purchase for those country codes at both client and server. Belgium
   carries criminal liability. Confirm current NL status with counsel before any release.
3. **Publish odds** on both platforms (non-negotiable, see below) and in-game for CN/KR SKUs.
4. **PEGI 16 floor** from June 2026: any title with paid random items submitted new gets
   minimum PEGI 16. If the target audience was previously under 16, reassess the IARC/ESRB path.
5. Watch the EU Digital Fairness Act (proposal expected Q3-Q4 2026); it may restrict paid
   loot boxes for minors EU-wide. Monitor and confirm with counsel before EU launch.

See [references/games-compliance.md](../../references/games-compliance.md) table 1 for full jurisdiction list.

## Step 3: Odds disclosure

Both Apple (Guideline 3.1.1) and Google Play require disclosure **before payment**.

- Disclose every distinct item type and rarity tier as a percentage or ratio.
- Disclose pity / guarantee mechanics; omitting them has triggered policy violations.
- Apple: reachable from the IAP purchase screen (in-app or linked page).
- Google Play: must be **in-app**, not only a linked external page.
- China: in-game Simplified Chinese disclosure + monthly spend caps.
- South Korea: legally mandated in-game disclosure before purchase (from March 2024).

See [references/games-compliance.md](../../references/games-compliance.md) section 2 for the format.

## Step 4: COPPA 2025 (compliance deadline April 22, 2026)

Apply if the game is directed to children or if you have actual knowledge of under-13 users.

```
[ ] Age screen is neutral: no design nudging children to misrepresent age.
[ ] No behavioral/targeted advertising to under-13 without verifiable parental opt-in.
[ ] Device/advertising ID not used for behavioral profiling without parental consent.
[ ] Parental consent collected before any personal information (name, email, device ID, location).
[ ] Consent is separate + granular: targeted ads require opt-in beyond core-app consent.
[ ] Children's data retention policy written and enforced; no retention beyond operational need.
[ ] Biometric data (face, voice, fingerprint) now in scope; no collection without parental consent.
[ ] Mixed-audience flow: COPPA protections activate on any signal of a user being under 13.
[ ] Privacy policy updated for 2025 scope (biometrics, retention limits, ad-targeting prohibition).
```

Flag for counsel: "directed to children" determination under revised FTC standard; whether neutral age screen suffices or verification is required per market; state-level overlays (California AADC, Maryland Kids Code).

## Step 5: Age ratings

- **IARC** is the submission path on both Google Play and Apple (for applicable regions); IARC
  routes to ESRB (US), PEGI (Europe), USK (Germany), ClassInd (Brazil), and others.
- **PEGI 16 minimum** for any title with paid random items submitted from June 2026 (new PEGI
  interactive risk categories, effective June 2026).
- **ESRB "Loot Boxes" descriptor**: voluntary in the US; apply it for transparency.
- If the game also has time-limited purchase offers, minimum PEGI 12 applies in addition.

Confirm the rating before launch; an incorrect IARC answer can result in rating removal.

## Step 6: Ads-to-minors

- **Google Play Families**: no interest-based or remarketing ads; only approved COPPA-compliant
  ad networks; no data collection for ad targeting; SDK allowlist applies.
- **Apple Kids category**: no behavioral advertising; no third-party analytics SDKs that collect
  child data without Apple approval; only contextual or house ads.
- For under-16 EU users: no behavioral profiling under GDPR; consent from the holder of
  parental responsibility required (age varies: 13-16 by member state).

See [references/games-compliance.md](../../references/games-compliance.md) section 5.

## Geo-soften knob

When full mechanics cannot ship to a restricted market, implement in this order:

1. **Server-side (required):** resolve the store country code from the purchase receipt; reject any random-item IAP for banned jurisdictions server-side.
2. **Client-side:** hide paid-random-item UI for the geo-blocked country code.
3. **Alternative offer:** provide a deterministic-purchase path (fixed price, player selects item) where commercially viable.
4. **Never rely on client-side geo-gate alone:** a client-only gate is bypassable and does not satisfy Belgium's legal requirement.

## Outbound: get the operator's yes first

Local work is fine to do without asking. Outbound here (submitting a game to any store, publishing a privacy policy, responding to a DSAR, enabling a live SDK that sends data, making any declaration to a regulator): stop, present exactly what would go out, and get the operator's explicit "yes" first.

## References

- [references/games-compliance.md](../../references/games-compliance.md) -- jurisdiction table, odds-disclosure
  format, PEGI 2026 categories, COPPA 2025 checklist, ads-to-minors limits.
- [references/games-compliance-detail.md](../../references/games-compliance-detail.md) -- COPPA 2025 full checklist,
  geo-soften implementation pattern.
- Apple App Store Review Guidelines 3.1.1 (loot boxes):
  https://developer.apple.com/app-store/review/guidelines/#in-app-purchase
- Google Play Payments policy (random items):
  https://support.google.com/googleplay/android-developer/answer/9901712
- FTC COPPA 2025 final rule:
  https://www.ftc.gov/news-events/news/press-releases/2025/01/ftc-finalizes-changes-childrens-privacy-rule-limiting-companies-ability-monetize-kids-data
- PEGI 2026 interactive risk categories (Reed Smith):
  https://www.reedsmith.com/articles/pegi-launches-interactive-risk-categories-overhauls-age-ratings-for-loot-boxes-in-game-spending-and-communication-features/
- EU Digital Fairness Act -- EP IMCO recommendation (Oct 2025): https://www.europarl.europa.eu/news/en/press-room/20251013IPR30892/new-eu-measures-needed-to-make-online-services-safer-for-minors
- Loot-box regulation global overview 2026: https://programminginsider.com/loot-boxes-regulation-and-where-the-line-sits-in-2026/
