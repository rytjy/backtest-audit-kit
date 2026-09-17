# Case 1 — Look-ahead: the exit scanned the future on the entry bar

**Symptom.** A single-asset perpetual strategy backtested beautifully: high win
rate, steady equity curve. It produced almost nothing live. The edge was a
future leak.

**Root cause.** The signal generator decided whether a trade would hit its
stop-loss or take-profit by scanning a forward window *at the moment of entry*:

```python
for ei in range(n):
    if not condition(df, ei):
        continue
    hit = None
    for j in range(ei + 1, min(ei + 1 + TO, n)):   # <-- scans the FUTURE
        if low(df, j) <= sl_price(df, ei):
            hit = "SL"; break
        if high(df, j) >= tp_price(df, ei):
            hit = "TP"; break
    if hit == "TP":                                    # only trade the winners
        entries.append(ei)
```

Every emitted signal already knew its own outcome. `auditkit.checks.lookahead`
flags this as `FUTURE_WINDOW_LOOP` (severity `HIGH`, because the loop is nested
inside the outer bar loop).

**What the fix changed.** Evaluate the exit only on the *current* bar, as the
backtest advances — no decision on bar `i` may see bar `i+1`.

| Variant | Trades | Win rate | Net PnL |
|---|---|---|---|
| Bar-level scan of the future (buggy) | 91 | 90.1% | **+$214.37** |
| Current-bar scan only (fixed)       | 26 | 65.4% | **-$0.12** |
| Tick-level scan only (fixed)        | 27 | 66.7% | **+$0.37** |

**Bottom line.** The leak was worth roughly **$214 of imaginary PnL** — the
entire reported profit. Fixing it turned a "90% win-rate winner" into a
break-even strategy. No parameter change; only the information available at
decision time.

**How to reproduce.** `tests/fixtures/lookahead_buggy.py` triggers the detector;
`tests/fixtures/lookahead_fixed.py` is clean.
