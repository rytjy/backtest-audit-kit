# Case 14 — a peer audit of a live account: 1,701 setups, 1,041 trades, one missing cost line

> Written 2026-11-06, with the account owner's written permission to name him.
> Subject: `BrockStar3540/mr-scrooge-v6`, issue #9 — a 20-day public exchange
> (2026-10-08 → 2026-10-29) between the owner and me. All numbers below are
> either his (cited) or mine, recomputed from files he published. Nothing here
> is a PnL claim about the strategy.

Thread: <https://github.com/BrockStar3540/mr-scrooge-v6/issues/9>

**Permission** (2026-10-28T14:48Z, verbatim):

> Citing this thread: yes. You can name me. I'm **Carl Brock, from Raleigh, NC**.
> You're welcome to write about me and the project, publish your backtests on our
> data, and credit it however you see fit. No need to send me the paragraph first.

## What the thread was

A live FX bot that had been running ~85 days. My opening challenge (2026-10-08)
was narrow: the admission bar's Benjamini–Hochberg correction runs over the
setups that reached their counting gates, not over everything ever scored — so
the multiplicity denominator was missing.

The owner's first reply conceded three points outright: the BH family is "the
docket, not the full search"; the hypothesis registry lived in a gitignored
`data/` directory, so nobody outside could measure the search; and **"No
deflated Sharpe or PBO has been run."**

## Half 1 — the owner ran the multiplicity audit himself

He pre-registered the prediction and the verdict rule first
(`research/deflation/PREREGISTRATION.md`, `48f82bf9`), then ran DSR and CSCV
PBO on a frozen copy of the shadow episodes. His summary line:

> It goes against the bar.

| item | value |
|---|---|
| hypotheses ever scored (M_ever) | 1,701 (M_live 1,619) |
| setups that ever held a seat | 163 |
| median daily SR of those 163 | 0.13 |
| best of 1,701 zero-skill trials | ≈0.67 daily SR |
| **median DSR (N=1,701)** | **0.00** (0/163 ≥ 0.95; 2 > 0.5) |
| median DSR at effective N≈42 | 0.01 |
| PBO, bar-replica predicate (S=16, 12,870 splits) | **0.03** |
| PBO, canonical best-in-sample (S=16) | 0.19 (~59th percentile) |

Sensitivity to closed-market stamps: dropping Saturdays (1,421 rows) gives
PBO_bar 0.034 (S=16) / 0.100 (S=8); dropping all closed-market stamps (2,696)
gives 0.041 / 0.086; median DSR stays 0.00; maxSR PBO moves 0.190 → 0.178 / 0.176.
So the weekend data does not drive the verdict.

**What I verified, and what I did not.** I downloaded the frozen input
(3,521,287 B), confirmed git blob sha1 `de73a281…` against the API, and the
gunzipped sha256 `e389bfd0…` against `results.json` and the registry at
`276ca5e0` — all match. I recomputed every field in `results.json` from the
published files. I did **not** re-run their registered pipeline end-to-end.

**The correction I contributed.** At N=1,701 over 85 days, a median DSR of 0.00
is close to structural — even their own equal-weight book (daily SR 0.364,
PSR 0.999) has DSR 0.0034. The honest statement is "this sample cannot separate
an edge from 1,701 searches", not "there is no edge". The owner accepted this
and amended the addendum: *"Measures the search" describes what the bar can
certify at this length, not proof of* no edge.

## Half 2 — the live tape, recomputed

He then published `livelog/trades.csv` and, later, `trades_detail_2026-10-28.csv`.

From 1,041 closed rows (2026-07-29 → 2026-10-28):

| metric | value |
|---|---|
| sum realized | **−$1,308.74** |
| mean / sd per trade | −1.257 / 13.60 |
| win rate | **78.29%** (815W / 226L) |
| avg win / avg loss | +4.01 / −20.26 |
| break-even win rate at that payoff | **83.47%** |
| gap to break-even | **−5.2 pp** |
| 95% CI on expectancy | **[−2.08, −0.43]**, t ≈ −3.0 |

The loss is not a coin flip: at 1,041 trades the standard error of the mean is
0.42, and the whole interval is below zero. The shape is the story — 78% wins,
but the average loss is five times the average win.

Two follow-ups on his data:

1. **Payoff grid** (368 trades with M1 history, three pairs, 07-29 → 10-01):
   sweeping stop × target from 0.75R to 3R, **every cell is negative**; best is
   1.25R stop / 1.0R target at −0.15 pips/trade, 95% CI [−5.20, +4.90]. Widening
   the target hurts monotonically.
2. **Sizing decomposition** (1,042 rows): the popper book's median risk is
   **1.42×** the parent's ($24.96 vs $17.59, CI 1.33–1.54) — but paired on
   instrument × month it is only 1.03× units and 1.08× stop width. The headline
   ratio is composition (September: 2.48×), not a standing rule.

## The missing line

Equity said −$1,435.97; realized fills said −$1,304.53. Difference: **−$131.44**
(9.6% of the total loss), uniform per trade at **0.24 pip** ($2.40 per $100k
round turn). I flagged it as a likely unlogged cost line — noting the direction
made his loss look *smaller*, not bigger.

His answer: it was overnight financing. Balance $2,500.00 → $1,068.24; realized
−$1,304.70 plus OANDA financing −$127.06 = −$1,431.76, to the cent. He also
volunteered that OANDA's half-spread on every fill sums to **$979.82** over the
live era — about three quarters of the realized loss was the spread.

## What this case is for

It shows the two halves of an audit that are usually sold separately:

- **Selection**: what the search itself costs (DSR 0.00, PBO 0.03–0.19).
- **Execution**: what the fills actually did (−1,308.74 before financing, a
  5.2 pp win-rate shortfall against the payoff's break-even).

And it shows the limit: with 85 days and 1,041 trades, the tape can measure a
negative expectancy (CI excludes zero) but cannot certify the absence of a
small edge. Reporting it as "the strategy loses" would be the same category
error as reporting DSR 0.00 as "no edge".

## Scope

- Owner-published numbers: registry counts, DSR, PBO, financing and spread
  totals. Verified by hash and by recomputation from `results.json`; not by
  re-running his pipeline.
- My numbers: the 1,041-row recomputation, the payoff grid (368 trades, M1,
  bid bars, no spread/slippage, 72h cap, both-touch counted as stop), and the
  sizing decomposition (bootstrap CIs, 2k resamples).
- Not covered: October trades and 14 of 17 pairs in the payoff grid (HistData
  monthly availability); the ratchet/reaper question, which stayed "likely
  harmful, not settled".
