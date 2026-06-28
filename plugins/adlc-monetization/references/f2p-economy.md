<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
# F2P economy: currency, sinks/sources, pricing, gacha, funnel health

Linked from `skills/f2p-economy-design/SKILL.md`. Load on demand.

---

## Dual-currency architecture

| Currency | Acquisition | Sink | Design rule |
|---|---|---|---|
| Soft (gold, coins, energy) | Gameplay, dailies, events, rewarded ads | Crafting, upgrades, energy refills, gacha (partial) | Sources must always exceed sinks at the F2P pace; restrict enough to create desire, not frustration |
| Hard (gems, crystals) | Real-money IAP, rare event login bonuses | Premium gacha, skip timers, cosmetics, starter pack | Hard currency earnable for free at a trickle (20-60/month F2P); IAP buyers get 5-30x that rate |

**Inflation kill switch.** Model monthly soft-currency in vs. out on a spreadsheet. If a top-50-percentile F2P player accumulates more than 3-4 weeks of spending power without a natural sink, prices erode. Add a rotating limited-time sink (event bundle, special upgrade slot) before it goes live.

---

## Sink / source balance checklist

```
[ ] List every source of soft currency (daily login, match reward, quest, ad).
[ ] List every sink (shop item, upgrade tier, energy refill, gacha).
[ ] Compute monthly net for three player archetypes: F2P casual, F2P active, low spender.
[ ] F2P casual: net soft should reach 0 naturally ~3x/week (creates an ad/spend trigger).
[ ] F2P active: should afford one meaningful upgrade per week via effort.
[ ] Hard currency: F2P earns enough for 1-2 guaranteed-pity pulls per month max.
```

---

## IAP pricing tiers and anchoring

Standard price points (USD; localize via StoreKit 2 / Play Billing per-country):

| Tier | Price | Role |
|---|---|---|
| Entry / Doubler | $0.99-$1.99 | First-purchase hook; a "first purchase doubler" (2x hard currency on first buy) converts fence-sitters |
| Starter pack | $4.99 | Time-gated (48-72 h from first session); deepest value per dollar; converts new players |
| Mid | $9.99 | Bread-and-butter repeat buy; 3-5x value of entry |
| Large | $19.99 | Occasional big pull |
| Whale anchor | $49.99-$99.99 | Anchor price that makes mid look reasonable; also serves top spenders |
| VIP / season pass | $4.99-$9.99/month | Subscription for daily drip of hard currency + cosmetics; sustains LTV |

**Anchoring rule.** Always show a higher-price option before the target tier. A $9.99 gem pack reads differently on a screen that also shows $49.99 and $99.99.

**Localization.** StoreKit 2 `product.displayPrice` + Play Billing's per-country price (set in Play Console per product since pricing-template deprecation, Oct 2025). Never hardcode price strings.

---

## P2W discipline: sell speed and status, not outcome

Forbidden P2W (shrinks TAM, triggers regulatory and community backlash):
- Selling units or equipment with higher base stats exclusively for money.
- PvP matchmaking that lets a $1000 account one-shot a fully-progressed F2P account with equal skill.

Permitted P2W (generates revenue without killing the funnel):
- Progression speed: sell XP boosters, crafting timers, energy refills. A player who paid gets the same end-state 2x faster.
- Cosmetics: skins, emotes, banners. Revenue with zero match-outcome effect.
- Roster breadth: buying more heroes/characters lets you explore the meta. Enough slots are earnable F2P to compete.

**Bracket payers via matchmaking.** Cluster players by power rating (not just skill MMR) so high-spend accounts face each other more. A fully maxed whale needs a living F2P population to fight; protect that population. Track the metric: if F2P day-30 retention drops below the baseline after a new P2W feature ships, it is too aggressive.

---

## Gacha / loot patterns

### Base rates and pity

Minimum viable gacha with disclosed odds:

| Tier | Soft pity start | Hard pity (guaranteed) | Base drop rate |
|---|---|---|---|
| Rare (4-star) | ~20 pulls | 10 pulls guaranteed | 5-10% |
| Epic (5-star) | ~60 pulls | 90 pulls guaranteed | 0.6-1.5% |

Soft pity: base rate increases linearly after the soft-pity threshold (e.g., +6% per pull after pull 60).

**Pity carry-over:** pity counter survives banner rotation. Players who know their pity persists plan spending instead of abandoning.

### Odds disclosure (required, not optional)

Apple App Store Review Guideline 3.1.1: disclose odds of each item type *before* purchase.
Google Play policy: same requirement.
FTC (US): enforcement under unfair/deceptive practices authority; Sept 2025 FTC action against Cognosphere ($20 M settlement) established that obscuring odds or targeting minors is actionable.

Implementation: show a tap-to-expand "Details / drop rates" table in every gacha UI before the purchase button. Present exact percentage for each rarity tier plus each named item where its individual rate differs from the tier rate.

### Geo-softening knob

A single `GachaConfig` remote config key per market lets you adjust rates without a release:
- Default (global): standard rates above.
- Belgium / Netherlands: set to `disabled` (randomized IAP is legally uncertain there).
- South Korea / Japan: comply with local mandatory odds disclosure + rate floor laws; rates and display format may differ.
- Additional markets: expand as enforcement evolves. Never hardcode market logic in client binary; keep it server-driven.

---

## Whale ladder / VIP

Structure whale spend to compound loyalty:

| VIP level | Cumulative spend | Perks |
|---|---|---|
| 1 | $5 lifetime | Daily hard-currency drip, exclusive shop tab |
| 3 | $50 lifetime | Priority support slot, bonus pull % |
| 5 | $200 lifetime | Named in credits, unique cosmetic, early event access |
| 10 | $1000 lifetime | Direct line to dev team, custom clan badge |

Perks must be status/cosmetic/service, not match-outcome advantages, to avoid the P2W trap at scale.

---

## Funnel-health metrics (alert thresholds)

| Metric | Healthy | Investigate |
|---|---|---|
| D1 retention | >= 40% | < 35% |
| D7 retention | >= 20% | < 15% |
| Day-7 conversion rate (any IAP) | 2-5% | < 1% or > 10% (churn spike) |
| F2P D30 retention | >= 8% | < 5% (P2W too aggressive) |
| ARPU (avg all users) | depends on genre; track trend | Drops > 15% MoM without a content gap |
| Rewarded ad eCPM impact on IAP | neutral or positive | IAP drops when rewarded rate increases |

---

## Economy sim (spreadsheet sanity check)

Before tuning live, run a simulation:

1. Define 3 archetypes: F2P casual (30 min/day), F2P active (2 h/day), Dolphin ($10/mo).
2. Simulate 30 days of soft and hard currency flow: sources (dailies, match rewards, events) vs. sinks (upgrades, gacha).
3. Check each archetype hits a meaningful upgrade at least once per week.
4. Verify the Dolphin does not max out their account in week 1 (leaves no aspiration ladder).
5. Adjust drain rates until the simulation is satisfactory, then set the values in Remote Config keys (not hardcoded).

---

## References

- F2P economy design (GDC, "Where the Whales Live"): https://www.gdcvault.com/play/1019671/Where-the-Whales-Live-The
- Apple App Store Review Guideline 3.1.1 (loot box odds): https://developer.apple.com/app-store/review/guidelines/#in-app-purchase
- Google Play loot box odds policy: https://www.fenwick.com/insights/publications/google-play-now-requires-disclosure-of-loot-box-odds
- FTC / Cognosphere (Genshin) settlement: https://www.bleepingcomputer.com/news/gaming/ftc-cracks-down-on-genshin-impact-gacha-loot-box-practices/
- Loot box law by jurisdiction 2025: https://blog.promise.legal/loot-box-laws-game-developers/
- F2P IAP monetization models 2026: https://blog.solar-engine.com/en-blog/docs/casual-games-iap-monetization-strategies
- StoreKit 2 pricing (displayPrice): https://medium.com/@dhruvinbhalodiya752/mastering-storekit-2-in-swiftui-a-complete-guide-to-in-app-purchases-2025-ef9241fced46
- Google Play pricing per-country (post pricing-template deprecation): https://newsletter.pricepush.app/p/google-play-pricing-templates-are
