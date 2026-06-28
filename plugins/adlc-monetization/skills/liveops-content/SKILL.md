---
name: liveops-content
description: >-
  This skill should be used when the user asks to "design the battle pass", "set up the
  live-ops calendar", "plan a limited-time event", "add daily login rewards", "run a
  season", "wire remote config to live ops", "ship content without a client update",
  "tune event rewards remotely", "keep F2P players engaged between updates", "design FOMO
  events that don't backfire", "plan the live-ops content loop", "design a season cadence",
  "set up a live-ops schedule", "make retention events", or "configure remote-config for
  a season". Covers the live-ops content loop that drives F2P retention and revenue:
  battle pass (free + premium tracks), limited-time events with honest FOMO, daily login
  chains, remote-config-driven content delivery, and calendar discipline. Engine-agnostic
  design; Unity SDK wiring defers to adlc-unity (unity-monetization-sdks). Store policy
  and gacha odds disclosure defer to the compliance packs.
version: 0.1.0
---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# liveops-content

Run the live-ops content loop that drives F2P retention and revenue. Engine-agnostic
design; SDK wiring defers to adlc-unity. Policy and odds disclosure defer to the
compliance packs.

## Detect first

Before designing anything, establish what is already live. For a Unity project:

```bash
grep -rn "RemoteConfigService\|GetInt\|GetString\|GetBool\|GetFloat" \
  Assets/ --include="*.cs" | grep -v "//.*Get" | head -30
grep -rn "BattlePass\|LiveOps\|Season\|DailyLogin" Assets/ --include="*.cs" -l
```

Record: remote-config backend, existing keys, whether a season or battle-pass system
exists in code, and what events have shipped. Mark anything unknown `unknown`. Do not
invent key names or assume defaults.

## Battle pass: retention and revenue backbone

Design the battle pass before planning events; everything else layers on top.

**Season cadence** (see references for detail):
- 4-week sprint: obstacle / hypercasual
- 6-week season: midcore auto-battler (Legion-TD)
- 8-week season: deep strategy / RPG

**Free track.** 30-40% of tiers. One cosmetic at halfway, one at the final tier.
Must feel rewarding enough that F2P players continue, but reserve the best items
for the premium track.

**Premium track.** $4.99-$9.99. Front-load desirable items in tiers 1-15 (drive
purchase before the player falls behind). End with the signature cosmetic. Return
60-80% of the pass cost as premium currency to completers: the "free next pass"
perception earns goodwill and avoids the Apex Legends / PUBG backlash pattern.

**Grind math.** Verify:
```
free_tiers / (missions_per_day * xp_per_mission / xp_per_tier) < (season_days - 2)
```
If it fails, cut tiers or lengthen the season; do not add grind.

**P2W constraint (operator context).** Lock cosmetics, status, and XP accelerators
behind the pass, never core combat power. Bracket payers via matchmaking so P2W
advantage is felt within a spending tier, not against the F2P population.

## Limited-time events and honest FOMO

FOMO that backfires is "urgency without value": a short event with mediocre rewards
trains players to ignore all future events. Use scarcity only when the reward
justifies the player's time.

**Three-layer event calendar:**
1. **Macro event** (4-8 weeks): the season itself; re-engagement anchor.
2. **Mid-cycle competition** (10-14 days): tournament or challenge; targets the
   D15 drop-off, the most dangerous retention cliff.
3. **Weekend blitz** (Fri 17:00 to Sun 23:59 local): flash IAP + XP multiplier;
   keep to 2-3 per season.

Keep 12-24 hours of dead air between events. Constant urgency = no urgency.

FOMO is honest when: the reward is unique and desirable, the grind is proportional
to the window, missing it does not break progression (cosmetic or status only), and
the end date is surfaced matter-of-factly, not as guilt.

## Daily login chains

Structure: Day 1 consumable, Day 3 premium currency (small), Day 5 cosmetic shard,
Day 7 meaningful currency or exclusive cosmetic. Give a 24-hour grace window on
streaks of 7 days or fewer. Punishing a real-life interruption loses a week of
retention with zero upside.

## Remote-config-driven content delivery

**Ship content as config, not as a client update.** Season starts, event activations,
price tests, and XP multipliers must all reach the live client from the dashboard
with no release.

Define a safe local default for every key in code. A failed remote-config fetch must
never crash the game loop or block a session. For the full key taxonomy, see the
references file. SDK wiring (fetch call, fallback handling, per-platform init) defers
to adlc-unity (unity-monetization-sdks).

## Live-ops calendar discipline

Maintain one source-of-truth calendar: season dates, `season_id` per platform,
event windows (epoch + timezone label), remote-config keys per event with their
scheduled values, and IAP SKUs active per window.

Sync the calendar to the remote-config backend so values flip at the scheduled
epoch automatically. A missed manual toggle is a broken event.

## Verify: remote-config reaches the client without a release

Run this pass/fail check before declaring live-ops "operational":

```
[ ] Change event_active from false to true on the dashboard.
    Client reflects the change within 5 minutes with no build push.
[ ] Set season_end_epoch to 3 minutes from now.
    Client countdown reaches zero and transitions correctly.
[ ] Kill network before launch.
    Client starts, uses local defaults, no crash, no blocked session.
[ ] Grind math check: F2P player at 1 mission/day completes the free
    battle-pass track by (season_length_days - 2).
```

Do not mark live-ops operational until every box passes.

## Outbound checkpoint

Local work is free. Outbound here (publishing remote-config values to the live dashboard, activating a live event, updating season end dates visible to players, or making price changes that reach production): stop, present exactly what keys and values would go live and to which environment, and get the operator's explicit "yes" first (global consent law).

## References

- [references/liveops-calendar.md](references/liveops-calendar.md): cadence tables, event type
  breakdown, daily login chain anatomy, remote-config key taxonomy, and the full
  verify checklist.
- Gamemakers, "Understanding Battle Pass Game Design":
  https://www.gamemakers.com/p/understanding-battle-pass-game-design
- Game Growth Advisor, "LiveOps Strategy for Mobile Games: The Complete Playbook" (2026):
  https://gamegrowthadvisor.com/blog/2026-03-31-liveops-strategy-mobile-games-guide/
- SplitMetrics, "A Full Guide to LiveOps in Games":
  https://splitmetrics.com/blog/a-full-guide-to-liveops-in-games-2024/
- Ruslan Valeev, "Essential Live Ops Calendar: Key Dates and Art for F2P Games":
  https://medium.com/@r_valeev/essential-live-ops-calendar-key-dates-and-art-for-f2p-games-fc750e10790c
