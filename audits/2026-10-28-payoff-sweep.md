# Payoff-shape sweep: 18 fixed target/stop combinations, none positive

*2026-10-28. Replay of the public live-trade log from `BrockStar3540/mr-scrooge-v6` (`livelog/detail/trades_detail_2026-10-28.csv`) on HistData M1 bid bars.*

## Scope (read this first)

- **368 of 1,042 trades (35%)**: only EUR_USD, GBP_USD and USD_JPY, and only 2026-07-29 to 2026-10-01.
- October is missing: HistData publishes monthly M1 files after month end, so the 288 October trades (and 12 other pairs) are not in this test.
- Bid bars only, no spread, no slippage, no commission. When a bar touches both target and stop, it counts as a stop (conservative).
- Positions are held at most **72h**; anything still open is marked to market at the last bar.

## Method

Each trade keeps its real entry time and price and its real initial stop distance `R`. For each grid cell, the stop is `k x R` from entry and the target is `m x R`; the replay walks M1 bars forward until one is touched or 72h pass. Result is in pips.

## Results (mean pips per trade)

| stop \ target | 0.5R | 0.75R | 1.0R | 1.5R | 2.0R | 3.0R |
|---|---:|---:|---:|---:|---:|---:|
| **0.75R** | -2.17 | -2.07 | -3.12 | -2.77 | -3.17 | -3.39 |
| **1.00R** | -0.83 | -0.43 | -0.84 | -1.53 | -3.14 | -3.21 |
| **1.25R** | -0.87 | -0.36 | -0.15 | -0.93 | -2.88 | -3.25 |

**No combination is positive.** The best cell is 1.25R stop / 1.0R target at **-0.15 pips/trade**, 95% CI **[-5.20, +4.90]** — statistically indistinguishable from zero. The cell closest to a classic 1:1 (1.00R/1.00R) is -0.84 pips/trade.

For the same 368 trades, the **actual** realized result is **+0.12 pips/trade**. So the bot's real exit stack (ratchet + stale-red reaper) is already at least as good as any fixed target/stop in this grid. The fixed-grid overlay does not rescue the strategy.

## Why the dollars are worse than the pips

The full tape: 1,042 trades, mean **-1.88 pips** (median **+6.80**) and mean **-$1.25**. Winners average **+8.8p**, losers **-40.0p**, with a median initial stop of ~55p on both sides. So the exit stack caps wins near +9p while letting losers run to -40p, and the size on losers is slightly larger (5,632 vs 5,140 units). That is where the money goes — not into a target/stop setting that was left on the table.

## What this does not say

- It does not say no exit rule can work: only that none of these 18 fixed (stop, target) pairs, applied to these entries on these bars, is positive.
- It does not cover October (the worst month for the tape so far) or 12 of the 17 traded pairs.
- It does not model spread, so a real fill would be worse, not better.

## Reproduce

`sweep.py` in this directory rebuilds the table from `trades_detail_2026-10-28.csv` plus HistData M1 files for the three pairs.
