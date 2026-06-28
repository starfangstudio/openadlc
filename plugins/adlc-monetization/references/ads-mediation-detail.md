<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
# Ads mediation: detail reference

Linked from `skills/ads-mediation/SKILL.md`. Load on demand.

## Rewarded vs interstitial at a glance

| Format | Player opt-in | Placement rule | Frequency (per session) | Retention signal |
|---|---|---|---|---|
| Rewarded video | Yes (watch for reward) | Tie to a meaningful economy reward; surface at a moment of need (out of lives, energy, retry) | 2-5 opt-in shows; cap at 8 before churn risk rises sharply | Non-paying users who engage are 4x more likely to convert to IAP |
| Interstitial | No | Level end / natural break only; never mid-action, never on death | 1-3 per session max; never back-to-back | Drops sharply if overused; use sparingly for non-paying cohorts only |

## Mediation: waterfall vs in-app bidding

**Waterfall (legacy):** networks ranked by historical eCPM in a static order. First in the list that fills wins. Under-monetizes because a lower-ranked network may pay more for a specific impression.

**In-app bidding (current standard):** all participating networks submit a real-time price; the auction winner fills. Unity/LevelPlay deprecated waterfall-only in 2025. Default to bidding.

**Hybrid:** keep a static waterfall fallback behind the bidding pool for networks that do not support real-time bidding.

## Platform-specific mediation SDKs

| Platform | Primary SDK | Notes |
|---|---|---|
| Unity games | LevelPlay (IronSource) | Wire via `adlc-unity/unity-monetization-sdks`; do not re-document here |
| Native Android | Google AdMob / MAX (AppLovin) | Direct SDK; integrate via Play Billing layer |
| Native iOS | Google AdMob / MAX (AppLovin) | Gate init on ATT; see ios-store-compliance |
| Cross-platform native | AppLovin MAX | Single SDK, multi-network |

## Verify checklist

```
[ ] Test ad loads and displays in sandbox/test mode (not a production ad).
[ ] Rewarded callback fires BEFORE reward is granted (not on ad close).
[ ] Interstitial: never fires mid-action (map is open, animation playing, etc.).
[ ] Frequency cap: confirm dashboard cap enforces 4-8/session limit in QA session.
[ ] Kids flag: if targeting under-13, confirm behavioral targeting is disabled
    and only certified ad networks are active.
[ ] No ad request made before ATT result on iOS (LevelPlay/AdMob gate).
```

## Economy calibration for rewarded ads

- Rewarded currency amount: meaningful but not sufficient. If a single rewarded grant covers an IAP-tier amount, IAP conversion drops.
- Soft-currency drain rate determines how often players hit a natural ad trigger (out of energy, retry, etc.). Tune the drain to create genuine moments of need, not artificial walls.
- Non-paying players: rewarded ads are their primary progression valve. Keep the experience honest -- an ad should feel like a shortcut, not a tax.

## References (external)

- AdMob mediation overview: https://developers.google.com/admob/android/mediation
- AppLovin MAX mediation: https://developers.applovin.com/en/max/android/overview/
- LevelPlay (IronSource) mediation: https://developers.is.com/ironsource-mobile/
- Rewarded ads best practices (AppSamurai, Jun 2025): https://appsamurai.com/blog/rewarded-ads-in-mobile-games-strategy-data-and-best-practices/
- F2P monetization 2026 comparison (Game Growth Advisor): https://gamegrowthadvisor.com/blog/2026-04-02-f2p-monetization-models-comparison-2026/
- IAP + rewarded ads balance (Playio): https://blog.playio.co/balancing-iap-rewarded-ads-monetization
- Frequency cap + retention data: https://coinis.com/glossary/rewarded-video
