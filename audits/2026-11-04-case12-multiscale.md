# Case 12 — the same 333 trades, three verdicts

> Written 2026-11-04. Companion to the v0.2.0 release. Everything below is
> reproducible from this repository plus one public daily kline file.

## The backtest

| item | value |
|---|---|
| data | Binance BNB/USDT daily klines, 2019-01-03 to 2026-06-18 |
| rule | daily close <= -3.0% vs previous close -> long at that close, exit at the next daily close |
| position | one at a time, re-entry blocked for the exit day |
| cost | 15bp round trip |
| trades | 333 |
| total return | +1062.4% (unlevered, before funding) |
| per-trade mean | +0.87% |

Regenerate with `python3 cases/12-multiscale/build_bnb.py`; it writes
`cases/12-multiscale/bnb_trades.csv` from the kline file and prints the same
three totals.

## Verdict A — `--trials 20 --timeframes 1`

The count most people report: five drop thresholds x two hold periods x two
cost assumptions, all tuned on the daily chart.

```

auditkit -- cases/12-multiscale/bnb_trades.csv  (333 rows, 333 return periods, return 列)
==============================================================================

[look-ahead] UNVERIFIED
   WARN       1 笔 entry==exit 价格：零持有（同 bar 进出）在多数市场不可成交
   UNVERIFIED 没有 --ohlc：只能查时间戳，价格级前视（用当根 bar 收盘/极值成交）判不了

[multiple testing] PASS
   PASS       每期 SR 0.17 > 门槛 0.13（N=20，校正后 p=0.024）—— 越过「最好的一次尝试」线

[out-of-sample decay] WARN
   WARN       前半 SR 2.06 -> 后半 SR 0.53，衰减 74%：超过一半的边没走到样本外；三段均值符号 ++-

------------------------------------------------------------------------------
legend: PASS 过了 / WARN 有痕迹 / FAIL 站不住 / UNVERIFIED 缺输入，判不了 / NODATA 没数据
```

Exit code 2 (one UNVERIFIED, no FAIL). The multiple-testing line is **PASS**,
p = 0.024.

## Verdict B — same file, `--trials 20 --timeframes 5`

Identical trade list, identical data. The only difference: those same five
thresholds were also tuned on 5m, 15m, 1h, 4h and 1d charts, so the effective
search is 20 x 5.

```

auditkit -- cases/12-multiscale/bnb_trades.csv  (333 rows, 333 return periods, return 列)
==============================================================================

[look-ahead] UNVERIFIED
   WARN       1 笔 entry==exit 价格：零持有（同 bar 进出）在多数市场不可成交
   UNVERIFIED 没有 --ohlc：只能查时间戳，价格级前视（用当根 bar 收盘/极值成交）判不了

[multiple testing] FAIL
   FAIL       每期 SR 0.17 < 门槛 0.17（N_eff=100 = 你报的 20 组 × 5 个时间框架，校正后 p=0.12）—— 与「试了 N_eff 次里最好的那次」不可区分
   WARN       多尺度搜索膨胀：只按 N=20 判 PASS（门槛 0.13），把 5 个时间框架计入后判 FAIL（门槛 0.17）—— 每个时间框架上的参数也是一次搜索。

[out-of-sample decay] WARN
   WARN       前半 SR 2.06 -> 后半 SR 0.53，衰减 74%：超过一半的边没走到样本外；三段均值符号 ++-

------------------------------------------------------------------------------
legend: PASS 过了 / WARN 有痕迹 / FAIL 站不住 / UNVERIFIED 缺输入，判不了 / NODATA 没数据
```

Exit code 1. **FAIL**, p = 0.12, plus the inflation WARN naming the flip:
PASS at N=20 (threshold 0.13) -> FAIL at N_eff=100 (threshold 0.17).

Nothing about the strategy changed between A and B. Only the accounting did.

## Verdict C — `--trials 576 --timeframes 1`

The count that matches what was actually run here: 8 coins x 3 start dates x
6 drop thresholds x 4 hold periods = 576 configurations scanned before this one
was chosen.

```

auditkit -- cases/12-multiscale/bnb_trades.csv  (333 rows, 333 return periods, return 列)
==============================================================================

[look-ahead] UNVERIFIED
   WARN       1 笔 entry==exit 价格：零持有（同 bar 进出）在多数市场不可成交
   UNVERIFIED 没有 --ohlc：只能查时间戳，价格级前视（用当根 bar 收盘/极值成交）判不了

[multiple testing] FAIL
   FAIL       每期 SR 0.17 < 门槛 0.20（N=576，校正后 p=0.7）—— 与「试了 N 次里最好的那次」不可区分

[out-of-sample decay] WARN
   WARN       前半 SR 2.06 -> 后半 SR 0.53，衰减 74%：超过一半的边没走到样本外；三段均值符号 ++-

------------------------------------------------------------------------------
legend: PASS 过了 / WARN 有痕迹 / FAIL 站不住 / UNVERIFIED 缺输入，判不了 / NODATA 没数据
```

**FAIL**, p = 0.7, on a single time frame. This is the honest verdict for this
trade list, and it is the one we publish alongside the flip.

## What the three outputs say together

1. A verdict is a function of the search count you declare. A -> B is not a
   market event; it is the same 333 returns divided by a different N.
2. The tool cannot stop you from declaring a small N. It can only make the
   consequence visible on the same screen as the claim, which is why B prints
   both thresholds inside one line.
3. C is what a reader should ask for: not "did it pass", but "how many things
   did you try before this one". 576 candidates, 333 trades, no economic reason
   for -3% on BNB specifically — the file passes only when N is understated.
4. Even block A is not a clean bill: look-ahead is UNVERIFIED without `--ohlc`
   (we only checked timestamps), and out-of-sample decay is WARN — first half
   SR 2.06 -> second half 0.53, 74% of the edge missing out of sample.

## Reproduce

```
pip install backtest-audit-kit
python -m auditkit.cli cases/12-multiscale/bnb_trades.csv --trials 20 --timeframes 1
python -m auditkit.cli cases/12-multiscale/bnb_trades.csv --trials 20 --timeframes 5
python -m auditkit.cli cases/12-multiscale/bnb_trades.csv --trials 576 --timeframes 1
```

Expected exit codes: 2, 1, 1.
