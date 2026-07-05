---
name: ads-mediation
description: >-
  This skill should be used when the user asks to "add ads to the game", "monetize with
  rewarded video", "add interstitial ads", "set up ad mediation", "configure waterfall or
  bidding", "add LevelPlay ads", "add AdMob mediation", "tune ad frequency", "balance ads
  and IAP", "avoid killing retention with ads", "set up rewarded ad placement", "cap how
  many ads players see", "does showing ads hurt IAP", "ad SDK for F2P game", or "kids and
  ads policy flag". Covers rewarded video vs interstitial placement rules, in-app bidding
  vs waterfall mediation (LevelPlay/AdMob), frequency capping, the ads-vs-IAP-cannibalization
  balance, and the kids/behavioral-ads policy flag. Unity SDK wiring defers to
  adlc-unity/unity-monetization-sdks. Store policy and behavioral-ads legality defer to
  games-compliance and adlc-privacy.
version: 0.1.0
---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# Ads mediation

Rewarded video is the player-friendly ad format: opt-in, tied to an economy reward, and
non-destructive to retention when placed correctly. Interstitials are a blunt instrument:
use them sparingly at natural breaks only, and never mid-action. Mediation (in-app
bidding preferred over waterfall) maximizes fill and eCPM across networks without
changing the player experience.

## Detect first

Inspect the project before recommending any SDK or configuration:

```bash
# Native Android: check for AdMob / MAX in gradle deps
grep -rEn "admob|applovin|ironSource|levelplay|mediation" \
  app/build.gradle* gradle/libs.versions.toml 2>/dev/null

# Native iOS: check Podfile or SPM
grep -rEin "admob|applovin|ironsource|levelplay" \
  Podfile Podfile.lock Package.resolved 2>/dev/null

# Unity: handled by adlc-unity/unity-monetization-sdks -- defer SDK wiring there
# Any project: surface existing placement names and frequency cap settings
grep -rEn "placementName|frequencyCap|adUnitId|APP_KEY" \
  . --include="*.swift" --include="*.kt" --include="*.java" 2>/dev/null | head -20
```

Mark what is found vs `unknown`. Never invent app keys, placement IDs, or network names.

## Format rules

**Rewarded video -- primary format.**

- Surface only at a genuine moment of need: out of energy/lives, post-defeat retry,
  bonus chest, speed-up. Never force it.
- Tie to a specific economy reward the player chose to receive. The watch is opt-in and
  voluntary; remove the placement entirely before making it coercive.
- Grant the reward in the completion callback only, never on ad close.
- Cap at 5-8 rewarded shows per session before satisfaction drops and D7 churn rises.

**Interstitials -- secondary, use sparingly.**

- Place at natural breaks: level end, map transition, session resume.
- Never mid-action, never on death, never back-to-back.
- Cap at 1-3 per session for non-paying cohorts. Skip entirely for paying players.
- Set the cap on the mediation dashboard (LevelPlay / AdMob), not in client code,
  so it tunes without a release.

See [references/ads-mediation-detail.md](../../references/ads-mediation-detail.md) for format comparison
table and session frequency data.

## Mediation: in-app bidding over waterfall

Default to **in-app bidding**: all participating networks submit a real-time price
per impression; the auction winner fills. Unity/LevelPlay deprecated waterfall-only
in early 2025. In-app bidding consistently outperforms static waterfall because a
lower-ranked network may pay more for a specific impression.

Keep a **static waterfall fallback** behind the bidding pool for networks that do not
support real-time bidding.

Primary mediation choices (engine-agnostic):

- **LevelPlay (IronSource):** use for Unity projects. SDK wiring in adlc-unity.
- **AdMob mediation:** use for native Android/iOS projects.
- **AppLovin MAX:** strong alternative for native; single SDK, multi-network.

Register each network adapter once in the mediation dashboard, not per-placement.

## Ads vs IAP: the cannibalization concern

Non-paying users who engage with rewarded ads are **more** likely to convert to IAP,
not less. Rewarded ads let them experience premium content; the IAP tier is still the
faster path. The risk runs the other way: if a rewarded grant provides as much value as
the equivalent IAP, IAP conversion drops. Calibrate reward amounts to be meaningful but
sub-IAP in value. See the economy calibration notes in the detail reference.

Do not show ads to a player mid-IAP funnel (purchase dialog open, store browsing). Gate
interstitials off for recent payers (last 7 days minimum).

## Kids and behavioral ads: the policy flag

If the game targets under-13 content (ESRB E/E10+, Play Families, iOS Kids category):

- Behavioral/interest-targeted advertising is **prohibited** (COPPA 2025, Play Families,
  Apple Kids guidelines).
- Only certified, COPPA-compliant ad networks may serve ads (AdMob Families program,
  SuperAwesome, etc.).
- All ad content must be age-appropriate; no violence, gambling themes, or adult content.

Stop here and flag this to the operator. Detailed policy steps and the age-gate design
defer to **games-compliance** and **adlc-privacy**.

## Verify (pass/fail before shipping)

```
[ ] Test ad: a test/sandbox ad loads and displays; no production ad key in debug builds.
[ ] Rewarded callback: reward is granted inside the completion callback, not on close.
[ ] Frequency cap: run a QA session past the cap limit; confirm the dashboard cap fires.
[ ] No mid-action: trigger an interstitial attempt mid-gameplay; confirm it does not show.
[ ] Paying player gate: simulate a recent purchase; confirm interstitials are suppressed.
[ ] Kids flag: if under-13 audience, confirm behavioral targeting is off and only
    certified networks are active.
```

## Outbound checkpoint

Local work is free. Outbound here (publishing ad unit IDs, app keys, or mediation config to a live LevelPlay/AdMob/MAX dashboard, enabling an ad SDK that sends device data like IDFA/GAID, IP, or device signals to ad networks, or changing frequency caps on a live mediation dashboard): stop, present exactly what would go out, and get the operator's explicit "yes" first (global consent law).

## References

- [references/ads-mediation-detail.md](../../references/ads-mediation-detail.md) -- format comparison,
  frequency data, mediation table, economy calibration, verify checklist.
- Google AdMob mediation overview: https://developers.google.com/admob/android/mediation
- AppLovin MAX mediation: https://developers.applovin.com/en/max/android/overview/
- LevelPlay / IronSource mediation: https://developers.is.com/ironsource-mobile/
- Rewarded ads best practices (AppSamurai, Jun 2025): https://appsamurai.com/blog/rewarded-ads-in-mobile-games-strategy-data-and-best-practices/
- AdMob + bidding guide 2026 (Boomie Studio): https://boomiestudio.com/blog/admob-bidding-guide
- IAP + rewarded ads balance: https://blog.playio.co/balancing-iap-rewarded-ads-monetization
- COPPA 2025 compliance for kids apps: https://blog.promise.legal/startup-central/coppa-compliance-in-2025-a-practical-guide-for-tech-edtech-and-kids-apps/
- Play Families certified ad SDKs (SuperAwesome): https://www.superawesome.com/blog/helping-kids-developers-comply-with-googles-play-store-policy-update/
