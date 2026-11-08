# Work Sample 02 — One rule, audited end to end

> Status: reproducible demo, **not** an alpha claim. The honest result is that this rule does not survive.

## Data and execution

- **Asset**: BTCUSDT, daily bars, 2019-01-01 → 2026-09-30 (2,768 bars, 7.75 years)
- **Source**: `data.binance.vision` monthly kline archives (public, no key); fetched 2026-11-08
- **Signal**: RSI(14) computed on closes; enter when RSI < entry threshold at close *t*
- **Execution**: enter at open *t+1* (no look-ahead), exit when RSI > exit threshold or after 10 days
- **Costs**: 10 bps per side, long only, no leverage, full equity
- **Split**: first 70% in-sample, last 30% out-of-sample, fixed before looking

## Results (all 9 variants, not just the best)

| entry | exit | IS CAGR | OOS CAGR | trades | Max DD |
|---|---|---|---|---|---|
| 25 | 50 | 3.7% | -1.7% | 14 | -17.3% |
| 25 | 55 | 3.7% | -5.4% | 14 | -17.3% |
| 25 | 60 | 3.7% | -5.4% | 14 | -17.3% |
| 30 | 50 | 10.9% | 3.7% | 24 | -16.5% |
| 30 | 55 | 9.1% | 0.1% | 24 | -18.4% |
| 30 | 60 | 10.4% | -0.3% | 24 | -18.4% |
| 35 | 50 | 10.3% | 4.8% | 48 | -42.3% |
| 35 | 55 | 8.5% | 3.3% | 48 | -42.3% |
| 35 | 60 | 11.0% | 0.7% | 48 | -42.3% |

## What the numbers say

1. **The best in-sample variant loses most of its edge out of sample.** Best IS = 11.0% CAGR (entry 35 / exit 60); the same variant out of sample = 0.7%. Decay ≈ 10.2 pp.
2. **Parameter choice moves the answer more than the market does.** IS CAGR ranges 3.7%–11.0% across nine variants of the same rule — that spread is the search, not the signal.
3. **The variant with the most trades has the worst drawdown** (-42.3% vs -17% for the low-frequency ones). More exposure did not mean better risk-adjusted return.
4. **After 10 bps per side, none of these beat buy-and-hold on a risk-adjusted basis** (not shown here, but the OOS CAGR of 0.1%–4.8% with 16%–42% drawdown is not a favourable exchange).

## Conclusion

On this sample, RSI(14) mean reversion on daily BTC does not produce a stable edge. The honest deliverable is the process: fixed split, all trials reported, costs included, and the negative result stated plainly.

## Limitations (scope)

- Single asset, daily bars; no intraday or cross-sectional test.
- 9 trials only; no CSCV/PBO or deflated Sharpe — those need the full trial matrix from a real search.
- Slippage and funding ignored; fees fixed at 10 bps.
- Binance Vision timestamps arrive in mixed units (ms before 2025, µs after); the loader normalises them, and the fix is in `fetch_data.py`.

## Reproduce

```
python3 fetch_data.py   # downloads btc_daily.csv from data.binance.vision
python3 case.py         # writes results.json, prints the table
```
