# Backtest audit — fixed scope, fixed price

I check whether your backtest is lying to you. Not whether your strategy makes money.

**What you get**

1. A ranked issue list, each with `file:line`
2. A runnable repro per issue (same data, same command)
3. A minimal patch where the fix is local
4. Before/after numbers: win rate, net PnL, multiple, MDD, t-stat

**Ways to start**

- **One issue — ¥199 / $29 / 30 USDT (TRC20).** One concrete problem, 48 hours
  from a runnable repro: one page, a repro script, and a minimal patch where the
  fix is local.
- **Full audit — ¥300–800.** One strategy/backtest, ≤2,000 lines or one runnable
  notebook; 2–4 days. Ranked issue list, one repro per issue, and before/after
  numbers.

- **On-chain yield check — same fixed price.** One public ERC4626 vault:
  headline APY vs realized share-price growth over 7/30/90/180 days. You get
  **one page**: claim and source, method, four windows, a one-paragraph reading
  of where the gap comes from, a one-command repro, and a scope box. 48 hours.
  See `cases/case7_onchain_yield.md`.

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

- **Independent listing** — `backtest-audit-kit` is listed in
  [awesome-quant](https://github.com/wilsonfreitas/awesome-quant) under Trading &
  Backtesting, accepted by its maintainer (PR #824, merged 2026-10-19).

- `cases/case7_onchain_yield.md` — a public vault advertising **8.44%** net
  paid **6.52%** over 30 days and **6.04%** over 90; **0.52 pp** was token
  rewards that never entered the share price.

**Not offered** — no signals, no managed money, no profit promises, no access to
funds or keys; no homework or thesis writing.

Contact: open an issue on this repo, or WeChat (provided on request).

**How to pay** — PayPal to `gbbggjvf@gmail.com`. Price is fixed before I start,
and I write the scope down first, so you pay against a stated deliverable rather
than a promise. If I find nothing reproducible, you pay nothing.

