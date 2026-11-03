# Multi-scale search is still search

**Claim.** If you tuned the same parameter grid on *k* time frames, your effective number of trials is `N × k`, not `N`. The deflated-Sharpe bar is a best-of-N bar, and every extra frame is another ticket in the same lottery.

## Why the frame axis counts

A multi-scale workflow asks one question per frame: *does this configuration work on this horizon?* Each answer is a comparison against noise, so each one spends significance. The bar rises as `sqrt(2 ln N / T)`, which means the cost of doubling N is not linear — it is the log, but it is still real.

## Worked example

400 return periods, per-period Sharpe 0.11:

| Trial bookkeeping | N | Bar | Adjusted p | Verdict |
|---|---|---|---|---|
| 2 configs, one frame | 2 | 0.059 | 0.028 | PASS |
| 2 configs × 10 frames | 20 | 0.122 | 0.28 | FAIL |

The strategy did not change. Only the count of things you looked at changed.

## Running it

```bash
python3 -m auditkit.cli trades.csv --trials 100 --timeframes 5
```

```
[multiple testing] FAIL
   FAIL  每期 SR 0.08 < 门槛 0.12（N_eff=500 = 你报的 100 组 × 5 个时间框架，校正后 p=1）
   WARN  多尺度搜索膨胀：只按 N=100 判 PASS（门槛 0.06），把 5 个时间框架计入后判 FAIL（门槛 0.12）
```

JSON output carries `timeframes`, `trials_effective` and `multiscale_inflation`.

## When not to multiply

If the frame was **pre-registered** — chosen before you looked at the data — then it is one hypothesis, and `k = 1`. The rule counts *searches*, not *mentions of time*. Tuning 5 frames and reporting the best one is 5 searches; deciding in advance to trade the daily frame is 1.

## Scope and limits

- This is bookkeeping, not proof. It says how many settings were looked at; it does not by itself prove the edge is fake.
- Frames on the same price series are correlated, so `N × k` is an upper bound on *independent* trials. We report the count because it is auditable and it errs toward the number you can defend in public.
- It inherits every assumption of the underlying deflated-Sharpe check: i.i.d. periods, normal approximation, Sharpe as the summary statistic.

*Shipped in v0.2.0. Code: `auditkit/cli.py` — `check_multiple_testing(..., timeframes=k)`.*
