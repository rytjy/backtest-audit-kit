# Case 8 — A column that changed meaning, and four engines that kept reading it

**Symptom.** The "final live config" backtest reported a **median terminal wealth
of 0x** — every sampled path lost everything, half of them to a bust. That looked
like a verdict on the strategy. It was a verdict on a column.

**Root cause.** On 2026-09-05 a migration moved `ret_24h` **up 24 rows**:

```python
rn[24:] = r[:-24]        # docstring: "→ historical returns"
```

After that write, the column is **trailing** 24h momentum — something you knew
before entering. Every engine that consumed it as the *forward* 24h return kept
subtracting fees and calling the result net PnL. Four scripts do this
(`bt_final_live.py`, `bt_2pos_circuit.py`, `bt_withdraw_design.py`,
`bt_path_enum.py`); the first one was the "final configuration".

**Evidence that the column is now backward-looking.** On the current
`proxy_1h_v5.csv`, of 2,011 sampled rows, **2,008 match `c[i]/c[i-24]-1`**
(the past) and 3 match the future. The author's own 2026-09-15 note already said
`ret_24h` correlates +1.0000 with the past 24h — the migration was known; the
consumers were never revisited.

**Same script, two semantics** (differs by one line, applied at load time):

| Data in the column | Median terminal wealth | Loss paths | Busts | Ended `>=1000x` |
|---|---:|---:|---:|---:|
| Current CSV (trailing return used as PnL) | **0x** | 100% | 50.0% | 0% |
| Rebuilt as forward 24h return | **1,760x** | 16.7% | 16.7% | 65% |

Neither number is evidence about the strategy. The first is arithmetic on the
wrong sign of time; the second is arithmetic on the right sign of time with a
backtest that still assumes you can fill at the close.

**The second correction: 1,760x is not an edge either.** Three experiments on the
rebuilt column:

1. **Event quality.** 487 events (DIV 217 / BRK 180 / WICK 90). Forward 24h
   mean **+3.77%**, median **+2.45%** after 29 bps. But median MAE is **−4.55%**
   and **P(MAE <= -16%) = 8.8%** — the path, not the endpoint, decides survival.
2. **Liquidation.** At 5x, marking only at the close gives a median of 39.8x with
   no busts. Add intrabar liquidation and the same trades give a median of
   **0.02x**, with **17%** busted. At 3x: 0.57x. At 1x: 601x. The 5x result was a
   fiction produced by ignoring the wick.
3. **Concurrency.** Half the events overlap another coin's event; median 2 open
   at once, p90 4, max 10. The old script compounded serially at full size. At 1x
   with a position cap over three years: **1.71x (K=1) · 5.28x (K=3) ·
   3.94x (K=5) · 2.26x (K=10)**.

One more caution: the "216 paths" in the original write-up are the 216
permutations of six year-blocks. **The independent sample size is six**, not 216;
percentages computed across them are pseudo-replication.

**Bottom line.** A column header is not a definition. When a data migration
changes the direction of time in a column, every consumer must be re-run, not
just the one that looks important. And fixing the direction gets you back to
arithmetic — it does not get you to an edge: leverage without intrabar
liquidation, and compounding without a concurrency cap, will manufacture one.

**Caveats (scope).** Audited on one machine's archive; no venue replay, no order
book, no funding. The pre-migration file
(`proxy_1h_v5.csv.bak_0905_poison`) is **no longer on disk**, so "the column used
to be forward-looking" is inferred from the migration script, the engine
semantics, and three historical magnitudes — not read directly from the old file.
Fees used: 29 bps per event round trip; slippage beyond that is not modelled.
