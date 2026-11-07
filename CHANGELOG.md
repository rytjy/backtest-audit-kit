# Changelog

## v0.2.3 — 2026-11-07

**Docs only. No code change.**

- The offer and the price now sit in the README itself: one path, one written report, 48 hours, ¥199 / $29, no reproducible finding no fee, plus a contact address.
- Reason: the PyPI long description *is* this README, and relative links (`PORTFOLIO.md`) do not resolve on a PyPI page. A reader arriving from `pip install` could not see a price or an address at all.

## v0.2.2 — 2026-11-07

**Two new checks for metric and funding accounting.**

- `checks/metrics.py`:
  - `downside_deviation()` — the standard definition, `sqrt(sum(min(r,0)^2)/N)` over **all** observations.
  - `sortino_ratio()` — annualised Sortino built on that denominator.
  - `check_reported_sortino()` — computes both the correct and the common wrong variant (dividing by the count of negative returns only). If the reported figure matches the wrong one and not the right one, it raises `SORTINO_DOWNSIDE_DENOMINATOR`; any other material gap raises `SORTINO_MISMATCH`.
  - `check_funding_coverage()` — walks each position window against the funding series. A funding event landing exactly at the exit timestamp is reported as `FUNDING_GAP_AT_EXIT` (the "closed on the bar that carried the funding" hole).
- 7 new tests (`tests/test_metrics.py`), suite total 30.
- New case: [Case 15](cases/case15_c2_hypothetical_annualized.md) — a vendor's "+90.2% annualised (compounded)" recomputed from its own monthly table. The compounding checks out; the figure is hypothetical, three months carry it (34.8% without them), monthly peak-to-trough is −21.8%.

## v0.2.1 — 2026-11-04

**Docs only. No code change.**

- README links [Case 12](audits/2026-11-04-case12-multiscale.md): one trade list, three verdicts — PASS at `--trials 20 --timeframes 1` (p=0.024), FAIL at the same N with `--timeframes 5` (N_eff=100, p=0.12), and FAIL at the search count actually scanned (576).
- Case count in the README corrected from 11 to 12.
- The PyPI long description is this README, so the case is now one click from `pip install backtest-audit-kit`.

## v0.2.0 — 2026-11-03

**Multi-scale search inflation.**

- New `--timeframes N` flag: effective trials become `--trials × --timeframes`.
- The multiple-testing check now reports `N_eff` and recomputes the bar and adjusted p against it.
- When inflation flips the verdict (PASS at N, FAIL at N_eff), a second WARN line spells out both bars.
- JSON output adds `timeframes`, `trials_effective`, `multiscale_inflation`.
- Default is 1, so existing invocations and their output are unchanged.
- Docs: `docs/MULTISCALE.md`; one-pager: `docs/multiscale-onepager.pdf`.

## v0.1.0 — 2026-11-01

- `auditkit.cli`: one command, three checks (look-ahead, deflated Sharpe / multiple testing, out-of-sample decay) on a plain CSV.
