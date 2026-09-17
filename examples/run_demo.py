"""End-to-end demo: run every checker on the bundled fixtures.

    cd portfolio/backtest-audit-kit && python3 examples/run_demo.py
"""

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from auditkit.checks import fees, lookahead, mutants
from auditkit.checks.invariants import check_ledger, violations_by_rule


def hr(title):
    print("\n" + "=" * 68)
    print(title)
    print("=" * 68)


def demo_lookahead():
    hr("1) look-ahead lint")
    fixtures = os.path.join(ROOT, "tests", "fixtures")
    for name in ("lookahead_buggy.py", "lookahead_fixed.py"):
        findings = lookahead.detect_file(os.path.join(fixtures, name))
        print(f"\n{name}: {len(findings)} finding(s)")
        print(lookahead.format_findings(findings))


def demo_invariants():
    hr("2) ledger invariants")
    buggy = [
        {"step": 0, "cap": 120.0, "cash": 120.0, "positions": {}, "wd_cum": 20.0},
        {"step": 1, "cap": 100.0, "cash": 100.0, "positions": {}, "bust": True},
    ]
    findings = check_ledger(buggy)
    print(f"\nbuggy ledger -> {len(findings)} violation(s): {violations_by_rule(findings)}")
    for v in findings:
        print("  " + str(v))


def demo_mutants():
    hr("3) mutation testing")
    target = (
        "\ndef apply_fee(cash, notional, fee_rate):\n"
        "    cash = cash - notional * fee_rate\n"
        "    return cash\n"
    )

    def weak_suite(ns):
        assert ns["apply_fee"](100.0, 1000.0, 0.0) == 100.0

    def strong_suite(ns):
        assert ns["apply_fee"](100.0, 1000.0, 0.0) == 100.0
        assert ns["apply_fee"](100.0, 1000.0, 0.01) == 90.0

    for label, suite in (("weak suite", weak_suite), ("strong suite", strong_suite)):
        res = mutants.run_mutation_tests(target, suite)
        print(f"\n{label}:")
        print("  " + res.report().replace("\n", "\n  "))


def demo_fees():
    hr("4) fee / funding / slippage")
    trades = [
        {"id": "buggy", "entry_notional": 10_000, "exit_notional": 10_000,
         "holding_bars": 8, "fee_paid": 5.0, "funding_paid": 1.0,
         "slippage_paid": 8.0},
    ]
    for issue in fees.check_trades(trades):
        print("  " + str(issue))


if __name__ == "__main__":
    demo_lookahead()
    demo_invariants()
    demo_mutants()
    demo_fees()
    print("\ndone.")
