# Sample audit: 37 Collective2 leaderboard strategies, screened in one pass

> Public sample of the paid verification service (USD 29 / one number / 48h / no charge if nothing is found).
> Source data is public: https://collective2.com/leader-board, fetched 2026-11-07. No client material is used.
> Method files: c2_fetch.py (one strategy), c2_screen.py (batch), c2_analyze.py (four checks).

## What was checked

- 37 strategy ids taken from the server-rendered leaderboard; each /details/<id> page parsed for its monthly table.
- **Reconciliation**: every year's monthly cells compounded locally and compared with the printed YTD; the annualised figure recomputed as eq^(365/days)-1.
- **Four checks** per strategy: (1) share of total log return carried by the best 3 months; (2) annual return vs max drawdown; (3) length of record; (4) win-rate edge vs the break-even win rate implied by average win/loss.

## Result

| Check | Hits (of 36 active) | What it means |
|---|---|---|
| Concentration > 70% | 19 | best 3 months carry >70% of the log return; >100% means the rest of the record is net negative |
| Annual / drawdown > 2.5x | 11 | return large relative to the reported max drawdown |
| History < 18 months | 11 | an annualised figure on a short record |
| Edge < 2 SE | 3 | win rate not yet distinguishable from break-even |
| No flag at all | 14 | checked, nothing found - also a deliverable |

**Arithmetic reconciles.** Every year's monthly cells compound to the printed YTD within 0.4pp, and the annual figure uses actual calendar days (verified on 5 strategies, error -1.6 to +0.2pp). The platform is not the problem.

## Two named examples

- **152974419 (Quant AI SP500)** - 14 months, +55.6% cumulative, annual 49.2%, max DD 7.5% (6.6x). The single +24.1% month (2026-07) carries 84% of the log return. 469 trades, 91.7% win rate against a 58.3% break-even.
- **152326039** - 17 months, +23.5%, best 3 months = 194% of the total: outside those months the record is net negative.

## Reading

The honest question is not "is the math wrong" but "how much of this return is one month, how short is the record, and does the drawdown match the annual figure". Flags point at where a buyer should ask; a clean result is still a result.

## Coverage and the denominator

- **Coverage**: 36 of 37 pages are live and complete (monthly cells printed for every month of the record). One page (124293346) has 89 monthly cells, all zero - 100% coverage, and the number means "inactive", not "flat". Every aggregate needs both a coverage count and a live/dead marker, because a missing cell never errors: in a sum it becomes 0, in a product 1.0, in a count it is skipped.
- **Denominator**: the eligible set here is the 37 ids the leaderboard publishes. That is already a selection - strategies that disappeared are not recoverable from public pages, so this report cannot measure survival bias beyond the published set. What it can do is put the featured example next to the median of the set (19 of 36 carry more than 70% of their log return in the best three months; 14 carry no flag).

## Scope and limits

- The leaderboard is a selection: it shows the winners. Nothing here measures the strategies that disappeared.
- Concentration is computed on log contributions of monthly returns; a share above 100% is legitimate arithmetic, not a bug.
- Everything is hypothetical per the platform's own disclaimer; no broker statements were seen.
- The edge test assumes a fixed average win and loss, which is an approximation.

---

Prepared as a public sample by rytjy - gbbggjvf@gmail.com - github.com/rytjy/backtest-audit-kit
