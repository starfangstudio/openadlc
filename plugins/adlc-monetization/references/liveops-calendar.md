<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
# Live-ops calendar reference

Companion to the `liveops-content` skill. Use as a lookup; the skill body
is the authoritative workflow.

---

## Season cadence options

| Cadence | Tier count | Best for |
|---|---|---|
| 4-week sprint | 50-60 tiers | Hypercasual / obstacle games; fast content refresh |
| 6-week season | 70-80 tiers | Midcore auto-battler (Legion-TD style) |
| 8-week season | 90-100 tiers | Content-heavy RPG / deep strategy |

Rule of thumb: a player doing one daily mission should complete the free
track with ~1-2 days to spare. If the math fails, shorten the season or cut
tiers before adding grind.

## Free vs. premium track split

- Free track: 30-40% of tiers. Mix XP boosts, consumables, one cosmetic at
  the halfway point, one cosmetic at the last tier. Serves as the "sample" that
  converts to premium.
- Premium track: every tier has something. Weight early tiers (1-15) with
  desirable items to drive purchase before the player falls behind. End the
  track with the signature cosmetic (character skin, arena effect, avatar frame).
- Currency rebate: return 60-80% of the pass cost in premium currency to
  committed completers. This creates a "free next pass if you finish" perception
  and earns sustained goodwill.

## Limited-time event types

| Type | Window | Function |
|---|---|---|
| Weekend blitz | Fri 17:00 - Sun 23:59 (player local) | Monetization spike; flash IAP offer |
| Mid-season tournament | 10-14 days | Re-engagement at D14-D21 of a season |
| Holiday overlay | 7-21 days | Seasonal cosmetics; high-impulse IAP |
| Collab / IP event | 14-28 days | New user acquisition + press |

Keep 12-24 hours of dead air between back-to-back events. Players disengage
permanently when every minute is "urgent".

## Daily login chain anatomy

```
Day 1  → consumable (low cost)
Day 2  → premium currency (small)
Day 3  → cosmetic shard or loot box
Day 5  → meaningful consumable or functional item
Day 7  → premium currency (meaningful) OR exclusive cosmetic
```

Rules:
- Do not reset the streak to zero on a single missed day for streaks <= 7 days;
  give a 24-hour grace window. Punishing a real-life interruption loses a week
  of retention with no upside.
- Streak breakage is fine at longer milestones (30-day streak = prestige reward),
  but never make the gap insurmountable.

## Remote-config key taxonomy (engine-agnostic)

| Key | Default example | Notes |
|---|---|---|
| `season_id` | `"s4"` | Change triggers event-start client-side |
| `season_end_epoch` | `1754006400` | Client countdown driven from this |
| `bp_premium_price_cents` | `999` | Override per region/test |
| `event_active` | `false` | Feature flag; ship the event dark |
| `event_multiplier` | `1.0` | XP/reward multiplier during event |
| `daily_offer_sku` | `"daily_deal_gems_1000"` | Rotate without releasing |
| `interstitial_cap_minutes` | `7` | Ad pacing; tune without release |

Always define a safe local default in code. A failed remote-config fetch must
never break the game loop.

## Verify checklist (pass/fail)

```
[ ] Change a remote-config key on the dashboard; client reflects it within 5 min
    without a release.
[ ] Set season_end_epoch to 2 minutes from now; client countdown reaches zero and
    transitions correctly.
[ ] Set event_active=true; event UI appears without a client build push.
[ ] Kill network; client starts and uses local defaults; no crash.
[ ] Battle-pass tier count: F2P player at 1 daily mission/day completes free track
    by (season_length_days - 2).
[ ] Mid-season D15 DAU target vs. D1 DAU: aim for >= 40% retention at this point.
```
