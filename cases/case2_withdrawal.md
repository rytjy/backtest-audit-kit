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
`wd_cum`.

| Configuration (2024–2026, same signals) | Reported multiple (buggy) | Reported multiple (fixed) |
|---|---|---|
| Withdrawal rule "double, keep half" (翻 2 留 1) | 7.82x | **215.27x** |

Comparing withdrawal-rule families ("翻 2 留 1" vs "翻 200 留 100") on the
fixed engine, the reported multiple moves by roughly **27x** — i.e. the bug's
size scales with how aggressively the strategy withdraws.

**Bottom line.** The same configuration reported **7.82x** buggy and
**215.27x** fixed — an understatement of about **27x**, purely because one
return path lost a counter. The bug was invisible in equity-curve charts and
only surfaced once the ledger invariants were asserted step by step.

**How to reproduce.** `tests/test_invariants.py::test_catches_planted_violations`
builds a ledger whose bust step drops `wd_cum` and asserts the violation fires;
`test_clean_ledger_has_no_violations` asserts the corrected ledger stays quiet.
