# Case 2 — Withdrawal accounting: the bust path forgot `wd_cum`

**Symptom.** Any strategy configured to *withdraw* profits showed systematically
worse historical returns than the same strategy without withdrawals — sometimes
by an order of magnitude. Withdrawals should be roughly neutral to a
multiple-of-capital metric; instead they crushed it.

**Root cause.** The engine tracked cumulative withdrawals in `wd_cum`. Two code
paths existed: the normal path updated it, the **liquidation / bust path**
returned only the reset capital and silently dropped `wd_cum`. Once a strategy
had withdrawn anything and later busted, its entire withdrawal history vanished
from the metric — so the reported multiple was computed on a smaller base and
came out too low.

`auditkit.checks.invariants` catches exactly this with the `BUST_WD_CARRY`
rule (the bust step must *carry* `wd_cum` forward, never reset it) and
`WD_ACCRUAL` / `WD_MONOTONIC` as companions.

**What the fix changed.** Make every exit path return the full state, including
`wd_cum`. The bug is real: **ten** bust returns in this engine returned `0.0`
and discarded both `wd_cum` and the remaining cash.

**How big is it?** Measured by planting / removing that one line on the same
engine and the same signals (2026-10-28 rerun, `bt_campaign_v2.py`):

| Config | Buggy | Fixed | Busts |
|---|---|---|---|
| lev 1.2 · 2024–26 · withdraw "double, keep half" | 7.82x | **7.82x** | 0 |
| lev 1.2 · 2024–26 · no withdrawal | 215.27x | 215.27x | 0 |
| lev 5 · 2021–26 · withdraw "double, keep half" | 0.00x | **5.97x** | 1 |

**An earlier version of this note paired the wrong two numbers.** `215.27x` is
the **no-withdrawal** line of the same signals, not the fixed value of the
withdrawal rule. At lev 1.2 the published run never busts, so the bug never
fires and the number does not move at all (7.82x → 7.82x). At 5x, where the run
busts, the bug is total: 0.00x reported against 5.97x with the fix.

**Bottom line.** Two separate effects were conflated:
* **withdrawal policy** — taking half out at every doubling costs ~27x of
  compounding on this sample (215.27x → 7.82x). Correct arithmetic, not a bug;
* **bust-path accounting** — worth 0x when nothing busts, and everything when
  something does (0.00x vs 5.97x).

The invariant is still worth asserting (`BUST_WD_CARRY`); the honest headline
is "this bug silently zeroes any run that busts after a withdrawal", not
"27x understatement".

**How to reproduce.** `tests/test_invariants.py::test_catches_planted_violations`
builds a ledger whose bust step drops `wd_cum` and asserts the violation fires;
`test_clean_ledger_has_no_violations` asserts the corrected ledger stays quiet.
