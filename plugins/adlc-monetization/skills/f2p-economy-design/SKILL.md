---
name: f2p-economy-design
description: >-
  Designs and balances a F2P monetization layer: dual-currency architecture, IAP pricing
  tiers, P2W discipline, gacha with pity and odds disclosure, and whale-ladder/VIP.
  Use this skill when the user asks to "design the game economy", "balance soft and hard
  currency", "design IAP pricing or a starter pack", "tune gacha rates or add a pity
  system", or "simulate currency flow and check funnel health".
version: 0.1.0
---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# F2P economy design

Design a monetization layer that earns hard at the top of the spend pyramid without
hollowing out the F2P base. The tension: the most aggressive gacha shrinks TAM via
regulation and churn; the right level sells aspiration, not frustration.

## Detect first

Inspect any existing economy before proposing changes:

```bash
# Config files, balance sheets, remote config keys
find . -iname "*.json" -o -iname "*.csv" | xargs grep -l "currency\|gem\|coin\|price\|pity" 2>/dev/null | head -20
grep -rn "hardCurrency\|softCurrency\|gemPrice\|pityCount\|gachaRate" . --include="*.cs" --include="*.kt" --include="*.swift" | head -30
```

Record: currency names, current IAP product IDs and prices, any existing pity counter
logic, matchmaking parameters. Mark unknowns as `unknown`; do not invent balances.

## Step 1: Dual-currency architecture

Define two currencies and keep their roles separate:

| Currency | Earned by | Spent on | F2P monthly earn rate |
|---|---|---|---|
| Soft (gold/coins) | Gameplay, dailies, quests, rewarded ads | Upgrades, crafting, energy refills | Enough for 1 meaningful upgrade/week |
| Hard (gems/crystals) | Rare event login, battle pass trickle | Premium gacha, skip timers, cosmetics | 20-60 gems/month (IAP = 5-30x faster) |

Run the sink/source balance check in [references/f2p-economy.md](../../references/f2p-economy.md) before coding any values.

## Step 2: IAP pricing + anchoring

Implement five tiers plus a time-gated starter pack:

| Tier | USD | Purpose |
|---|---|---|
| Entry / first-purchase doubler | $0.99-$1.99 | Converts fence-sitters; 2x hard currency on first buy only |
| Starter pack | $4.99 | Gate to 48-72 h post-install; deepest value ratio |
| Mid | $9.99 | Repeat purchase; 3-5x entry value |
| Large | $19.99 | Occasional big pull |
| Anchor | $49.99-$99.99 | Makes mid look reasonable; also serves top spenders |

Fetch prices at runtime: `product.displayPrice` (StoreKit 2) / Play Billing
`ProductDetails.getOneTimePurchaseOfferDetails().getFormattedPrice()`. Never hardcode
price strings. Localize per-territory in App Store Connect and per-product in Play
Console (pricing templates removed Oct 2025; set every product individually).

## Step 3: P2W discipline (sell speed and status, not outcome)

Prohibited: pay-only units/items with superior base stats; PvP where $1000 spend
one-shots a fully-progressed F2P player at equal skill.

Permitted: XP boosters, timer skips, energy refills (speed); cosmetics with zero stat
impact (status); roster breadth where enough slots are F2P-earnable to compete.

**Bracket payers via matchmaking.** Cluster by power rating (not just skill MMR) so high-
spend accounts face each other. Track F2P D30 retention after every P2W feature ship; a
drop >5 pp below baseline means the feature is too aggressive. Whales need F2P to fight.

## Step 4: Gacha with pity and disclosed odds

Minimum viable pity (adjust via Remote Config, not hardcode):

| Tier | Base rate | Soft pity starts | Hard pity (guaranteed) |
|---|---|---|---|
| Rare (4-star) | 5-10% | Pull 20 | Pull 10 |
| Epic (5-star) | 0.6-1.5% | Pull 60 | Pull 90 |

Soft pity: linear rate increase after the threshold. Pity carries across banner rotations.

**Odds disclosure (required by Apple, Google, FTC).** Apple Guideline 3.1.1 and Google
Play policy both require disclosing odds *before* purchase. FTC enforcement (Cognosphere/
Genshin, $20 M settlement, 2025) adds US deceptive-practice exposure. Add a
tap-to-expand "Drop rates" table in every gacha UI before the purchase button; list exact
percentages per rarity tier and per named item where individual rates differ.

**Geo-softening knob.** Store all gacha rates in a `gacha_config` Remote Config key per
market. Set Belgium/Netherlands to `disabled`; apply South Korea/Japan's mandated rate
floors and disclosure formats without a binary release. As new markets regulate, update
the server config. Legality detail defers to the games-compliance pack.

## Step 5: Whale ladder / VIP

Structure VIP levels on cumulative lifetime spend. Perks must be status/cosmetics/
service, not match-outcome advantages. See the full tier table in
[references/f2p-economy.md](../../references/f2p-economy.md).

## Step 6: Economy sim (pass/fail before launch)

Run the spreadsheet simulation in [references/f2p-economy.md](../../references/f2p-economy.md)
against three archetypes (F2P casual, F2P active, Dolphin $10/mo) before any live
tuning. Gate: each archetype hits a meaningful upgrade at least once per week and the
Dolphin does not max their account in week 1.

## Step 7: Verify funnel health

```
[ ] Soft-currency net for F2P casual hits 0 naturally ~3x/week (creates an ad/spend trigger).
[ ] F2P D1 retention >= 40%; D7 >= 20%; D30 >= 8%.
[ ] Day-7 IAP conversion 2-5%; outside that range investigate before scaling UA.
[ ] F2P D30 retention does not drop >5 pp after any new P2W feature ships.
[ ] Every gacha UI shows a "Drop rates" table before the purchase button.
[ ] Gacha rates and geo-gate config are Remote Config keys, not hardcoded.
[ ] Starter pack correctly gates to first 48-72 h per install (not per account).
[ ] Price strings come from store APIs at runtime, no hardcoded values.
```

## Outbound checkpoint

Local work is free. Outbound here (publishing Remote Config changes live to players, pushing IAP product definitions to App Store Connect or Play Console, or enabling live gacha banners on a backend server): stop, present exactly what would go out (product IDs, prices, rates, affected markets), and get the operator's explicit "yes" first (global consent law).

## References

- [references/f2p-economy.md](../../references/f2p-economy.md) - currency/sinks/pricing/gacha
  patterns, funnel-health metrics, economy sim, whale-ladder tiers
- Apple App Store Guideline 3.1.1 (loot box odds disclosure):
  https://developer.apple.com/app-store/review/guidelines/#in-app-purchase
- Google Play loot box odds policy:
  https://www.fenwick.com/insights/publications/google-play-now-requires-disclosure-of-loot-box-odds
- FTC / Cognosphere (Genshin) settlement 2025:
  https://www.bleepingcomputer.com/news/gaming/ftc-cracks-down-on-genshin-impact-gacha-loot-box-practices/
- Loot box law by jurisdiction 2025:
  https://blog.promise.legal/loot-box-laws-game-developers/
- GDC "Where the Whales Live" (F2P pyramid model):
  https://www.gdcvault.com/play/1019671/Where-the-Whales-Live-The
- StoreKit 2 + Play Billing pricing detail: see [references/f2p-economy.md](../../references/f2p-economy.md)
