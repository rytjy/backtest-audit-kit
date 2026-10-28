# Case 3 — Drawdown metric: the circuit-breaker reset the peak

**Symptom.** The report said "max drawdown: 53.1%". An investor looking at the
equity curve could see that it had, at one point, lost almost everything. The
two numbers could not both be right.

**Root cause.** The engine had a circuit-breaker: when drawdown crossed a
threshold it halted, and on resume it **reset the running peak to the current
capital**. The drawdown metric was measured against that peak. So the "reported
MDD" was only the deepest drawdown *within one post-breaker segment* — the
original, from-the-all-time-high drawdown was never recorded.

`auditkit.checks.invariants` supports the fix directly: assert the equity
identity every step and treat the peak as an all-time series that is never
modified by a control-flow event.

**What the fix changed.** Write **two** drawdown numbers at once:

* `mdd_reported` — segment-local drawdown (what the breaker sees), and
* `mdd_raw` — drawdown from the all-time-high capital, never reset.

| Metric | Value |
|---|---|
| Investor-view raw drawdown, full history (fixed) | **98.7%** |
| Reported MDD (breaker-local, buggy) | **53.1%** |
| Gap | **45.6 percentage points** |

*Provenance.* Both numbers come from the same run — `trading_research/run_out/risk_gate_tests.txt`,
lev 1.2, 2021: `MDD 53.1% | 原始MDD 98.7%`. An earlier version of this note
quoted 99.7%, which is a **different** configuration (lev 1.2, breaker off,
full history, `run_out/sens_odds_fix.txt`). The conclusion is unchanged; the
pairing was wrong and is corrected here.

**Bottom line.** The headline number hid a near-total loss. **MDD must be
dual-written**: a control-flow variable may be reset, but the investor-facing
metric may not. Reporting only the reset number is, at minimum, materially
misleading.

**How to reproduce.** Any ledger whose `cap` drops from an all-time high while
a control event resets the internal peak; assert the equity identity and
preserve an unmodified peak series. See `cases/README` guidance and
`tests/test_invariants.py` for the invariant form.
