# Case 5 — Cost omission: a take-profit smaller than one round trip

**Symptom.** A high-turnover strategy backtested at 50x reported **+30%** over
~83 days with **749 round trips** and a clean equity curve. No fee, funding or
slippage line appeared anywhere in the engine.

**Root cause.** The engine credited PnL on every close but never *debited* a
cost. `bal += margin * pnl_pct / 100` was the only balance mutation in the
loop — no taker fee, no per-bar funding, no spread. The reported profit was the
gross move, not the net one.

**Why it is fatal here, not merely optimistic.** A 50x move needs only a
**+0.08%** price change to reach a take-profit of `+4` (percent of margin):
`0.08% * 50 = 4`. But one round trip at the venue's taker fee of 4.5 bps per side is
**0.09%** of notional. The target is *smaller than the toll*:

| Quantity (as % of notional) | Value |
|---|---|
| Take-profit target (4% of margin at 50x) | **0.08%** |
| Round-trip taker fee (4.5 bps x 2)         | **0.09%** |

So a winning trade, once its own costs are charged, is a loser. No amount of
signal quality fixes an edge below the toll.

**What the checker found.** Reconstructing per-trade notional and holding bars
and running `auditkit.checks.fees.check_trades`:

| Rule | Count |
|---|---|
| `ONE_SIDED_FEE` (no fee recorded at all)   | 749 |
| `FUNDING_ONCE` (funding not charged per bar) | 162 |
| **total** | **911** |

**What the costs would have been** (in the audited book; venue taker fee 4.5 bps/side, funding 1 bp/bar
funding, 2 bps/fill slippage; notional 400 per side):

| Item | Amount |
|---|---|
| Reported gross profit | **+24.2** |
| Fees | 269.6 |
| Funding | 40.1 |
| Slippage | 119.8 |
| **Total cost** | **429.6** |

Cost is **~5.4x the starting capital** and **~17.8x the reported profit**. Even on
a maker-only assumption (2 bps/side) the fees alone (119.8) exceed the capital.

**Bottom line.** The headline number was an artifact of charging nothing. In a
high-turnover strategy, **cost is the strategy**: if the average edge per trade
is below the round-trip toll, the backtest's profit cannot exist live. Write the
cost model first, then the signal.

**Caveats.** The fee is the venue's real taker rate (4.5 bps/side); funding
and slippage are tool-default placeholders — calibrate both to your venue.
Notional is taken as margin x leverage. Absolute numbers scale with all three —
the structural point (target < toll) does not.

**How to reproduce.** `python3 cases/repro_cost_omission.py` charges the venue rate
against a same-shape book of zero-cost round trips and prints the toll-vs.
target arithmetic. Per-item totals move with the holding-bar mix (the repro's
own book differs slightly from the audited one); the structural point does not.
Anonymized: no venue, symbol or account data.
