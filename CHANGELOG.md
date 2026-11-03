# Changelog

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
