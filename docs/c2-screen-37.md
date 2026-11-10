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
| No flag at all | 11 | checked, nothing found - also a deliverable |

**Arithmetic reconciles.** Every year's monthly cells compound to the printed YTD within 0.4pp, and the annual figure uses actual calendar days (verified on 5 strategies, error -1.6 to +0.2pp). The platform is not the problem.

## Two named examples

- **152974419 (Quant AI SP500)** - 14 months, +55.6% cumulative, annual 49.2%, max DD 7.5% (6.6x). The single +24.1% month (2026-07) carries 84% of the log return. 469 trades, 91.7% win rate against a 58.3% break-even.
- **152326039** - 17 months, +23.5%, best 3 months = 194% of the total: outside those months the record is net negative.

## Reading

The honest question is not "is the math wrong" but "how much of this return is one month, how short is the record, and does the drawdown match the annual figure". Flags point at where a buyer should ask; a clean result is still a result.

## Coverage and the denominator

- **Coverage**: 36 of 37 pages are live and complete (monthly cells printed for every month of the record). One page (124293346) has 89 monthly cells, all zero - 100% coverage, and the number means "inactive", not "flat". Every aggregate needs both a coverage count and a live/dead marker, because a missing cell never errors: in a sum it becomes 0, in a product 1.0, in a count it is skipped.
- **Denominator**: the eligible set here is the 37 ids the leaderboard publishes. That is already a selection - strategies that disappeared are not recoverable from public pages, so this report cannot measure survival bias beyond the published set. What it can do is put the featured example next to the median of the set (19 of 36 carry more than 70% of their log return in the best three months; 11 carry no flag).

## Rank stability: one month left out

Ranking = annualised return from the monthly cells, over the 36 active strategies. For each strategy, one month is removed at a time, the remaining record is re-annualised over its actual days, the set is re-ranked, and the worst place that strategy holds across its own months is recorded.

- Median worst place: **4 ranks below** the current one. Six of 36 fall 10+ places; the largest drop is 15.
- 25 of 36 touch rank 20 or worse at least once.
- Four never leave the top 10: 150377786, 141710744, 148705494, 150004796.
- Concentration and rank-dependence agree: the 19 flagged above 70% in the best three months have a median worst drop of **7 places**; the other 17, **2 places**.
- Worst single-month cases: 153432780 #8 -> #23 without 2026-01 (+30.2%); 153416579 #15 -> #29 without 2026-03 (+18.3%); 153204518 #6 -> #18 without 2026-03 (+25.6%); 152974419 #12 -> #23 without 2026-07 (+24.1%).
- **Limit**: removing a positive month can only lower an annualised return, so the test is one-sided - it measures how much of a place rests on the best month, not symmetric robustness. Ranking by return/drawdown would reorder the set.
- Full table, all 36 rows: [c2-rank-stability.pdf](c2-rank-stability.pdf) (2 pages, now with a `min ann%` column). Renderer: `audits/c2_stability_pdf.py`.

## Return stability under the same omissions

Same set, same 36 omissions per strategy; the recorded quantity is now the lowest annualised return the record produces, not the worst place.

| Measure | Value |
|---|---|
| Median shortfall | **9.9 pp** |
| Strategies losing more than 5 / 10 / 20 pp | 27 / 18 / 9 of 36 |
| Largest shortfall | **43.4 pp** - 150004796: 100.8% to 57.3% without 2026-04 |
| Only strategy that turns negative | 152326039: 17.3% to **-2.1%** without 2026-07 |

Ranks and returns do not move together. The four that never leave the top 10 by rank still lose 18.0 to 43.4 pp of annualised return on a single omission (150004796 -43.4, 148705494 -28.1, 150377786 -25.0, 141710744 -18.0). The smallest shortfall in the set, 1.0 pp, belongs to 13202557, which ranks #28. A stable place is not a stable number.

| id | base ann% | min ann% | shortfall | month removed |
|---|---|---|---|---|
| 150004796 | 100.8 | 57.3 | 43.4 | 2026-04 |
| 153432780 | 61.5 | 25.8 | 35.6 | 2026-01 |
| 153204518 | 64.8 | 35.9 | 28.9 | 2026-03 |
| 148705494 | 85.3 | 57.1 | 28.1 | 2025-04 |
| 151330723 | 67.0 | 41.9 | 25.1 | 2025-04 |
| 150377786 | 128.7 | 103.7 | 25.0 | 2025-08 |
| 152974419 | 49.6 | 25.0 | 24.6 | 2026-07 |
| 152169281 | 45.4 | 23.2 | 22.2 | 2026-04 |
| 153416579 | 40.6 | 20.4 | 20.1 | 2026-03 |

Nine rows shown; the full 36 are in the PDF column `min ann%`. Same one-sided caveat applies: removing a positive month lowers the return, so this measures exposure to the best month, not symmetric robustness.

## Corrections (2026-11-10)

- The table export carried 41 rows from three fetch dates; the screened set is the 37 ids named in the prose. Four stale rows from the 2026-11-01 batch were removed from `c2-screen-37.table.txt`.
- Two 13-month strategies printed no annualised figure; computed from their own cells they are 40.6% (153416579) and 61.5% (153432780), now filled in the table.
- "No flag at all" is **11**, not the 14 originally written.

## Scope and limits

- The leaderboard is a selection: it shows the winners. Nothing here measures the strategies that disappeared.
- Concentration is computed on log contributions of monthly returns; a share above 100% is legitimate arithmetic, not a bug.
- Everything is hypothetical per the platform's own disclaimer; no broker statements were seen.
- The edge test assumes a fixed average win and loss, which is an approximation.

---

Prepared as a public sample by rytjy - gbbggjvf@gmail.com - github.com/rytjy/backtest-audit-kit
