# Changelog

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
