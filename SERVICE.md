# Backtest audit — fixed scope, fixed price

I check whether your backtest is lying to you. Not whether your strategy makes money.

**What you get**

1. A ranked issue list, each with `file:line`
2. A runnable repro per issue (same data, same command)
3. A minimal patch where the fix is local
4. Before/after numbers: win rate, net PnL, multiple, MDD, t-stat

**Two ways to start**

- **One issue — ¥199 / $29 / 30 USDT (TRC20).** One concrete problem, 48 hours
  from a runnable repro: one page, a repro script, and a minimal patch where the
  fix is local.
- **Full audit — ¥300–800.** One strategy/backtest, ≤2,000 lines or one runnable
  notebook; 2–4 days. Ranked issue list, one repro per issue, and before/after
  numbers.

Price is quoted before I start. 48-hour rush: +50%.

**Guarantee** — if I find nothing reproducible, you pay nothing.

**Free first step** — send the repo or the core file. I reply with one concrete,
reproducible problem. If it's useful, we continue; if not, we stop there.

**Proof**

- `cases/case5_cost_omission.md` — a real BTC backtest with no cost model: the
  omitted cost ran **~5.4× the starting capital** and **~17.8× the reported
  profit**. Take-profit needed **+0.08%**; one round trip at 4.5 bps/side costs
  **0.09%** — the target sits below the toll.
- `cases/case6_numeric_cancellation.md` — an expanding R² on a perfectly linear
  series returned **0.14–0.69** instead of **1.0**, from raw-moment cancellation.
  Silent, plausible, wrong.

**Not offered** — no signals, no managed money, no profit promises, no access to
funds or keys; no homework or thesis writing.

Contact: open an issue on this repo, or WeChat (provided on request).
